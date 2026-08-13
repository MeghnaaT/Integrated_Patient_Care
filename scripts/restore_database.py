# =============================================================================
# scripts/restore_database.py — Database Restore Utility
# =============================================================================
# Restores a target MySQL SQL dump file into the configured MySQL database.
# =============================================================================

import os
import sys
import subprocess

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import _load_env

def run_restore(backup_filepath=None):
    _load_env()
    db_user = os.environ.get('DB_USER', 'root')
    db_pass = os.environ.get('DB_PASSWORD', '')
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_port = os.environ.get('DB_PORT', '3306')
    db_name = os.environ.get('DB_NAME', 'hospital_db')

    backups_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backups'))

    if not backup_filepath:
        if not os.path.exists(backups_dir):
            print("ERROR: No backups directory found.")
            return False
        files = [os.path.join(backups_dir, f) for f in os.listdir(backups_dir) if f.endswith('.sql')]
        if not files:
            print("ERROR: No .sql backup files found in backups/ directory.")
            return False
        backup_filepath = max(files, key=os.path.getmtime)

    if not os.path.exists(backup_filepath):
        print(f"ERROR: File not found: {backup_filepath}")
        return False

    print(f"=== IPCMS Database Restore ===")
    print(f"Restoring File: {backup_filepath}")
    print(f"Target DB:      {db_name} on {db_host}:{db_port}")

    import pymysql
    try:
        conn = pymysql.connect(host=db_host, port=int(db_port), user=db_user, password=db_pass)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        cursor.execute(f"USE `{db_name}`;")

        with open(backup_filepath, 'r', encoding='utf-8') as f:
            sql_statements = f.read().split(';')

        for stmt in sql_statements:
            stmt_clean = stmt.strip()
            if stmt_clean and not stmt_clean.startswith('--'):
                cursor.execute(stmt_clean)

        conn.commit()
        conn.close()
        print(f"SUCCESS: Database restored successfully from {backup_filepath}!")
        return True
    except Exception as e:
        print(f"ERROR: Restore failed: {e}")
        return False

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else None
    run_restore(target)
