"""
Standalone Seed Data Runner for Scoto_Admin_ERP
Usage: python scripts/seed_data.py
"""
import os
import sys
import re
from sqlalchemy import create_engine, text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.core.config import settings

def run_seed():
    db_name = settings.DB_KEY_DB2 or "Scoto_Admin_ERP"
    db_uri = (
        f"mssql+pymssql://{settings.MSSQL_USER}:{settings.MSSQL_PASSWORD}"
        f"@{settings.MSSQL_SERVER}:{settings.MSSQL_PORT}/{db_name}"
    )
    engine = create_engine(db_uri, isolation_level="AUTOCOMMIT")
    base_dir = os.path.dirname(__file__)
    seed_file = os.path.join(base_dir, "..", "migrations", "02_seed_Scoto_Admin_ERP.sql")

    with engine.connect() as conn:
        print(f"Applying seed data to [{db_name}]...")
        with open(seed_file, "r", encoding="utf-8") as f:
            batches = re.split(r'^\s*GO\s*$', f.read(), flags=re.MULTILINE | re.IGNORECASE)
            for batch in batches:
                cmd = batch.strip()
                if cmd:
                    conn.execute(text(cmd))
        print(f"[OK] Seed data successfully verified and applied to [{db_name}]!")

if __name__ == "__main__":
    run_seed()
