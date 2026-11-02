import logging
import re
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from src.api.deps import get_mssql_session
from src.services.device_service import DeviceService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["eSSL / ZKTeco ADMS Push Protocol"])


def parse_adms_attlog(raw_text: str) -> List[Dict[str, Any]]:
    """
    Parse ZKTeco/eSSL ADMS attendance log data.
    Supports tab-delimited, key-value (PIN=...), and regex-delimited lines.
    """
    records = []
    if not raw_text:
        return records

    lines = raw_text.strip().splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 1. Key-value format (PIN=1	TIME=2026-10-14 11:00:00...)
        if "pin=" in line.lower() or "checktime=" in line.lower():
            kv_dict = {}
            for part in re.split(r"[\t, ]+", line):
                if "=" in part:
                    k, v = part.split("=", 1)
                    kv_dict[k.strip().lower()] = v.strip()

            user_id = kv_dict.get("pin") or kv_dict.get("userid") or kv_dict.get("user_id")
            time_str = kv_dict.get("checktime") or kv_dict.get("time") or kv_dict.get("logdate")
            io_mode = kv_dict.get("checktype") or kv_dict.get("status") or "0"
            verify_mode = kv_dict.get("verifytype") or kv_dict.get("verifymode") or "15"
            work_code = kv_dict.get("workcode") or "0"

            if user_id and time_str:
                try:
                    log_dt = datetime.strptime(time_str[:19], "%Y-%m-%d %H:%M:%S")
                    records.append({
                        "UserId": user_id,
                        "LogDate": log_dt,
                        "InOutMode": io_mode,
                        "VerifyMode": verify_mode,
                        "WorkCode": work_code,
                    })
                except Exception:
                    continue
            continue

        # 2. Tab-delimited positional format:
        # col 0: UserId, col 1: LogDate, col 2: InOutMode, col 3: VerifyMode, col 4: WorkCode
        parts = [p.strip() for p in line.split("\t") if p.strip()]
        if len(parts) >= 2 and re.match(r"^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}", parts[1]):
            user_id = parts[0]
            time_str = parts[1]
            io_mode = parts[2] if len(parts) > 2 else "0"
            verify_mode = parts[3] if len(parts) > 3 else "15"
            work_code = parts[4] if len(parts) > 4 else "0"
            try:
                log_dt = datetime.strptime(time_str[:19], "%Y-%m-%d %H:%M:%S")
                records.append({
                    "UserId": user_id,
                    "LogDate": log_dt,
                    "InOutMode": io_mode,
                    "VerifyMode": verify_mode,
                    "WorkCode": work_code,
                })
                continue
            except Exception:
                pass

        # 3. Regex fallback (space, comma, or mixed delimiters)
        match = re.match(
            r"^\s*([^\s\t,]+)[\t, ]+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})(?:[\t, ]+(\d+))?(?:[\t, ]+(\d+))?(?:[\t, ]+(\d+))?",
            line,
        )
        if match:
            user_id = match.group(1)
            time_str = match.group(2)
            io_mode = match.group(3) or "0"
            verify_mode = match.group(4) or "15"
            work_code = match.group(5) or "0"
            try:
                log_dt = datetime.strptime(time_str[:19], "%Y-%m-%d %H:%M:%S")
                records.append({
                    "UserId": user_id,
                    "LogDate": log_dt,
                    "InOutMode": io_mode,
                    "VerifyMode": verify_mode,
                    "WorkCode": work_code,
                })
            except Exception:
                pass

    return records


@router.api_route("/cdata.aspx", methods=["GET", "POST"])
@router.api_route("/cdata", methods=["GET", "POST"])
async def iclock_cdata(
    request: Request,
    db1: Session = Depends(get_mssql_session("db1")),
    db2: Session = Depends(get_mssql_session("db2")),
):
    """
    Main communication endpoint for eSSL / ZKTeco ADMS devices.
    - GET: Device handshake & parameter exchange.
    - POST: Device attendance punches & operational logs.
    """
    qp = request.query_params
    sn = qp.get("SN") or qp.get("sn") or ""
    table = qp.get("table") or qp.get("TABLE") or ""
    options = qp.get("options") or qp.get("OPTIONS") or ""

    if request.method == "GET":
        if options.lower() == "all":
            logger.info("Handshake received from ADMS device SN: %s", sn)
            response_text = (
                f"GET OPTION FROM: {sn}\n"
                f"Stamp=9999\n"
                f"OpStamp=0\n"
                f"PhotoStamp=0\n"
                f"ErrorDelay=60\n"
                f"Delay=10\n"
                f"TransTimes=00:00;14:05\n"
                f"TransInterval=1\n"
                f"TransFlag=TransData AttLog\tOpLog\tAttPhoto\tEnrollUser\tChgUser\tEnrollFP\tChgFP\tUserPic\tFACE\n"
                f"TimeZone=330\n"
                f"Realtime=1\n"
                f"Encrypt=0\n"
                f"ServerVersion=2.4.1\n"
            )
            return Response(content=response_text, media_type="text/plain")

        return Response(content="OK\n", media_type="text/plain")

    # POST method:
    raw_body = (await request.body()).decode("utf-8", errors="ignore")

    if table.upper() == "ATTLOG":
        punches = parse_adms_attlog(raw_body)
        if punches:
            try:
                DeviceService.process_adms_punch_batch(
                    db1=db1,
                    db2=db2,
                    device_sn=sn,
                    punches=punches,
                )
                logger.info("Successfully processed %d ADMS punches for device %s", len(punches), sn)
                return Response(content=f"OK: {len(punches)}\n", media_type="text/plain")
            except Exception as e:
                logger.error("Failed to store ADMS punches: %s", e)
                return Response(content="OK\n", media_type="text/plain")

        return Response(content="OK: 0\n", media_type="text/plain")

    return Response(content="OK\n", media_type="text/plain")


@router.api_route("/getrequest", methods=["GET", "POST"])
@router.api_route("/getrequest.aspx", methods=["GET", "POST"])
def iclock_getrequest(request: Request):
    """Device command poll endpoint."""
    return Response(content="OK\n", media_type="text/plain")


@router.api_route("/devicecmd", methods=["GET", "POST"])
@router.api_route("/devicecmd.aspx", methods=["GET", "POST"])
def iclock_devicecmd(request: Request):
    """Device command acknowledgement endpoint."""
    return Response(content="OK\n", media_type="text/plain")


@router.api_route("/fdata", methods=["GET", "POST"])
@router.api_route("/fdata.aspx", methods=["GET", "POST"])
def iclock_fdata(request: Request):
    """Biometric template / photo upload endpoint."""
    return Response(content="OK\n", media_type="text/plain")
