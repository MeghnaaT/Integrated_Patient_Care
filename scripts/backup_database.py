# =============================================================================
# scripts/backup_database.py — Database Backup Utility
# =============================================================================
# Reads credentials from .env and exports MySQL database schema and data
# into a timestamped SQL backup file stored in backups/ directory.
# =============================================================================

import os
import sys
import datetime
import subprocess

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import _load_env

def run_backup():
    _load_env()
    db_user = os.environ.get('DB_USER', 'root')
    db_pass = os.environ.get('DB_PASSWORD', '')
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_port = os.environ.get('DB_PORT', '3306')
    db_name = os.environ.get('DB_NAME', 'hospital_db')

    backups_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backups'))
    os.makedirs(backups_dir, exist_ok=True)

    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backups_dir, f"{db_name}_backup_{timestamp}.sql")

    print(f"=== IPCMS Database Backup ===")
    print(f"Target Database: {db_name} on {db_host}:{db_port}")
    print(f"Output File:     {backup_file}")

    # Use mysqldump if available
    cmd = [
        "mysqldump",
        f"--host={db_host}",
        f"--port={db_port}",
        f"--user={db_user}",
        f"--result-file={backup_file}",
        "--routines",
        "--triggers",
        db_name
    ]
    if db_pass:
        cmd.insert(4, f"--password={db_pass}")

    try:
        res = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(f"SUCCESS: Database backup completed successfully!")
        print(f"File created: {backup_file} ({os.path.getsize(backup_file)} bytes)")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Notice: mysqldump utility not in PATH. Using PyMySQL Python fallback dumper...")
        return py_backup_fallback(db_user, db_pass, db_host, db_port, db_name, backup_file)

def py_backup_fallback(user, password, host, port, dbname, out_file):
    """Python fallback dumper using PyMySQL when mysqldump is not in PATH."""
    import pymysql
    try:
        conn = pymysql.connect(host=host, port=int(port), user=user, password=password, database=dbname)
        cursor = conn.cursor()
        
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]

        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(f"-- IPCMS MySQL Database Backup Fallback\n")
            f.write(f"-- Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"CREATE DATABASE IF NOT EXISTS `{dbname}`;\nUSE `{dbname}`;\n\n")

            for table in tables:
                cursor.execute(f"SHOW CREATE TABLE `{table}`")
                create_stmt = cursor.fetchone()[1]
                f.write(f"DROP TABLE IF EXISTS `{table}`;\n")
                f.write(f"{create_stmt};\n\n")

                cursor.execute(f"SELECT * FROM `{table}`")
                rows = cursor.fetchall()
                if rows:
                    cursor.execute(f"SHOW COLUMNS FROM `{table}`")
                    cols = [f"`{col[0]}`" for col in cursor.fetchall()]
                    cols_str = ", ".join(cols)

                    for row in rows:
                        vals = []
                        for val in row:
                            if val is None:
                                vals.append("NULL")
                            elif isinstance(val, (int, float)):
                                vals.append(str(val))
                            else:
                                escaped_val = str(val).replace("'", "''").replace("\\", "\\\\")
                                vals.append(f"'{escaped_val}'")
                        vals_str = ", ".join(vals)
                        f.write(f"INSERT INTO `{table}` ({cols_str}) VALUES ({vals_str});\n")
                    f.write("\n")

        conn.close()
        print(f"SUCCESS: Python fallback backup completed successfully!")
        print(f"File created: {out_file} ({os.path.getsize(out_file)} bytes)")
        return True
    except Exception as ex:
        print(f"ERROR: Backup failed: {ex}")
        return False

if __name__ == '__main__':
    run_backup()
