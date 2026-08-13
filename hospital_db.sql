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
    aadhaar_number VARCHAR(12) NULL UNIQUE,
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

-- ----------------------------------------------------------------------------
-- 16. Table: medicines (Pharmacy Inventory)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS medicines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    medicine_code VARCHAR(50) NOT NULL UNIQUE,
    medicine_name VARCHAR(150) NOT NULL,
    category VARCHAR(50) NOT NULL,
    manufacturer VARCHAR(100) NOT NULL,
    stock INT NOT NULL DEFAULT 0,
    unit_price DECIMAL(10, 2) NOT NULL,
    expiry_date DATE NOT NULL,
    status ENUM('Available', 'Low Stock', 'Expired') NOT NULL DEFAULT 'Available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 17. Table: medicine_dispensations
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS medicine_dispensations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    prescription_id INT NULL,
    patient_id INT NOT NULL,
    medicine_id INT NOT NULL,
    quantity INT NOT NULL,
    dispensed_by INT NULL,
    dispensed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_dispense_patient_id FOREIGN KEY (patient_id)
        REFERENCES patients(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_dispense_medicine_id FOREIGN KEY (medicine_id)
        REFERENCES medicines(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 18. Table: bills (Billing & Payments)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bill_number VARCHAR(50) NOT NULL UNIQUE,
    patient_id INT NOT NULL,
    consultation_id INT NULL,
    total_consultation_fee DECIMAL(10, 2) DEFAULT 0.00,
    total_lab_fee DECIMAL(10, 2) DEFAULT 0.00,
    total_pharmacy_fee DECIMAL(10, 2) DEFAULT 0.00,
    other_charges DECIMAL(10, 2) DEFAULT 0.00,
    sub_total DECIMAL(10, 2) NOT NULL,
    discount DECIMAL(10, 2) DEFAULT 0.00,
    tax_amount DECIMAL(10, 2) DEFAULT 0.00,
    total_amount DECIMAL(10, 2) NOT NULL,
    payment_method ENUM('UPI', 'Card', 'Cash', 'Insurance') NOT NULL DEFAULT 'UPI',
    transaction_id VARCHAR(100) NULL,
    payment_status ENUM('Paid', 'Unpaid', 'Pending') NOT NULL DEFAULT 'Paid',
    bill_date DATE NOT NULL,
    due_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_bills_patient_id FOREIGN KEY (patient_id)
        REFERENCES patients(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 19. Table: bill_items
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bill_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bill_id INT NOT NULL,
    service_type ENUM('Consultation', 'Laboratory', 'Pharmacy', 'Other') NOT NULL,
    description VARCHAR(255) NOT NULL,
    reference_id VARCHAR(50) NULL,
    amount DECIMAL(10, 2) NOT NULL,

    CONSTRAINT fk_bill_items_bill_id FOREIGN KEY (bill_id)
        REFERENCES bills(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 20. Table: notifications
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    notification_code VARCHAR(50) NOT NULL UNIQUE,
    patient_id INT NULL,
    user_id INT NULL,
    type ENUM('Appointment Reminder', 'Lab Report', 'Prescription Ready', 'Billing Reminder', 'General Info') NOT NULL,
    message TEXT NOT NULL,
    date_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivery_method ENUM('In-App', 'SMS', 'Email') NOT NULL DEFAULT 'In-App',
    status ENUM('Delivered', 'Failed', 'Read') NOT NULL DEFAULT 'Delivered',
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_notifications_patient_id FOREIGN KEY (patient_id)
        REFERENCES patients(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 21. Table: activity_logs (Security Audit Logs)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS activity_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    action VARCHAR(255) NOT NULL,
    ip_address VARCHAR(50) NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- INDEXES FOR QUERY OPTIMIZATION
-- ============================================================================

-- Speed up search on patient demographics
CREATE INDEX idx_patients_last_name ON patients(last_name);
CREATE INDEX idx_patients_phone ON patients(phone_number);
CREATE INDEX idx_patients_aadhaar ON patients(aadhaar_number);

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
CREATE INDEX idx_medicines_status ON medicines(status);
CREATE INDEX idx_bills_patient ON bills(patient_id);
CREATE INDEX idx_notifications_patient ON notifications(patient_id);

-- ============================================================================
-- INITIAL SAMPLE DATA INSERTION (SEED DATA)
-- ============================================================================

-- 1. Seed Roles
INSERT INTO roles (id, name, description) VALUES
(1, 'Admin', 'Overall system administration and configuration rights'),
(2, 'Doctor', 'Clinical consulting, prescription writing, and EHR logging'),
(3, 'Nurse', 'Vitals collection, calendar management, and patient coordination'),
(4, 'Patient', 'Appointment booking and personal EHR viewing rights'),
(5, 'Pharmacist', 'Pharmacy inventory, stock update, and medicine dispensing'),
(6, 'Laboratory Staff', 'Laboratory test processing and test result entry'),
(7, 'Receptionist', 'Front-desk patient registration and appointment scheduling');

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
(4, 'patient_user', 'patient@ipcms.com', 'scrypt:32768:8:1$rX7uK9z8qE3tQkL2$d397a539b5b2e59df9547d2f9547cb029a8a65f9bf72382103f6fdf6708b7672bc19ca7892b1a82ef2f05c3d2568e61fb19c961e6ca3a07865e90df3a1b1867c', 4, TRUE),
(5, 'pharmacist_user', 'pharmacist@ipcms.com', 'scrypt:32768:8:1$uPlxR2p7zE2cQkK8$b671a539b5b2e59df9547d2f9547cb029a8a65f9bf72382103f6fdf6708b7672bc19ca7892b1a82ef2f05c3d2568e61fb19c961e6ca3a07865e90df3a1b1836c', 5, TRUE);

-- 4. Seed Doctors
INSERT INTO doctors (id, first_name, last_name, specialization, qualification, department_id, contact_number, email_address, available_time) VALUES
(2, 'John', 'Smith', 'Cardiologist', 'MD, FACC', 1, '9876543210', 'doctor@ipcms.com', '10:00 AM - 01:00 PM');

-- 5. Seed Nurses
INSERT INTO nurses (id, first_name, last_name, department_id, contact_number) VALUES
(3, 'Sarah', 'Connor', 5, '9876543212');

-- 6. Seed Patients (Rahul Kumar matching Slide 6 & 16)
INSERT INTO patients (id, first_name, last_name, age, gender, blood_group, phone_number, email, aadhaar_number, address, medical_history, registered_on) VALUES
(4, 'Rahul', 'Kumar', 28, 'Male', 'O+', '9876543210', 'patient@ipcms.com', '123456789012', '123, Green Street, Chennai - 600001', 'No known allergies', '2024-01-10');

-- 7. Seed EHR Details
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

-- 13. Seed Medicines (Matching Slide 11 Mockup)
INSERT INTO medicines (id, medicine_code, medicine_name, category, manufacturer, stock, unit_price, expiry_date, status) VALUES
(1, 'MED101', 'Paracetamol 500 mg', 'Tablet', 'ABC Pharma Ltd.', 250, 15.00, '2027-12-31', 'Available'),
(2, 'MED102', 'Amoxicillin 250 mg', 'Capsule', 'XYZ Pharmaceuticals', 120, 45.00, '2027-08-15', 'Available'),
(3, 'MED103', 'Cough Syrup', 'Syrup', 'HealthCare Pvt. Ltd.', 45, 80.00, '2026-10-20', 'Low Stock'),
(4, 'MED104', 'Ibuprofen 400 mg', 'Tablet', 'LifeCare Pharma', 300, 20.00, '2028-05-10', 'Available'),
(5, 'MED105', 'Vitamin C 500 mg', 'Tablet', 'Wellness Pharma', 75, 30.00, '2027-03-05', 'Low Stock');

-- 14. Seed Bills (Matching Slide 16 Mockup)
INSERT INTO bills (id, bill_number, patient_id, consultation_id, total_consultation_fee, total_lab_fee, total_pharmacy_fee, other_charges, sub_total, discount, tax_amount, total_amount, payment_method, transaction_id, payment_status, bill_date, due_date) VALUES
(1, 'BILL1001', 4, 1, 500.00, 850.00, 450.00, 200.00, 2000.00, 0.00, 0.00, 2000.00, 'UPI', 'UPI1234567890', 'Paid', '2026-07-22', '2026-07-22');

INSERT INTO bill_items (id, bill_id, service_type, description, reference_id, amount) VALUES
(1, 1, 'Consultation', 'Dr. Priya - General Medicine', 'CONS1001', 500.00),
(2, 1, 'Laboratory', 'Complete Blood Count (CBC)', 'LAB1001', 550.00),
(3, 1, 'Laboratory', 'Lipid Profile', 'LAB1002', 300.00),
(4, 1, 'Pharmacy', 'Paracetamol 500 mg (10 Tablets)', 'PHAR1001', 150.00),
(5, 1, 'Pharmacy', 'Amoxicillin 250 mg (10 Capsules)', 'PHAR1002', 300.00),
(6, 1, 'Other', 'Registration Charges', 'OTH1001', 200.00);

-- 15. Seed Notifications (Matching Slide 26 Mockup)
INSERT INTO notifications (id, notification_code, patient_id, user_id, type, message, date_time, delivery_method, status, is_read) VALUES
(1, 'NOT1001', 4, 4, 'Appointment Reminder', 'Your appointment with Dr. Priya is scheduled on 24-07-2026 at 10:00 AM.', '2026-07-23 09:30:00', 'In-App', 'Delivered', TRUE),
(2, 'NOT1002', 4, 4, 'Lab Report', 'Your Blood Test report is available. Please check.', '2026-07-23 08:45:00', 'In-App', 'Delivered', TRUE),
(3, 'NOT1003', 4, 4, 'Prescription Ready', 'Your prescription is ready for collection at the pharmacy.', '2026-07-22 18:15:00', 'SMS', 'Delivered', TRUE),
(4, 'NOT1004', 4, 4, 'Billing Reminder', 'Your payment of 2,000 is pending. Please make the payment.', '2026-07-22 17:00:00', 'In-App', 'Delivered', TRUE);

-- 16. Seed Activity Logs
INSERT INTO activity_logs (id, user_id, action, ip_address) VALUES
(1, 1, 'Admin user logged in', '192.168.1.105'),
(2, 2, 'Dr. Priya updated patient record', '192.168.1.110'),
(3, 5, 'Pharmacist dispensed prescription PRS1005', '192.168.1.120');


