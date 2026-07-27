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
-- 8. Table: medical_records / consultations
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

-- ----------------------------------------------------------------------------
-- 9. Table: ehr_details (Patient Health Vitals & Summary)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ehr_details (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL UNIQUE,
    height INT NULL,
    weight INT NULL,
    bmi DECIMAL(4,1) NULL,
    smoking_status VARCHAR(50) NULL DEFAULT 'No',
    alcohol_status VARCHAR(50) NULL DEFAULT 'No',
    chronic_diseases VARCHAR(255) NULL DEFAULT 'No',
    remarks TEXT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_ehr_patient_id FOREIGN KEY (patient_id)
        REFERENCES patients(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 10. Table: allergies
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS allergies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    allergen VARCHAR(100) NOT NULL,
    reaction VARCHAR(255) NOT NULL,
    added_on DATE NOT NULL,

    CONSTRAINT fk_allergies_patient_id FOREIGN KEY (patient_id)
        REFERENCES patients(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 11. Table: patient_medications (Active Medications)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS patient_medications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    medicine VARCHAR(150) NOT NULL,
    dosage VARCHAR(100) NOT NULL,
    frequency VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,

    CONSTRAINT fk_patient_meds_patient_id FOREIGN KEY (patient_id)
        REFERENCES patients(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 12. Table: consultations
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS consultations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    consultation_date DATE NOT NULL,
    symptoms TEXT NOT NULL,
    diagnosis TEXT NOT NULL,
    treatment_notes TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_consultations_patient_id FOREIGN KEY (patient_id)
        REFERENCES patients(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_consultations_doctor_id FOREIGN KEY (doctor_id)
        REFERENCES doctors(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 13. Table: prescriptions
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS prescriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    consultation_id INT NULL,
    prescription_date DATE NOT NULL,
    special_instructions TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_prescriptions_patient_id FOREIGN KEY (patient_id)
        REFERENCES patients(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_prescriptions_doctor_id FOREIGN KEY (doctor_id)
        REFERENCES doctors(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_prescriptions_consultation_id FOREIGN KEY (consultation_id)
        REFERENCES consultations(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 14. Table: prescription_items
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS prescription_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    prescription_id INT NOT NULL,
    medicine_name VARCHAR(150) NOT NULL,
    dosage VARCHAR(100) NOT NULL,
    frequency VARCHAR(100) NOT NULL,
    duration VARCHAR(100) NOT NULL,

    CONSTRAINT fk_prescription_items_prescription_id FOREIGN KEY (prescription_id)
        REFERENCES prescriptions(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 15. Table: lab_reports
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lab_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    test_name VARCHAR(150) NOT NULL,
    test_date DATE NOT NULL,
    result VARCHAR(255) NOT NULL,
    remarks TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_lab_reports_patient_id FOREIGN KEY (patient_id)
        REFERENCES patients(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_lab_reports_doctor_id FOREIGN KEY (doctor_id)
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

-- Speed up schedule lookups for appointments
CREATE INDEX idx_appointments_date_time ON appointments(appointment_date, appointment_time);
CREATE INDEX idx_appointments_patient ON appointments(patient_id);
CREATE INDEX idx_appointments_doctor ON appointments(doctor_id);

-- Speed up medical record & consultation access
CREATE INDEX idx_records_patient_date ON medical_records(patient_id, visit_date);
CREATE INDEX idx_consultations_patient ON consultations(patient_id);
CREATE INDEX idx_prescriptions_patient ON prescriptions(patient_id);
CREATE INDEX idx_lab_reports_patient ON lab_reports(patient_id);

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

-- 3. Seed Users
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

-- 6. Seed Patients (Rahul Kumar matching Slide 6)
INSERT INTO patients (id, first_name, last_name, age, gender, blood_group, phone_number, email, address, medical_history, registered_on) VALUES
(4, 'Rahul', 'Kumar', 28, 'Male', 'O+', '9876543210', 'patient@ipcms.com', '123, Green Street, Chennai - 600001', 'No known allergies', '2024-01-10');

-- 7. Seed EHR Details (Matching Slide 6 Mockup)
INSERT INTO ehr_details (id, patient_id, height, weight, bmi, smoking_status, alcohol_status, chronic_diseases, remarks) VALUES
(1, 4, 175, 72, 23.5, 'No', 'Occasional', 'No', 'Patient is healthy.');

-- 8. Seed Allergies
INSERT INTO allergies (id, patient_id, allergen, reaction, added_on) VALUES
(1, 4, 'Penicillin', 'Rash', '2024-01-10');

-- 9. Seed Current Medications
INSERT INTO patient_medications (id, patient_id, medicine, dosage, frequency, start_date) VALUES
(1, 4, 'Paracetamol', '500 mg', 'Twice a day', '2024-05-15'),
(2, 4, 'Vitamin D3', '60,000 IU', 'Once a week', '2024-05-15');

-- 10. Seed Consultations
INSERT INTO consultations (id, patient_id, doctor_id, consultation_date, symptoms, diagnosis, treatment_notes) VALUES
(1, 4, 2, '2024-05-20', 'Fever, Cough, Headache and Body Pain', 'Viral Fever', 'Paracetamol 500 mg - Twice a day. Drink plenty of water and take rest.'),
(2, 4, 2, '2024-02-10', 'Acidity and stomach fullness', 'Acidity', 'Avoid spicy food, take antacids after meals.'),
(3, 4, 2, '2023-12-05', 'High temperature and chills', 'Fever', 'Recovered after medication.');

-- 11. Seed Prescriptions & Items
INSERT INTO prescriptions (id, patient_id, doctor_id, consultation_id, prescription_date, special_instructions) VALUES
(1, 4, 2, 1, '2024-05-20', 'Drink plenty of water and take rest.');

INSERT INTO prescription_items (id, prescription_id, medicine_name, dosage, frequency, duration) VALUES
(1, 1, 'Paracetamol 500 mg', '500 mg', 'Twice a Day', '5 Days'),
(2, 1, 'Cetirizine 10 mg', '10 mg', 'Once a Day', '3 Days');

-- 12. Seed Lab Reports
INSERT INTO lab_reports (id, patient_id, doctor_id, test_name, test_date, result, remarks) VALUES
(1, 4, 2, 'Complete Blood Count', '2024-05-18', 'Normal', 'All parameters within standard limits'),
(2, 4, 2, 'Blood Sugar (Fasting)', '2024-05-18', 'Normal', 'Fasting blood sugar 92 mg/dL'),
(3, 4, 2, 'Lipid Profile', '2024-05-18', 'Borderline', 'Triglycerides slightly elevated');

