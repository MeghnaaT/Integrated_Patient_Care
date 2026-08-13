import os
import datetime
from flask import Flask
from werkzeug.security import generate_password_hash
import pymysql

# Custom parser to load .env without external dependencies (python-dotenv)
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    os.environ[key.strip()] = val.strip()

# Load env configurations
load_env()

# Retrieve database connection settings
db_user = os.getenv('DB_USER', 'root')
db_pass = os.getenv('DB_PASSWORD', '')
db_host = os.getenv('DB_HOST', 'localhost')
db_port = os.getenv('DB_PORT', '3306')
db_name = os.getenv('DB_NAME', 'hospital_db')
secret_key = os.getenv('SECRET_KEY', 'super_secret_key')

# Construct database connection string (using pymysql driver)
database_uri = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

# Setup minimal Flask app for database context
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = secret_key

# Import connection db instance and models
from database.connection import db
db.init_app(app)

from models import (
    User, Role, Patient, Doctor, Nurse, Department, Appointment, MedicalRecord,
    EHRDetail, Allergy, PatientMedication, Consultation, Prescription, PrescriptionItem, LabReport
)

def create_database_if_not_exists():
    """Establish a direct connection to MySQL server and ensure the target database exists."""
    print(f"Ensuring database '{db_name}' exists on MySQL server at {db_host}:{db_port}...")
    try:
        # Connect without specifying database name first
        conn = pymysql.connect(
            host=db_host,
            port=int(db_port),
            user=db_user,
            password=db_pass
        )
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        conn.commit()
        conn.close()
        print(f"-> Database '{db_name}' is verified/created successfully.")
    except Exception as e:
        print(f"-> Warning (Pre-database creation check): {e}")
        print("-> Will attempt to proceed with SQLAlchemy connection directly.")

def explain_relationships():
    explanation = """
================================================================================
                    DATABASE RELATIONSHIPS EXPLANATION (MILESTONE 2)
================================================================================
1. Role <-> User (One-to-Many):
   - A single Role (e.g. 'Doctor', 'Patient') can be assigned to multiple Users.

2. User <-> Patient / Doctor / Nurse (One-to-One / Shared Primary Keys):
   - Each medical staff or patient profile is linked to exactly one User credential account.

3. Patient <-> EHRDetail (One-to-One):
   - Stores vitals (height, weight, BMI), lifestyle habits, chronic diseases, and remarks.

4. Patient <-> Allergies & Active Medications (One-to-Many):
   - Tracks allergen warnings and active prescription regimes for clinical safety.

5. Patient & Doctor <-> Consultation (Many-to-One):
   - Binds doctor examination notes, symptoms, diagnosis, and treatment plan.

6. Consultation <-> Prescription <-> PrescriptionItems (One-to-One / One-to-Many):
   - Prescriptions link doctor recommendations to structured medication lists (dosage, frequency, duration).

7. Patient & Doctor <-> LabReport (Many-to-One):
   - Tracks requested/completed diagnostic test results (e.g. CBC, Blood Sugar, Lipid Profile).
================================================================================
"""
    print(explanation)

