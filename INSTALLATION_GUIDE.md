# Installation & Setup Guide — IPCMS

This document provides a step-by-step installation guide to set up the **Integrated Patient Care Management System (IPCMS)** locally on a Windows machine.

---

## 1. Prerequisites

Make sure the following software is installed on your system:
1. **Python 3.8+** (Ensure Python is added to your system `PATH`)
2. **MySQL Server 8.0+** (Running locally on port 3306 or on a network host)

---

## 2. Step-by-Step Installation

### Step 2.1: Clone or Navigate to the Workspace
Open your PowerShell/Terminal window and navigate to the project directory:
```powershell
cd d:\Meghna\Integrated_Patient_Care
```

### Step 2.2: Set Up Virtual Environment
Create a clean virtual Python environment:
```powershell
python -m venv .venv
```
Activate the virtual environment:
```powershell
.venv\Scripts\activate
```

### Step 2.3: Install System Dependencies
Install all package requirements using `pip`:
```powershell
pip install -r requirements.txt
```

### Step 2.4: Configure Environment Settings
Create a `.env` file in the project root folder. You can copy the sample configuration file `.env.example`:
```powershell
copy .env.example .env
```
Open `.env` and fill in your MySQL database connection credentials:
```ini
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=hospital_db
SECRET_KEY=generate_a_random_hex_key
```

### Step 2.5: Build Database & Seed Defaults
Run the database setup script. This script will automatically create the target database schema, compile the DDL structure, validate relationships, and seed roles, departments, user profiles, appointments, and EHR records:
```powershell
python setup_database.py
```

### Step 2.6: Run Local Server
Start the development server using:
```powershell
python run.py
```
Open your web browser and navigate to:
[http://127.0.0.1:5000/](http://127.0.0.1:5000/)

---

## 3. Seed Credentials for Quick Login

The following credentials are seeded by `setup_database.py` for testing and evaluation:
* **Administrator:** `admin@ipcms.com` / `admin123`
* **Doctor:** `doctor@ipcms.com` / `doctor123`
* **Nurse:** `nurse@ipcms.com` / `nurse123`
* **Patient:** `patient@ipcms.com` / `patient123`
