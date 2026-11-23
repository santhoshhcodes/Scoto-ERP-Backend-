import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from sqlalchemy import text
from src.api.deps import get_mssql_session

def setup():
    session_gen = get_mssql_session('db2')()
    db = next(session_gen)
    try:
        # Update SystemAdmin
        db.execute(text("""
            UPDATE UserDetails
            SET UserType = 'SystemAdmin', 
                Email = 'ho@scoto.in', 
                UserName = 'System Administrator', 
                Status = 'Approved'
            WHERE UserID = 'ADMIN'
        """))

        # Check or Insert SUPERADMIN
        super_exists = db.execute(text("SELECT UserID FROM UserDetails WHERE UserID = 'SUPERADMIN'")).first()
        if not super_exists:
            db.execute(text("""
                INSERT INTO UserDetails (Ccode, Lcode, UserID, UserName, UserType, Status, Email, IsFirstLogin)
                VALUES ('SCT', 'UNIT I', 'SUPERADMIN', 'Santhosh Kannan', 'SuperAdmin', 'Approved', 'santhoshkannan@scoto.in', 0)
            """))
        else:
            db.execute(text("""
                UPDATE UserDetails
                SET UserType = 'SuperAdmin', 
                    Email = 'santhoshkannan@scoto.in', 
                    UserName = 'Santhosh Kannan', 
                    Status = 'Approved'
                WHERE UserID = 'SUPERADMIN'
            """))

        super_login = db.execute(text("SELECT UserId FROM Login WHERE UserId = 'SUPERADMIN'")).first()
        if not super_login:
            db.execute(text("""
                INSERT INTO Login (Ccode, Lcode, UserId, Password, isLoggedIN)
                VALUES ('SCT', 'UNIT I', 'SUPERADMIN', 'admin@123', 0)
            """))

        db.commit()
        print("Admins successfully configured:")
        rows = db.execute(text("SELECT UserID, UserName, UserType, Email FROM UserDetails")).fetchall()
        for r in rows:
            print(f"  User: {r[0]} | Name: {r[1]} | Role: {r[2]} | Email: {r[3]}")
    except Exception as e:
        db.rollback()
        print("Error setting up admins:", e)
        raise
    finally:
        db.close()

if __name__ == "__main__":
    setup()