def seed_data():
    # Ensure alter table columns exist for existing tables
    from sqlalchemy import text
    try:
        db.session.execute(text("ALTER TABLE patients ADD COLUMN aadhaar_number VARCHAR(12) NULL UNIQUE;"))
        db.session.commit()
    except Exception:
        db.session.rollback()

    print("Seeding database...")
    
    # 1. Seed Roles
    role_admin_obj = Role.query.filter_by(name='Admin').first()
    if not role_admin_obj:
        roles = [
            Role(name='Admin', description='Overall system administration and configuration rights'),
            Role(name='Doctor', description='Clinical consulting, prescription writing, and EHR logging'),
            Role(name='Nurse', description='Vitals collection, calendar management, and patient coordination'),
            Role(name='Patient', description='Appointment booking and personal EHR viewing rights'),
            Role(name='Pharmacist', description='Pharmacy inventory, stock update, and medicine dispensing'),
            Role(name='Laboratory Staff', description='Laboratory test processing and test result entry'),
            Role(name='Receptionist', description='Front-desk patient registration and appointment scheduling')
        ]
        db.session.bulk_save_objects(roles)
        db.session.commit()
        print("-> Roles seeded.")
    else:
        # Check if new roles need to be added
        for r_name, r_desc in [
            ('Pharmacist', 'Pharmacy inventory, stock update, and medicine dispensing'),
            ('Laboratory Staff', 'Laboratory test processing and test result entry'),
            ('Receptionist', 'Front-desk patient registration and appointment scheduling')
        ]:
            if not Role.query.filter_by(name=r_name).first():
                db.session.add(Role(name=r_name, description=r_desc))
        db.session.commit()
        print("-> Roles updated.")

    # 2. Seed Departments
    cardio_dept = Department.query.filter_by(name='Cardiology').first()
    if not cardio_dept:
        depts = [
            Department(name='Cardiology', description='Heart, blood vessels, and circulatory system disorders'),
            Department(name='Neurology', description='Brain, spinal cord, and nervous system disorders'),
            Department(name='Orthopedics', description='Musculoskeletal system, bone fractures, and joint surgeries'),
            Department(name='Pediatrics', description='Infant, child, and adolescent medical care'),
            Department(name='General Medicine', description='Common illnesses, health screenings, and primary medical support')
        ]
        db.session.bulk_save_objects(depts)
        db.session.commit()
        print("-> Departments seeded.")
    else:
        print("-> Departments already exist.")

    # Fetch IDs for linking
    role_admin = Role.query.filter_by(name='Admin').first().id
    role_doctor = Role.query.filter_by(name='Doctor').first().id
    role_nurse = Role.query.filter_by(name='Nurse').first().id
    role_patient = Role.query.filter_by(name='Patient').first().id
    role_pharm = Role.query.filter_by(name='Pharmacist').first().id

    dept_cardio = Department.query.filter_by(name='Cardiology').first().id
    dept_genmed = Department.query.filter_by(name='General Medicine').first().id

    # 3. Seed Users
    u_admin = User.query.filter_by(username='admin_user').first()
    if not u_admin:
        user_admin = User(
            username='admin_user',
            email='admin@ipcms.com',
            password_hash=generate_password_hash('admin123', method='scrypt'),
            role_id=role_admin
        )
        user_doctor = User(
            username='doctor_user',
            email='doctor@ipcms.com',
            password_hash=generate_password_hash('doctor123', method='scrypt'),
            role_id=role_doctor
        )
        user_nurse = User(
            username='nurse_user',
            email='nurse@ipcms.com',
            password_hash=generate_password_hash('nurse123', method='scrypt'),
            role_id=role_nurse
        )
        user_patient = User(
            username='patient_user',
            email='patient@ipcms.com',
            password_hash=generate_password_hash('patient123', method='scrypt'),
            role_id=role_patient
        )
        user_pharm = User(
            username='pharmacist_user',
            email='pharmacist@ipcms.com',
            password_hash=generate_password_hash('pharm123', method='scrypt'),
            role_id=role_pharm
        )
        db.session.add_all([user_admin, user_doctor, user_nurse, user_patient, user_pharm])
        db.session.commit()
        print("-> Users credentials accounts seeded.")
    else:
        print("-> Users already exist.")
        # Ensure default test accounts remain active for test runs
        for username in ['admin_user', 'doctor_user', 'nurse_user', 'patient_user', 'pharmacist_user']:
            u = User.query.filter_by(username=username).first()
            if u:
                u.is_active = True
        db.session.commit()

    # Re-fetch users to get IDs
    user_doctor_id = User.query.filter_by(username='doctor_user').first().id
    user_nurse_id = User.query.filter_by(username='nurse_user').first().id
    user_patient_id = User.query.filter_by(username='patient_user').first().id

    # 4. Seed Doctor Profiles
    doc = Doctor.query.filter_by(id=user_doctor_id).first()
    if not doc:
        doctor_profile = Doctor(
            id=user_doctor_id,
            first_name='John',
            last_name='Smith',
            specialization='Cardiologist',
            qualification='MD, FACC',
            department_id=dept_cardio,
            contact_number='9876543210',
            email_address='doctor@ipcms.com',
            available_time='10:00 AM - 01:00 PM'
        )
        db.session.add(doctor_profile)
        db.session.commit()
        print("-> Doctor profile seeded.")
    else:
        print("-> Doctor profile already exists.")

    # 5. Seed Nurse Profiles
    nurse = Nurse.query.filter_by(id=user_nurse_id).first()
    if not nurse:
        nurse_profile = Nurse(
            id=user_nurse_id,
            first_name='Sarah',
            last_name='Connor',
            department_id=dept_genmed,
            contact_number='9876543212'
        )
        db.session.add(nurse_profile)
        db.session.commit()
        print("-> Nurse profile seeded.")
    else:
        print("-> Nurse profile already exists.")

    # 6. Seed Patient Profile (Rahul Kumar matching Slide 6 & 16)
    pat = Patient.query.filter_by(id=user_patient_id).first()
    if not pat:
        patient_profile = Patient(
            id=user_patient_id,
            first_name='Rahul',
            last_name='Kumar',
            age=28,
            gender='Male',
            blood_group='O+',
            phone_number='9876543210',
            email='patient@ipcms.com',
            aadhaar_number='123456789012',
            address='123, Green Street, Chennai - 600001',
            medical_history='No known allergies',
            registered_on=datetime.date(2024, 1, 10)
        )
        db.session.add(patient_profile)
        db.session.commit()
        print("-> Patient profile seeded.")
    else:
        pat.first_name = 'Rahul'
        pat.last_name = 'Kumar'
        pat.age = 28
        pat.gender = 'Male'
        pat.blood_group = 'O+'
        pat.phone_number = '9876543210'
        pat.aadhaar_number = '123456789012'
        pat.address = '123, Green Street, Chennai - 600001'
        db.session.commit()
        print("-> Patient profile updated to match EHR mockup.")

    # 7. Seed EHR Details
    ehr = EHRDetail.query.filter_by(patient_id=user_patient_id).first()
    if not ehr:
        e1 = EHRDetail(
            patient_id=user_patient_id,
            height=175,
            weight=72,
            bmi=23.5,
            smoking_status='No',
            alcohol_status='Occasional',
            chronic_diseases='No',
            remarks='Patient is healthy.'
        )
        db.session.add(e1)
        db.session.commit()
        print("-> EHR Details seeded.")

    # 8. Seed Allergies
    alg = Allergy.query.filter_by(patient_id=user_patient_id).first()
    if not alg:
        a1 = Allergy(
            patient_id=user_patient_id,
            allergen='Penicillin',
            reaction='Rash',
            added_on=datetime.date(2024, 1, 10)
        )
        db.session.add(a1)
        db.session.commit()
        print("-> Allergy record seeded.")

    # 9. Seed Current Active Medications
    med = PatientMedication.query.filter_by(patient_id=user_patient_id).first()
    if not med:
        m1 = PatientMedication(patient_id=user_patient_id, medicine='Paracetamol', dosage='500 mg', frequency='Twice a day', start_date=datetime.date(2024, 5, 15))
        m2 = PatientMedication(patient_id=user_patient_id, medicine='Vitamin D3', dosage='60,000 IU', frequency='Once a week', start_date=datetime.date(2024, 5, 15))
        db.session.add_all([m1, m2])
        db.session.commit()
        print("-> Active medications seeded.")

    # 10. Seed Consultations
    cons = Consultation.query.filter_by(patient_id=user_patient_id).first()
    if not cons:
        c1 = Consultation(patient_id=user_patient_id, doctor_id=user_doctor_id, consultation_date=datetime.date(2024, 5, 20), symptoms='Fever, Cough, Headache and Body Pain', diagnosis='Viral Fever', treatment_notes='Paracetamol 500 mg - Twice a day. Drink plenty of water and take rest.')
        c2 = Consultation(patient_id=user_patient_id, doctor_id=user_doctor_id, consultation_date=datetime.date(2024, 2, 10), symptoms='Acidity and stomach fullness', diagnosis='Acidity', treatment_notes='Avoid spicy food, take antacids after meals.')
        c3 = Consultation(patient_id=user_patient_id, doctor_id=user_doctor_id, consultation_date=datetime.date(2023, 12, 5), symptoms='High temperature and chills', diagnosis='Fever', treatment_notes='Recovered after medication.')
        db.session.add_all([c1, c2, c3])
        db.session.commit()
        print("-> Consultations seeded.")

    # 11. Seed Prescriptions
    presc = Prescription.query.filter_by(patient_id=user_patient_id).first()
    if not presc:
        p1 = Prescription(patient_id=user_patient_id, doctor_id=user_doctor_id, consultation_id=1, prescription_date=datetime.date(2024, 5, 20), special_instructions='Drink plenty of water and take rest.')
        db.session.add(p1)
        db.session.commit()

        item1 = PrescriptionItem(prescription_id=p1.id, medicine_name='Paracetamol 500 mg', dosage='500 mg', frequency='Twice a Day', duration='5 Days')
        item2 = PrescriptionItem(prescription_id=p1.id, medicine_name='Cetirizine 10 mg', dosage='10 mg', frequency='Once a Day', duration='3 Days')
        db.session.add_all([item1, item2])
        db.session.commit()
        print("-> Prescriptions and items seeded.")

    # 12. Seed Lab Reports
    lab = LabReport.query.filter_by(patient_id=user_patient_id).first()
    if not lab:
        l1 = LabReport(patient_id=user_patient_id, doctor_id=user_doctor_id, test_name='Complete Blood Count', test_date=datetime.date(2024, 5, 18), result='Normal', remarks='All parameters within standard limits')
        l2 = LabReport(patient_id=user_patient_id, doctor_id=user_doctor_id, test_name='Blood Sugar (Fasting)', test_date=datetime.date(2024, 5, 18), result='Normal', remarks='Fasting blood sugar 92 mg/dL')
        l3 = LabReport(patient_id=user_patient_id, doctor_id=user_doctor_id, test_name='Lipid Profile', test_date=datetime.date(2024, 5, 18), result='Borderline', remarks='Triglycerides slightly elevated')
        db.session.add_all([l1, l2, l3])
        db.session.commit()
        print("-> Lab reports seeded.")

    # 13. Seed Medicines (Matching Slide 11 Mockup)
    from models.pharmacy import Medicine, MedicineDispensation
    from models.billing import Bill, BillItem
    from models.notification import Notification
    from models.activity_log import ActivityLog

    med1 = Medicine.query.filter_by(medicine_code='MED101').first()
    if not med1:
        m_list = [
            Medicine(medicine_code='MED101', medicine_name='Paracetamol 500 mg', category='Tablet', manufacturer='ABC Pharma Ltd.', stock=250, unit_price=15.00, expiry_date=datetime.date(2027, 12, 31), status='Available'),
            Medicine(medicine_code='MED102', medicine_name='Amoxicillin 250 mg', category='Capsule', manufacturer='XYZ Pharmaceuticals', stock=120, unit_price=45.00, expiry_date=datetime.date(2027, 8, 15), status='Available'),
            Medicine(medicine_code='MED103', medicine_name='Cough Syrup', category='Syrup', manufacturer='HealthCare Pvt. Ltd.', stock=45, unit_price=80.00, expiry_date=datetime.date(2026, 10, 20), status='Low Stock'),
            Medicine(medicine_code='MED104', medicine_name='Ibuprofen 400 mg', category='Tablet', manufacturer='LifeCare Pharma', stock=300, unit_price=20.00, expiry_date=datetime.date(2028, 5, 10), status='Available'),
            Medicine(medicine_code='MED105', medicine_name='Vitamin C 500 mg', category='Tablet', manufacturer='Wellness Pharma', stock=75, unit_price=30.00, expiry_date=datetime.date(2027, 3, 5), status='Low Stock')
        ]
        db.session.add_all(m_list)
        db.session.commit()
        print("-> Pharmacy inventory seeded.")

    # 14. Seed Bills (Matching Slide 16 Mockup)
    b1 = Bill.query.filter_by(bill_number='BILL1001').first()
    if not b1:
        bill1 = Bill(
            bill_number='BILL1001',
            patient_id=user_patient_id,
            consultation_id=1,
            total_consultation_fee=500.00,
            total_lab_fee=850.00,
            total_pharmacy_fee=450.00,
            other_charges=200.00,
            sub_total=2000.00,
            discount=0.00,
            tax_amount=0.00,
            total_amount=2000.00,
            payment_method='UPI',
            transaction_id='UPI1234567890',
            payment_status='Paid',
            bill_date=datetime.date(2026, 7, 22),
            due_date=datetime.date(2026, 7, 22)
        )
        db.session.add(bill1)
        db.session.commit()

        items = [
            BillItem(bill_id=bill1.id, service_type='Consultation', description='Dr. Priya - General Medicine', reference_id='CONS1001', amount=500.00),
            BillItem(bill_id=bill1.id, service_type='Laboratory', description='Complete Blood Count (CBC)', reference_id='LAB1001', amount=550.00),
            BillItem(bill_id=bill1.id, service_type='Laboratory', description='Lipid Profile', reference_id='LAB1002', amount=300.00),
            BillItem(bill_id=bill1.id, service_type='Pharmacy', description='Paracetamol 500 mg (10 Tablets)', reference_id='PHAR1001', amount=150.00),
            BillItem(bill_id=bill1.id, service_type='Pharmacy', description='Amoxicillin 250 mg (10 Capsules)', reference_id='PHAR1002', amount=300.00),
            BillItem(bill_id=bill1.id, service_type='Other', description='Registration Charges', reference_id='OTH1001', amount=200.00)
        ]
        db.session.add_all(items)
        db.session.commit()

        # Seed additional bill entries for history list
        b2 = Bill(bill_number='BILL1000', patient_id=user_patient_id, sub_total=1250.00, total_amount=1250.00, payment_method='Card', payment_status='Paid', bill_date=datetime.date(2026, 7, 18), due_date=datetime.date(2026, 7, 18))
        b3 = Bill(bill_number='BILL0999', patient_id=user_patient_id, sub_total=750.00, total_amount=750.00, payment_method='Cash', payment_status='Paid', bill_date=datetime.date(2026, 7, 15), due_date=datetime.date(2026, 7, 15))
        b4 = Bill(bill_number='BILL0998', patient_id=user_patient_id, sub_total=1500.00, total_amount=1500.00, payment_method='UPI', payment_status='Unpaid', bill_date=datetime.date(2026, 7, 10), due_date=datetime.date(2026, 7, 25))
        db.session.add_all([b2, b3, b4])
        db.session.commit()
        print("-> Billing and invoices seeded.")

    # 15. Seed Notifications (Matching Slide 26 Mockup)
    n1 = Notification.query.filter_by(notification_code='NOT1001').first()
    if not n1:
        n_list = [
            Notification(notification_code='NOT1001', patient_id=user_patient_id, user_id=user_patient_id, type='Appointment Reminder', message='Your appointment with Dr. Priya is scheduled on 24-07-2026 at 10:00 AM.', delivery_method='In-App', status='Delivered', is_read=True),
            Notification(notification_code='NOT1002', patient_id=user_patient_id, user_id=user_patient_id, type='Lab Report', message='Your Blood Test report is available. Please check.', delivery_method='In-App', status='Delivered', is_read=True),
            Notification(notification_code='NOT1003', patient_id=user_patient_id, user_id=user_patient_id, type='Prescription Ready', message='Your prescription is ready for collection at the pharmacy.', delivery_method='SMS', status='Delivered', is_read=True),
            Notification(notification_code='NOT1004', patient_id=user_patient_id, user_id=user_patient_id, type='Billing Reminder', message='Your payment of 2,000 is pending. Please make the payment.', delivery_method='In-App', status='Delivered', is_read=True),
            Notification(notification_code='NOT1005', patient_id=user_patient_id, user_id=user_patient_id, type='Appointment Reminder', message='Your appointment with Dr. Raj is scheduled on 25-07-2026 at 11:30 AM.', delivery_method='SMS', status='Delivered', is_read=False),
            Notification(notification_code='NOT1006', patient_id=user_patient_id, user_id=user_patient_id, type='Lab Report', message='Your X-Ray report is available. Please check.', delivery_method='In-App', status='Delivered', is_read=False)
        ]
        db.session.add_all(n_list)
        db.session.commit()
        print("-> Notifications seeded.")

    # 16. Seed Activity Logs
    al = ActivityLog.query.first()
    if not al:
        logs = [
            ActivityLog(user_id=user_doctor_id, action='Admin user logged in', ip_address='192.168.1.105'),
            ActivityLog(user_id=user_doctor_id, action='Dr. Priya updated patient record', ip_address='192.168.1.110'),
            ActivityLog(user_id=user_nurse_id, action='Nurse updated vital signs', ip_address='192.168.1.115')
        ]
        db.session.add_all(logs)
        db.session.commit()
        print("-> Activity logs seeded.")


if __name__ == '__main__':
    explain_relationships()
    create_database_if_not_exists()
    with app.app_context():
        try:
            print("Connecting to database and creating tables...")
            db.create_all()
            print("Database tables validated/created successfully.")
            seed_data()
            print("Database setup complete.")
        except Exception as e:
            print(f"\n[ERROR] Setup failed: {e}")
            print("\nPlease make sure that:")
            print(f"1. MySQL server is running at {db_host}:{db_port}")
            print(f"2. Your .env file credentials (DB_USER, DB_PASSWORD) are correct.")
            print("3. Needed python libraries are installed: pip install Flask Flask-SQLAlchemy PyMySQL cryptography")
