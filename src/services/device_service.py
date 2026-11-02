import json
import logging
import os
import subprocess
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADER_SCRIPT = os.path.join(CURRENT_DIR, "device_downloader.ps1")


class DeviceService:

    @staticmethod
    def _ensure_monthly_table(db1: Session, month: int, year: int) -> str:
        """Ensure the monthly ESSL log table exists in DB1."""

        table_name = f"dbo.DeviceLogs_{month}_{year}"

        table_id = db1.execute(
            text("SELECT OBJECT_ID(:table_name, 'U')"),
            {"table_name": table_name},
        ).scalar()

        if table_id is None:
            raw_tbl = f"DeviceLogs_{month}_{year}"

            db1.execute(text(f"""
                CREATE TABLE [{raw_tbl}] (
                    [DeviceLogId] INT IDENTITY(1,1) NOT NULL,
                    [DownloadDate] DATETIME NULL,
                    [DeviceId] INT NULL,
                    [UserId] NVARCHAR(50) NOT NULL,
                    [LogDate] DATETIME NOT NULL,
                    [Direction] NVARCHAR(100) NULL,
                    [AttDirection] NVARCHAR(255) NULL,
                    [C1] NVARCHAR(255) NULL,
                    [C2] NVARCHAR(255) NULL,
                    [C3] NVARCHAR(255) NULL,
                    [C4] NVARCHAR(255) NULL,
                    [C5] NVARCHAR(255) NULL,
                    [C6] NVARCHAR(255) NULL,
                    [C7] NVARCHAR(255) NULL,
                    [WorkCode] NVARCHAR(100) NULL,
                    [UpdateFlag] INT NULL,
                    [IsApproved] INT DEFAULT (-1),
                    [EmployeeImage] IMAGE NULL,
                    [FileName] NVARCHAR(255) NULL,
                    [Longitude] NVARCHAR(255) NULL,
                    [Latitude] NVARCHAR(255) NULL,
                    [CreatedDate] DATETIME NULL,
                    [LastModifiedDate] DATETIME NULL,
                    [LocationAddress] NVARCHAR(4000) NULL,
                    [BodyTemperature] FLOAT DEFAULT (0),
                    [IsMaskOn] INT DEFAULT (0),
                    CONSTRAINT [PK_{raw_tbl}_1]
                        PRIMARY KEY CLUSTERED ([UserId], [LogDate])
                ) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
            """))

            logger.info("Created monthly ESSL table: %s", table_name)

        return table_name

    @staticmethod
    def _ensure_employee_on_first_checkin(
        db1: Session,
        db2: Session,
        essl_user_id: str,
    ) -> bool:
        """
        If this check-in belongs to an employee missing from DB2,
        create the initial ERP employee profile.

        Existing DB2 profiles are never overwritten.
        Returns True when an employee was inserted.
        """

        essl_user_id = str(essl_user_id or "").strip()

        if not essl_user_id:
            return False

        # Employee already linked to this ESSL ID?
        existing_essl = db2.execute(
            text("""
                SELECT TOP 1 EmployeeCode
                FROM dbo.Employee_Mst
                WHERE ESSLEmployeeCode = :essl_code
            """),
            {"essl_code": essl_user_id},
        ).first()

        if existing_essl:
            return False

        # Find the employee in the existing eTimeTrackLite master.
        # UserId is matched against the ESSL employee identifiers.
        source = db1.execute(
            text("""
                SELECT TOP 1
                    EmployeeCode,
                    EmployeeCodeInDevice,
                    EmployeeName,
                    Status,
                    RecordStatus
                FROM dbo.Employees
                WHERE (
                    LTRIM(RTRIM(CONVERT(NVARCHAR(50), EmployeeCode))) = :essl_code
                    OR LTRIM(RTRIM(CONVERT(NVARCHAR(50), EmployeeCodeInDevice))) = :essl_code
                )
                  AND (RecordStatus = 1 OR RecordStatus IS NULL)
                ORDER BY
                    CASE
                        WHEN LTRIM(RTRIM(CONVERT(NVARCHAR(50), EmployeeCode))) = :essl_code
                        THEN 0
                        ELSE 1
                    END
            """),
            {"essl_code": essl_user_id},
        ).mappings().first()

        if not source:
            logger.warning(
                "Check-in for ESSL ID %s has no matching DB1 employee.",
                essl_user_id,
            )
            return False

        employee_name = str(source["EmployeeName"] or "").strip()
        internal_code = str(source["EmployeeCode"] or "").strip()

        if not employee_name or not internal_code:
            logger.warning(
                "Skipping ESSL ID %s: employee name or internal code is missing.",
                essl_user_id,
            )
            return False

        # Do not create a duplicate internal ERP employee.
        code_exists = db2.execute(
            text("""
                SELECT TOP 1 EmployeeCode
                FROM dbo.Employee_Mst
                WHERE EmployeeCode = :employee_code
            """),
            {"employee_code": internal_code},
        ).first()

        if code_exists:
            logger.warning(
                "Cannot auto-create ESSL ID %s: ERP EmployeeCode %s "
                "is already assigned. Resolve the mapping manually.",
                essl_user_id,
                internal_code,
            )
            return False

        # Insert only the initial profile. Later check-ins must not
        # overwrite fields edited by an ERP administrator.
        db2.execute(
            text("""
                INSERT INTO dbo.Employee_Mst (
                    EmployeeCode,
                    FirstName,
                    DisplayName,
                    EmployeeSource,
                    ESSLEmployeeCode,
                    ESSLStatus,
                    ESSLSyncedAt,
                    IsActive,
                    CreatedAt,
                    UpdatedAt
                )
                VALUES (
                    :employee_code,
                    :employee_name,
                    :display_name,
                    'ESSL',
                    :essl_code,
                    'ACTIVE',
                    SYSDATETIME(),
                    1,
                    SYSDATETIME(),
                    SYSDATETIME()
                )
            """),
            {
                "employee_code": internal_code,
                "employee_name": employee_name,
                "display_name": employee_name,
                "essl_code": essl_user_id,
            },
        )

        logger.info(
            "Created ERP employee %s from first check-in for ESSL ID %s.",
            internal_code,
            essl_user_id,
        )

        return True

    @classmethod
    def download_biometric_logs(
        cls,
        db1: Session,
        db2: Session,
        device_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Download device logs into DB1 and create an Employee_Mst
        profile when a check-in belongs to a previously unlinked
        ESSL employee.

        DB1: eTimeTrackLite
        DB2: SCOTO_ACC_ERP
        """

        # 1. Find the configured device.
        if device_id:
            devices = db1.execute(
                text("""
                    SELECT
                        DeviceId, DeviceFName, DeviceSName,
                        DeviceDirection, SerialNumber, IpAddress,
                        CommKey, LastLogDownloadDate
                    FROM dbo.Devices
                    WHERE DeviceId = :dev_id
                """),
                {"dev_id": device_id},
            ).fetchall()
        else:
            devices = db1.execute(
                text("""
                    SELECT
                        DeviceId, DeviceFName, DeviceSName,
                        DeviceDirection, SerialNumber, IpAddress,
                        CommKey, LastLogDownloadDate
                    FROM dbo.Devices
                    WHERE IpAddress IS NOT NULL
                      AND LEN(LTRIM(RTRIM(IpAddress))) > 0
                    ORDER BY
                        CASE WHEN LEN(SerialNumber) > 5 THEN 0 ELSE 1 END,
                        LastLogDownloadDate DESC
                """)
            ).fetchall()

        if not devices:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No configured biometric device found in database.",
            )

        device = devices[0]

        dev_id = device.DeviceId
        dev_name = device.DeviceFName or f"Device {dev_id}"
        ip_address = (device.IpAddress or "").strip()
        comm_key = str(device.CommKey or "000000").strip()
        last_download = device.LastLogDownloadDate

        if not ip_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The selected biometric device has no IP address.",
            )

        # 2. Download cutoff.
        if last_download and last_download > datetime(2020, 1, 1):
            since_dt = last_download - timedelta(days=2)
        else:
            now_dt = datetime.now()
            since_dt = now_dt.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )

        since_str = since_dt.strftime("%Y-%m-%d %H:%M:%S")

        logger.info(
            "Downloading logs from %s (%s) since %s",
            dev_name,
            ip_address,
            since_str,
        )

        # 3. Execute the existing PowerShell downloader.
        cmd = [
            "powershell.exe",
            "-ExecutionPolicy", "Bypass",
            "-File", DOWNLOADER_SCRIPT,
            "-IpAddress", ip_address,
            "-Port", "4370",
            "-CommKey", comm_key,
            "-SinceDate", since_str,
        ]

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=45,
            )
        except subprocess.TimeoutExpired as exc:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=(
                    f"Connection to biometric device at {ip_address} "
                    "timed out after 45 seconds."
                ),
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to execute downloader script: {exc}",
            ) from exc

        stdout_clean = res.stdout.strip()

        start_idx = next(
            (
                i for i, char in enumerate(stdout_clean)
                if char in ("[", "{")
            ),
            -1,
        )

        if start_idx == -1:
            err_msg = (
                res.stderr.strip()
                or stdout_clean
                or "Unknown downloader error"
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Device communication failed: {err_msg}",
            )

        try:
            parsed = json.loads(stdout_clean[start_idx:])
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Invalid response from device: {exc}",
            ) from exc

        if isinstance(parsed, dict) and "error" in parsed:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Biometric device error: {parsed['error']}",
            )

        if not isinstance(parsed, (list, dict)):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unexpected response format from biometric device.",
            )

        logs_list = [parsed] if isinstance(parsed, dict) else parsed

        # 4. Save logs and ensure the employee exists.
        now = datetime.now()
        new_count = 0
        dup_count = 0
        employee_created_count = 0
        max_log_dt = last_download

        try:
            for item in logs_list:
                user_id = str(item.get("UserId", "")).strip()

                if not user_id:
                    continue

                try:
                    log_dt = datetime.strptime(
                        item["LogDate"], "%Y-%m-%d %H:%M:%S"
                    )
                except (ValueError, KeyError, TypeError):
                    logger.warning("Skipping invalid ESSL log: %s", item)
                    continue

                # IMPORTANT:
                # Run the employee check before duplicate-log handling.
                # This also repairs the case where the punch already exists
                # in DB1 but the employee is missing from DB2.
                was_created = cls._ensure_employee_on_first_checkin(
                    db1=db1,
                    db2=db2,
                    essl_user_id=user_id,
                )

                if was_created:
                    employee_created_count += 1

                v_mode = str(item.get("VerifyMode", 15))
                io_mode = str(item.get("InOutMode", 0))
                w_code = str(item.get("WorkCode", 0))

                table = cls._ensure_monthly_table(
                    db1, log_dt.month, log_dt.year
                )

                exists = db1.execute(
                    text(f"""
                        SELECT 1
                        FROM {table}
                        WHERE UserId = :uid AND LogDate = :ldt
                    """),
                    {"uid": user_id, "ldt": log_dt},
                ).first()

                if exists:
                    dup_count += 1
                    continue

                db1.execute(
                    text(f"""
                        INSERT INTO {table} (
                            DeviceId, LogDate, UserId, Direction,
                            DownloadDate, WorkCode, C1, C4, C5,
                            UpdateFlag, CreatedDate
                        )
                        VALUES (
                            :dev_id, :ldt, :uid, '',
                            :down_dt, :w_code, 'in', :c4, :c5,
                            0, :created_dt
                        )
                    """),
                    {
                        "dev_id": dev_id,
                        "ldt": log_dt,
                        "uid": user_id,
                        "down_dt": now,
                        "w_code": w_code,
                        "c4": io_mode,
                        "c5": v_mode,
                        "created_dt": now,
                    },
                )

                new_count += 1

                if max_log_dt is None or log_dt > max_log_dt:
                    max_log_dt = log_dt

            # 5. Update device's last-download timestamp.
            if max_log_dt and max_log_dt > (
                last_download or datetime(1900, 1, 1)
            ):
                db1.execute(
                    text("""
                        UPDATE dbo.Devices
                        SET LastLogDownloadDate = :max_dt
                        WHERE DeviceId = :dev_id
                    """),
                    {"max_dt": max_log_dt, "dev_id": dev_id},
                )

            # Commit both databases after processing completes.
            db1.commit()
            db2.commit()

        except Exception:
            db1.rollback()
            db2.rollback()
            logger.exception("ESSL log download or employee creation failed.")
            raise

        logger.info(
            "Device %s download finished: %s inserted, %s duplicates, "
            "%s employees created.",
            dev_name,
            new_count,
            dup_count,
            employee_created_count,
        )

        return {
            "status": "success",
            "device_id": dev_id,
            "device_name": dev_name,
            "ip_address": ip_address,
            "total_retrieved": len(logs_list),
            "new_inserted": new_count,
            "duplicates_skipped": dup_count,
            "employees_created": employee_created_count,
            "last_log_download_date": (
                max_log_dt.strftime("%Y-%m-%d %H:%M:%S")
                if max_log_dt
                else None
            ),
        }


    @classmethod
    def process_adms_punch_batch(
        cls,
        db1: Session,
        db2: Session,
        device_sn: str,
        punches: list,
    ) -> Dict[str, Any]:
        """
        Process real-time biometric punches pushed via ADMS / iclock protocol.
        Writes logs to DB1 monthly table and links new employees in DB2.
        """
        if not punches:
            return {"status": "empty", "total": 0, "inserted": 0, "duplicates": 0}

        dev_id = 1
        dev_name = f"ADMS Device {device_sn}"
        last_download = None

        if device_sn:
            device = db1.execute(
                text("""
                    SELECT TOP 1 DeviceId, DeviceFName, LastLogDownloadDate
                    FROM dbo.Devices
                    WHERE SerialNumber = :sn
                """),
                {"sn": device_sn.strip()},
            ).first()

            if device:
                dev_id = device.DeviceId
                dev_name = device.DeviceFName or dev_name
                last_download = device.LastLogDownloadDate
            else:
                any_dev = db1.execute(
                    text("SELECT TOP 1 DeviceId, DeviceFName, LastLogDownloadDate FROM dbo.Devices ORDER BY DeviceId ASC")
                ).first()
                if any_dev:
                    dev_id = any_dev.DeviceId
                    last_download = any_dev.LastLogDownloadDate

        now = datetime.now()
        new_count = 0
        dup_count = 0
        employee_created_count = 0
        max_log_dt = last_download

        try:
            for item in punches:
                user_id = str(item.get("UserId", "")).strip()
                if not user_id:
                    continue

                log_dt = item.get("LogDate")
                if not isinstance(log_dt, datetime):
                    continue

                was_created = cls._ensure_employee_on_first_checkin(
                    db1=db1,
                    db2=db2,
                    essl_user_id=user_id,
                )
                if was_created:
                    employee_created_count += 1

                io_mode = str(item.get("InOutMode", 0))
                v_mode = str(item.get("VerifyMode", 15))
                w_code = str(item.get("WorkCode", 0))

                table = cls._ensure_monthly_table(db1, log_dt.month, log_dt.year)

                exists = db1.execute(
                    text(f"""
                        SELECT 1
                        FROM {table}
                        WHERE UserId = :uid AND LogDate = :ldt
                    """),
                    {"uid": user_id, "ldt": log_dt},
                ).first()

                if exists:
                    dup_count += 1
                    continue

                db1.execute(
                    text(f"""
                        INSERT INTO {table} (
                            DeviceId, LogDate, UserId, Direction,
                            DownloadDate, WorkCode, C1, C4, C5,
                            UpdateFlag, CreatedDate
                        )
                        VALUES (
                            :dev_id, :ldt, :uid, '',
                            :down_dt, :w_code, 'in', :c4, :c5,
                            0, :created_dt
                        )
                    """),
                    {
                        "dev_id": dev_id,
                        "ldt": log_dt,
                        "uid": user_id,
                        "down_dt": now,
                        "w_code": w_code,
                        "c4": io_mode,
                        "c5": v_mode,
                        "created_dt": now,
                    },
                )
                new_count += 1

                if max_log_dt is None or log_dt > max_log_dt:
                    max_log_dt = log_dt

            if max_log_dt and max_log_dt > (last_download or datetime(1900, 1, 1)):
                db1.execute(
                    text("""
                        UPDATE dbo.Devices
                        SET LastLogDownloadDate = :max_dt
                        WHERE DeviceId = :dev_id
                    """),
                    {"max_dt": max_log_dt, "dev_id": dev_id},
                )

            db1.commit()
            db2.commit()

        except Exception:
            db1.rollback()
            db2.rollback()
            logger.exception("Failed to process ADMS punches for %s", device_sn)
            raise

        logger.info(
            "ADMS %s: %s punches received (%s inserted, %s dups, %s new employees)",
            device_sn,
            len(punches),
            new_count,
            dup_count,
            employee_created_count,
        )

        return {
            "status": "success",
            "device_sn": device_sn,
            "total": len(punches),
            "inserted": new_count,
            "duplicates": dup_count,
            "employees_created": employee_created_count,
        }
