# API Documentation — IPCMS Endpoint Specification

This document details all HTTP endpoints, route parameters, methods, validation payloads, and role-based authorization constraints for the **Integrated Patient Care Management System (IPCMS)**.

---

## 1. Authentication Blueprint (`/auth`)

### 1.1 POST `/auth/login`
- **Description:** Establish session credentials.
- **Roles:** Anonymous visitors.
- **Form Data (WTForms):**
  - `email` (String, required, valid email format)
  - `password` (String, required)
  - `remember_me` (Boolean, optional)
- **Response:** Redirects to `/dashboard` on success; re-renders `/auth/login` on failure.

### 1.2 GET `/auth/logout`
- **Description:** Terminate session credentials.
- **Roles:** Logged-in users.
- **Response:** Redirects to `/auth/login`.

---

## 2. Patients Blueprint (`/patient`)

### 2.1 GET `/patient/list`
- **Description:** Directory list of active patients.
- **Roles:** `Admin`, `Nurse`, `Doctor`.
- **Query Parameters:**
  - `q` (String, optional) — search keyword.
  - `page` (Int, optional, default 1) — page index.
  - `sort` (String, default 'last_name') — sort column.
  - `direction` (String, default 'asc') — sort direction.
- **Response:** Renders `templates/patients/list.html`.

### 2.2 POST `/patient/add`
- **Description:** Register a new patient and create a login account.
- **Roles:** `Admin`, `Nurse`.
- **Form Data:**
  - `first_name`, `last_name`, `age` (Int), `gender` (Select), `blood_group` (Select), `phone_number`, `email` (Unique), `address`, `medical_history`.
- **Response:** Redirects to `/patient/list` on success.

### 2.3 POST `/patient/edit/<int:patient_id>`
- **Description:** Update demographics.
- **Roles:** `Admin`, `Nurse`, or the `Patient` owner themselves.
- **Response:** Redirects to profile details page.

### 2.4 POST `/patient/delete/<int:patient_id>`
- **Description:** Soft-delete patient credential account.
- **Roles:** `Admin`, `Nurse`.
- **Response:** Redirects to directory.

### 2.5 GET `/patient/view/<int:patient_id>`
- **Description:** Detailed patient demographics, scheduled consultations, and EHR notes.
- **Roles:** `Admin`, `Nurse`, `Doctor`, or the `Patient` owner themselves.

---

## 3. Doctors Blueprint (`/doctor`)

### 3.1 GET `/doctor/list`
- **Description:** Directory list of active doctors.
- **Roles:** `Admin`, `Nurse`, `Doctor`.
- **Query Parameters:** `q`, `page`, `sort`, `direction`.

### 3.2 POST `/doctor/add`
- **Description:** Register a doctor profile and linked login account.
- **Roles:** `Admin`.
- **Form Data:** `first_name`, `last_name`, `specialization`, `qualification`, `department_id`, `contact_number`, `email_address` (Unique), `available_time` (e.g. "10:00 AM - 01:00 PM").

### 3.3 POST `/doctor/edit/<int:doctor_id>`
- **Description:** Update clinical profile details and availability hours.
- **Roles:** `Admin`, or the `Doctor` themselves.

### 3.4 POST `/doctor/delete/<int:doctor_id>`
- **Description:** Soft-delete doctor credential account.
- **Roles:** `Admin`.

### 3.5 GET `/doctor/view/<int:doctor_id>`
- **Description:** Detailed clinical profile, department, and upcoming consultation agenda.
- **Roles:** `Admin`, `Nurse`, `Doctor`, `Patient`.

---

## 4. Nurses Blueprint (`/nurse`)

### 4.1 GET `/nurse/list`
- **Description:** Directory list of active nurses.
- **Roles:** `Admin`, `Nurse`, `Doctor`.

### 4.2 POST `/nurse/add`
- **Description:** Register a nurse and linked login account.
- **Roles:** `Admin`.
- **Form Data:** `first_name`, `last_name`, `department_id`, `shift` (Morning/Evening/Night), `contact_number`, `email` (Unique).

### 4.3 POST `/nurse/edit/<int:nurse_id>`
- **Description:** Update shift or department details.
- **Roles:** `Admin`, or the `Nurse` themselves.

### 4.4 POST `/nurse/delete/<int:nurse_id>`
- **Description:** Soft-delete nurse credential account.
- **Roles:** `Admin`.

### 4.5 GET `/nurse/view/<int:nurse_id>`
- **Description:** View detailed nurse profile.
- **Roles:** `Admin`, `Nurse`, `Doctor`, `Patient`.

---

## 5. Appointments Blueprint (`/appointment`)

### 5.1 GET `/appointment/list`
- **Description:** Filterable list of all appointments.
- **Roles:** `Admin`, `Nurse`, `Doctor`.
- **Query Parameters:** `date` (YYYY-MM-DD), `doctor_id`, `patient_id`, `status`.

### 5.2 POST `/appointment/book`
- **Description:** Schedule a consultation.
- **Roles:** `Admin`, `Nurse`, `Patient`.
- **Form Data:** `patient_id` (Omitted/hidden for Patient self-bookings), `doctor_id`, `appointment_date`, `appointment_time`.
- **Validations Checked:** Doctor availability hours, doctor duplicate slot checks, patient duplicate slot checks, future date validation.

### 5.3 POST `/appointment/edit/<int:appointment_id>`
- **Description:** Reschedule/modify consultation details or status.
- **Roles:** `Admin`, `Nurse`.

### 5.4 POST `/appointment/cancel/<int:appointment_id>`
- **Description:** Cancel an appointment.
- **Roles:** `Admin`, `Nurse`, or the `Patient` booking owner.

### 5.5 GET `/appointment/doctor/<int:doctor_id>/schedule`
- **Description:** View doctor daily chronological timetable schedule.
- **Roles:** `Admin`, `Nurse`, `Doctor`.
- **Query Parameters:** `date` (YYYY-MM-DD, defaults to today).
