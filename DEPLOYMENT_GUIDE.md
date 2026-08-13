# Integrated Patient Care Management System (IPCMS)
## Production & Deployment Guide

This guide provides step-by-step instructions to deploy, configure, run, and maintain IPCMS on a clean Windows machine or production server.

---

### System Requirements

- **Operating System**: Windows 10/11 or Windows Server 2019+
- **Python**: Python 3.10+ (Recommended: 3.13)
- **Database**: MySQL 8.0 Server (Running on localhost:3306 or remote host)
- **Network Port**: 5000 (Default Flask web server port)

---

### Step 1: Environment Setup & Dependencies

1. **Clone or Copy Codebase**:
   ```cmd
   git clone <repository_url> Integrated_Patient_Care
   cd Integrated_Patient_Care
   ```

2. **Create Python Virtual Environment**:
   ```cmd
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```cmd
   pip install -r requirements.txt
   ```

---

### Step 2: Configuration & Environment Variables

1. **Copy Environment Template**:
   ```cmd
   copy .env.example .env
   ```

2. **Configure `.env` Secrets**:
   Open `.env` and set your credentials:
   ```env
   DB_USER=root
   DB_PASSWORD=your_actual_mysql_password
   DB_HOST=localhost
   DB_PORT=3306
   DB_NAME=hospital_db

   SECRET_KEY=generate_a_secure_random_key_here
   FLASK_ENV=production
   ```

   *To generate a secure SECRET_KEY*:
   ```cmd
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

---

### Step 3: Database Initialization & Seeding

Run the database setup script to verify MySQL liveness, create tables, and populate default seed data & roles:

```cmd
.venv\Scripts\python.exe setup_database.py
```

Default System Roles & Accounts Created:
- **Admin**: `admin@ipcms.com` / `admin123`
- **Doctor**: `doctor@ipcms.com` / `doctor123`
- **Nurse**: `nurse@ipcms.com` / `nurse123`
- **Patient**: `patient@ipcms.com` / `patient123`
- **Pharmacist**: `pharmacist@ipcms.com` / `pharm123`

---

### Step 4: Running the Application

#### Development / Testing Mode:
```cmd
.venv\Scripts\python.exe run.py
```

#### Production Deployment (Waitress WSGI Server on Windows):
```cmd
pip install waitress
waitress-serve --port=5000 app:create_app()
```

Access the application in browser at: `http://localhost:5000`

---

### Step 5: Database Backup & Recovery Procedures

#### 1. Execute Database Backup:
Exports database schema and records into a timestamped `.sql` file in `backups/`:
```cmd
.venv\Scripts\python.exe scripts/backup_database.py
```

#### 2. Restore Database from Backup:
Restores schema and data from the latest backup file:
```cmd
.venv\Scripts\python.exe scripts/restore_database.py
```

Or specify a target backup file:
```cmd
.venv\Scripts\python.exe scripts/restore_database.py backups/hospital_db_backup_20260813_233809.sql
```

---

### Step 6: Smoke Testing & Verification

Run the automated test suite to ensure all 44 unit and integration tests pass cleanly:

```cmd
.venv\Scripts\python.exe -m unittest discover tests
```

Expected Output:
```text
Ran 44 tests in 18.824s
OK
```
