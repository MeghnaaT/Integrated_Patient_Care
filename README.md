# Integrated Patient Care Management System (IPCMS)

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Flask Version](https://img.shields.io/badge/flask-3.0%2B-green.svg)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/database-MySQL%208.0%2B-orange.svg)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/license-HIPAA--Aligned-red.svg)]()

Welcome to the **Integrated Patient Care Management System (IPCMS)**. This is a comprehensive, production-ready web application built to streamline operations across modern clinical environments. The system facilitates role-based access for Administrators, Doctors, Nurses, and Patients, ensuring secure demographics indexing, appointment scheduling, and Electronic Health Records (EHR) management.

---

## 1. Feature Map (Milestone 1)

### 🔑 Authentication & Role-Based Access Control (RBAC)
- Multi-role gateway supporting **Admin**, **Doctor**, **Nurse**, and **Patient**.
- Enforces route decorators to block cross-role unauthorized queries.
- Utilizes cryptographically secure passwords (Werkzeug Scrypt hashing).
- Supports soft-delete states: instead of deleting billing or medical history data, soft-deletion disables the linked `User` record (`is_active = False`).

### 👥 Demographic Management (CRUD)
- **Patient Management:** Create, view, paginate, sort, search, and edit patient demographics (age, gender, blood group, phone, address, and history).
- **Doctor Management:** Clinical specialization, qualification, department, contact, and doctor available time slot ranges.
- **Nurse Management:** Demographics sync, department mapping, and custom shifts (**Morning**, **Evening**, **Night**).

### 📅 Consultation & Appointment Scheduling
- **Doctor Hours Parser:** Parses human-readable availability ranges (e.g. `'10:00 AM - 01:00 PM'`) and validates requested times against doctor hours.
- **Collision Detection (Anti-Double Booking):** Prevents double-bookings for the same doctor or same patient at the exact same Date and Time.
- **Chronological Agendas:** Doctor schedule timetable displaying daily agendas.
- **Status Workflows:** Booking states: **Pending**, **Confirmed**, **Completed**, and **Cancelled**.

### 📊 Role-Specific Analytical Dashboards
- **Admin:** System performance stats, gender breakdown charts, status breakdown charts, side-by-side recent bookings, and quick action cards.
- **Doctor:** Today's consultation counts, backlog details, personal status charts, and recent EHR entries.
- **Nurse:** Active patient lists, today's chronological schedule, and registration actions.
- **Patient:** Booked session metrics, personal EHR medical records history, and inline appointment cancellations.

---

## 2. Complete Project Documentation Portal

We have created dedicated, high-quality documentation guides for every facet of the codebase. Please navigate using the links below:

1. **[Installation & Setup Guide](file:///d:/Meghna/Integrated_Patient_Care/INSTALLATION_GUIDE.md):** Detailed guide to set up virtual environments, configure `.env` parameters, run the database compiler, and launch the development server.
2. **[Testing & Isolation Guide](file:///d:/Meghna/Integrated_Patient_Care/TESTING_GUIDE.md):** Information on our test suites, unittest discovery commands, and test isolation design.
3. **[Deployment & Security Guide](file:///d:/Meghna/Integrated_Patient_Care/DEPLOYMENT_GUIDE.md):** Guide to set up Nginx reverse proxies, systemd background daemons, SSL termination via Let's Encrypt, and secure cookie storage.
4. **[Project Structure Documentation](file:///d:/Meghna/Integrated_Patient_Care/PROJECT_STRUCTURE.md):** Visual diagram of the architecture execution flow (Controller-Service-Repository pattern) and complete file descriptions.
5. **[Database Schema Documentation](file:///d:/Meghna/Integrated_Patient_Care/DATABASE_DOCUMENTATION.md):** Full Entity Relationship Diagram (ERD), detailed table structures, foreign key constraints, and index optimization rules.
6. **[API Endpoint Documentation](file:///d:/Meghna/Integrated_Patient_Care/API_DOCUMENTATION.md):** Route mappings, request payloads, response redirects, and RBAC rules.

---

## 3. Seed Credentials for Quick Evaluation

Run `python setup_database.py` to compile the schema and seed the following default accounts:
* **Administrator Account:** `admin@ipcms.com` / password `admin123`
* **Doctor Account:** `doctor@ipcms.com` / password `doctor123`
* **Nurse Account:** `nurse@ipcms.com` / password `nurse123`
* **Patient Account:** `patient@ipcms.com` / password `patient123`
