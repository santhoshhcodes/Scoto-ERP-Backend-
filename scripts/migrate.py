"""
Automated Database Migration Runner for Scoto_Admin_ERP
Usage: 
    python scripts/migrate.py          # Safely applies schema and seeds
    python scripts/migrate.py --reset  # Drops existing tables and rebuilds fresh
"""
import os
import sys
import re
import argparse
from sqlalchemy import create_engine, text

# Adjust import to reach scoto-backend root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.core.config import settings

def run_migration(reset=False):
    # 1. Connect to master database to check/create Scoto_Admin_ERP
    master_uri = (
        f"mssql+pymssql://{settings.MSSQL_USER}:{settings.MSSQL_PASSWORD}"
        f"@{settings.MSSQL_SERVER}:{settings.MSSQL_PORT}/master"
    )
    engine = create_engine(master_uri, isolation_level="AUTOCOMMIT")

    print("Connecting to Microsoft SQL Server...")
    with engine.connect() as conn:
        print("Checking/Creating database [Scoto_Admin_ERP]...")
        conn.execute(text("IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'Scoto_Admin_ERP') CREATE DATABASE [Scoto_Admin_ERP]"))

    # 2. Connect directly to Scoto_Admin_ERP
    db_uri = (
        f"mssql+pymssql://{settings.MSSQL_USER}:{settings.MSSQL_PASSWORD}"
        f"@{settings.MSSQL_SERVER}:{settings.MSSQL_PORT}/Scoto_Admin_ERP"
    )
    db_engine = create_engine(db_uri, isolation_level="AUTOCOMMIT")

    base_dir = os.path.dirname(__file__)
    schema_file = os.path.join(base_dir, "..", "migrations", "01_schema_Scoto_Admin_ERP.sql")
    seed_file = os.path.join(base_dir, "..", "migrations", "02_seed_Scoto_Admin_ERP.sql")

    with db_engine.connect() as conn:
        if reset:
            print("Reset flag detected: Dropping existing tables in [Scoto_Admin_ERP]...")
            # Drop foreign keys first if any, then tables
            drop_fks = """
                DECLARE @sql NVARCHAR(MAX) = N'';
                SELECT @sql += N'ALTER TABLE ' + QUOTENAME(OBJECT_SCHEMA_NAME(parent_object_id))
                    + '.' + QUOTENAME(OBJECT_NAME(parent_object_id)) 
                    + ' DROP CONSTRAINT ' + QUOTENAME(name) + ';'
                FROM sys.foreign_keys;
                EXEC sp_executesql @sql;
            """
            conn.execute(text(drop_fks))

            drop_tables = """
                DECLARE @sql NVARCHAR(MAX) = N'';
                SELECT @sql += N'DROP TABLE ' + QUOTENAME(TABLE_SCHEMA) + '.' + QUOTENAME(TABLE_NAME) + ';'
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE';
                EXEC sp_executesql @sql;
            """
            conn.execute(text(drop_tables))
            print("[OK] Existing tables dropped cleanly.")

        print("Executing 01_schema_Scoto_Admin_ERP.sql (33 tables)...")
        with open(schema_file, "r", encoding="utf-8") as f:
            content = f.read()
            batches = re.split(r'^\s*GO\s*$', content, flags=re.MULTILINE | re.IGNORECASE)
            for batch in batches:
                cmd = batch.strip()
                if cmd:
                    conn.execute(text(cmd))
        print("[OK] Schema completed.")

        print("Executing 02_seed_Scoto_Admin_ERP.sql (Initial records)...")
        with open(seed_file, "r", encoding="utf-8") as f:
            content = f.read()
            batches = re.split(r'^\s*GO\s*$', content, flags=re.MULTILINE | re.IGNORECASE)
            for batch in batches:
                cmd = batch.strip()
                if cmd:
                    conn.execute(text(cmd))
        print("[OK] Seed completed.")

    print("\nSUCCESS: Database [Scoto_Admin_ERP] is fully initialized and ready!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scoto_Admin_ERP Migration Runner")
    parser.add_argument("--reset", action="store_true", help="Drop existing tables and rebuild schema cleanly")
    args = parser.parse_args()

    run_migration(reset=args.reset)
