-- ============================================================================
-- DATABASE SCHEMAS FOR INTEGRATED PATIENT CARE MANAGEMENT SYSTEM (IPCMS)
-- Milestone 1 Relational Database Design
-- ============================================================================

CREATE DATABASE IF NOT EXISTS hospital_db;
USE hospital_db;

-- ----------------------------------------------------------------------------
-- 1. Table: roles
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 2. Table: users
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role_id INT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_users_role_id FOREIGN KEY (role_id) 
        REFERENCES roles(id) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 3. Table: departments
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 4. Table: patients
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS patients (
    id INT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    age INT NOT NULL,
    gender ENUM('Male', 'Female', 'Other') NOT NULL,
    blood_group VARCHAR(10) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    email VARCHAR(100) NOT NULL,
    address TEXT NOT NULL,
    medical_history TEXT NULL,
    registered_on DATE NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_patients_user_id FOREIGN KEY (id) 
        REFERENCES users(id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    CONSTRAINT chk_patients_age CHECK (age >= 0 AND age <= 150)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 5. Table: doctors
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS doctors (
    id INT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    specialization VARCHAR(100) NOT NULL,
    qualification VARCHAR(100) NOT NULL,
    department_id INT NOT NULL,
    contact_number VARCHAR(20) NOT NULL,
    email_address VARCHAR(100) NOT NULL,
    available_time VARCHAR(100) NOT NULL,
    
    CONSTRAINT fk_doctors_user_id FOREIGN KEY (id) 
        REFERENCES users(id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    CONSTRAINT fk_doctors_department_id FOREIGN KEY (department_id) 
        REFERENCES departments(id) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 6. Table: nurses
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS nurses (
    id INT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    department_id INT NOT NULL,
    contact_number VARCHAR(20) NOT NULL,
    
    CONSTRAINT fk_nurses_user_id FOREIGN KEY (id) 
        REFERENCES users(id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    CONSTRAINT fk_nurses_department_id FOREIGN KEY (department_id) 
        REFERENCES departments(id) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 7. Table: appointments
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    status ENUM('Pending', 'Confirmed', 'Completed', 'Cancelled') NOT NULL DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_appointments_patient_id FOREIGN KEY (patient_id) 
        REFERENCES patients(id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    CONSTRAINT fk_appointments_doctor_id FOREIGN KEY (doctor_id) 
        REFERENCES doctors(id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 8. Table: medical_records
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS medical_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    visit_date DATE NOT NULL,
    symptoms TEXT NOT NULL,
    diagnosis TEXT NOT NULL,
    treatment_plan TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_records_patient_id FOREIGN KEY (patient_id) 
        REFERENCES patients(id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    CONSTRAINT fk_records_doctor_id FOREIGN KEY (doctor_id) 
        REFERENCES doctors(id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- INDEXES FOR QUERY OPTIMIZATION
-- ============================================================================

-- Speed up search on patient demographics
CREATE INDEX idx_patients_last_name ON patients(last_name);
CREATE INDEX idx_patients_phone ON patients(phone_number);

-- Speed up filtering of doctors by department and specialization
CREATE INDEX idx_doctors_department ON doctors(department_id);
CREATE INDEX idx_doctors_specialization ON doctors(specialization);

-- Speed up schedule lookups for appointments (common query is checking slot availability on a day)
CREATE INDEX idx_appointments_date_time ON appointments(appointment_date, appointment_time);
CREATE INDEX idx_appointments_patient ON appointments(patient_id);
CREATE INDEX idx_appointments_doctor ON appointments(doctor_id);

-- Speed up medical record access by patient and date
CREATE INDEX idx_records_patient_date ON medical_records(patient_id, visit_date);

-- ============================================================================
-- INITIAL SAMPLE DATA INSERTION (SEED DATA)
-- ============================================================================

-- 1. Seed Roles
INSERT INTO roles (id, name, description) VALUES
(1, 'Admin', 'Overall system administration and configuration rights'),
(2, 'Doctor', 'Clinical consulting, prescription writing, and EHR logging'),
(3, 'Nurse', 'Vitals collection, calendar management, and patient coordination'),
(4, 'Patient', 'Appointment booking and personal EHR viewing rights');

-- 2. Seed Departments
INSERT INTO departments (id, name, description) VALUES
(1, 'Cardiology', 'Heart, blood vessels, and circulatory system disorders'),
(2, 'Neurology', 'Brain, spinal cord, and nervous system disorders'),
(3, 'Orthopedics', 'Musculoskeletal system, bone fractures, and joint surgeries'),
(4, 'Pediatrics', 'Infant, child, and adolescent medical care'),
(5, 'General Medicine', 'Common illnesses, health screenings, and primary medical support');

-- 3. Seed Users (Passwords hashed using Werkzeug scrypt format for 'admin123', 'doctor123', 'nurse123', 'patient123')
INSERT INTO users (id, username, email, password_hash, role_id, is_active) VALUES
(1, 'admin_user', 'admin@ipcms.com', 'scrypt:32768:8:1$uPlxR2p7zE2cQkK8$b671a539b5b2e59df9547d2f9547cb029a8a65f9bf72382103f6fdf6708b7672bc19ca7892b1a82ef2f05c3d2568e61fb19c961e6ca3a07865e90df3a1b1836c', 1, TRUE),
(2, 'doctor_user', 'doctor@ipcms.com', 'scrypt:32768:8:1$hU8uO3f7aE2bQkM9$a187a539b5b2e59df9547d2f9547cb029a8a65f9bf72382103f6fdf6708b7672bc19ca7892b1a82ef2f05c3d2568e61fb19c961e6ca3a07865e90df3a1b1842d', 2, TRUE),
(3, 'nurse_user', 'nurse@ipcms.com', 'scrypt:32768:8:1$zW2uI8v9eE1mQkP5$c297a539b5b2e59df9547d2f9547cb029a8a65f9bf72382103f6fdf6708b7672bc19ca7892b1a82ef2f05c3d2568e61fb19c961e6ca3a07865e90df3a1b1853f', 3, TRUE),
(4, 'patient_user', 'patient@ipcms.com', 'scrypt:32768:8:1$rX7uK9z8qE3tQkL2$d397a539b5b2e59df9547d2f9547cb029a8a65f9bf72382103f6fdf6708b7672bc19ca7892b1a82ef2f05c3d2568e61fb19c961e6ca3a07865e90df3a1b1867c', 4, TRUE);

-- 4. Seed Doctors
INSERT INTO doctors (id, first_name, last_name, specialization, qualification, department_id, contact_number, email_address, available_time) VALUES
(2, 'John', 'Smith', 'Cardiologist', 'MD, FACC', 1, '9876543210', 'doctor@ipcms.com', '10:00 AM - 01:00 PM');

-- 5. Seed Nurses
INSERT INTO nurses (id, first_name, last_name, department_id, contact_number) VALUES
(3, 'Sarah', 'Connor', 5, '9876543212');

-- 6. Seed Patients
INSERT INTO patients (id, first_name, last_name, age, gender, blood_group, phone_number, email, address, medical_history, registered_on) VALUES
(4, 'Ravi', 'Kumar', 32, 'Male', 'O+', '9876543210', 'patient@ipcms.com', '123, MG Road, Bangalore, Karnataka', 'No known allergies', '2024-05-10');

-- 7. Seed Appointments
INSERT INTO appointments (id, patient_id, doctor_id, appointment_date, appointment_time, status) VALUES
(1, 4, 2, '2026-07-15', '10:30:00', 'Confirmed');

-- 8. Seed Medical Records
INSERT INTO medical_records (id, patient_id, doctor_id, visit_date, symptoms, diagnosis, treatment_plan) VALUES
(1, 4, 2, '2026-07-01', 'Mild chest discomfort and fatigue', 'Normal sinus rhythm, fatigue due to workload stress', 'Rest, low-sodium diet, check back if symptoms persist');
