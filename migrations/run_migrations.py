"""
Migration Runner for Scoto ERP (MSSQL)
Applies SQL migrations safely to the target database configured in .env (DB_KEY_DB2).

Usage:
    python migrations/run_migrations.py
    python migrations/run_migrations.py --db SCOTO_ACC_ERP
"""
import os
import sys
import re
import argparse
import pymssql

# Add project root to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from src.core.config import settings

def run_migration_file(cursor, file_path: str):
    print(f"--> Executing: {os.path.basename(file_path)}")
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Strip USE statements so we don't accidentally switch databases
    text_clean = re.sub(r'USE\s+\[.*?\]\s*;?', '', text, flags=re.IGNORECASE)
    
    # Split into batches by GO
    batches = [b.strip() for b in re.split(r'^\s*GO\s*$', text_clean, flags=re.MULTILINE | re.IGNORECASE) if b.strip()]

    for idx, batch in enumerate(batches, 1):
        try:
            cursor.execute(batch)
        except Exception as e:
            print(f"    [!] Warning/Error on batch {idx}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Run MSSQL migrations for Scoto ERP")
    parser.add_argument("--db", type=str, default=None, help="Target database name (default: from .env DB_KEY_DB2)")
    parser.add_argument("--server", type=str, default=None, help="MSSQL server host (default: from .env MSSQL_SERVER)")
    parser.add_argument("--port", type=int, default=None, help="MSSQL port (default: from .env MSSQL_PORT)")
    parser.add_argument("--user", type=str, default=None, help="MSSQL username (default: from .env MSSQL_USER)")
    parser.add_argument("--password", type=str, default=None, help="MSSQL password (default: from .env MSSQL_PASSWORD)")
    parser.add_argument("--file", type=str, default=None, help="Specific migration file to run (optional)")
    args = parser.parse_args()

    target_server = args.server or settings.MSSQL_SERVER
    target_port = args.port or settings.MSSQL_PORT
    target_user = args.user or settings.MSSQL_USER
    target_password = args.password if args.password is not None else settings.MSSQL_PASSWORD
    target_db = args.db or settings.databases_map.get("db2", "SCOTO_ACC_ERP")

    print(f"=== Running Migrations on Database: [{target_db}] ===")
    print(f"Server: {target_server}:{target_port} | User: {target_user}")

    try:
        conn = pymssql.connect(
            server=target_server,
            port=target_port,
            user=target_user,
            password=target_password,
            database=target_db,
            autocommit=True
        )
    except Exception as e:
        print(f"\n[X] Connection Failed: {e}")
        print("\nTroubleshooting tips for Error 18456 (Login failed for user):")
        print("  1. Verify the SQL password for user 'sa' in your .env file (MSSQL_PASSWORD).")
        print("  2. Or pass credentials directly via CLI: python migrations/run_migrations.py --user sa --password <YOUR_PASSWORD> --db scotoAdmin")
        print("  3. Alternatively, open the SQL scripts directly in SQL Server Management Studio (SSMS) using Windows Authentication.\n")
        sys.exit(1)

    cursor = conn.cursor()

    migrations_dir = os.path.join(root_dir, "migrations")

    if args.file:
        files = [os.path.join(migrations_dir, args.file)]
    else:
        # Run all incremental migrations (03, 04, 05, 06...) in order
        files = sorted([
            os.path.join(migrations_dir, f)
            for f in os.listdir(migrations_dir)
            if f.endswith(".sql") and not f.startswith("01_") and not f.startswith("02_")
        ])

    for f in files:
        if os.path.exists(f):
            run_migration_file(cursor, f)
        else:
            print(f"[X] File not found: {f}")

    conn.close()
    print("=== Migration process finished! ===")

if __name__ == "__main__":
    main()

