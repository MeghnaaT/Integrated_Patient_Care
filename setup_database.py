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
    print("Seeding database...")
    
    # 1. Seed Roles
    admin_role = Role.query.filter_by(name='Admin').first()
    if not admin_role:
        roles = [
            Role(name='Admin', description='Overall system administration and configuration rights'),
            Role(name='Doctor', description='Clinical consulting, prescription writing, and EHR logging'),
            Role(name='Nurse', description='Vitals collection, calendar management, and patient coordination'),
            Role(name='Patient', description='Appointment booking and personal EHR viewing rights')
        ]
        db.session.bulk_save_objects(roles)
        db.session.commit()
        print("-> Roles seeded.")
    else:
        print("-> Roles already exist.")

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
        
        db.session.add_all([user_admin, user_doctor, user_nurse, user_patient])
        db.session.commit()
        print("-> Users credentials accounts seeded.")
    else:
        print("-> Users already exist.")
        # Ensure default test accounts remain active for test runs
        for username in ['admin_user', 'doctor_user', 'nurse_user', 'patient_user']:
            u = User.query.filter_by(username=username).first()
            if u:
                u.is_active = True
        db.session.commit()

    # Re-fetch users to get IDs
    user_doctor_id = User.query.filter_by(username='doctor_user').first().id
    user_nurse_id = User.query.filter_by(username='nurse_user').first().id
    user_patient_id = User.query.filter_by(username='patient_user').first().id

    # 4. Seed Doctor Demographics
    doc = db.session.get(Doctor, user_doctor_id)
    if not doc:
        doctor_record = Doctor(
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
        db.session.add(doctor_record)
        db.session.commit()
        print("-> Doctor demographics profiles seeded.")
    else:
        print("-> Doctor profiles already exist.")

    # 5. Seed Nurse Demographics
    nurse = db.session.get(Nurse, user_nurse_id)
    if not nurse:
        nurse_record = Nurse(
            id=user_nurse_id,
            first_name='Sarah',
            last_name='Connor',
            department_id=dept_genmed,
            contact_number='9876543212'
        )
        db.session.add(nurse_record)
        db.session.commit()
        print("-> Nurse demographics profiles seeded.")
    else:
        print("-> Nurse profiles already exist.")

    # 6. Seed Patient Demographics (Rahul Kumar matching Slide 6)
    pat = db.session.get(Patient, user_patient_id)
    if not pat:
        patient_record = Patient(
            id=user_patient_id,
            first_name='Rahul',
            last_name='Kumar',
            age=28,
            gender='Male',
            blood_group='O+',
            phone_number='9876543210',
            email='patient@ipcms.com',
            address='123, Green Street, Chennai - 600001',
            medical_history='No known allergies',
            registered_on=datetime.date(2024, 1, 10)
        )
        db.session.add(patient_record)
        db.session.commit()
        print("-> Patient demographics profiles seeded.")
    else:
        # Update existing patient to Rahul Kumar for consistency with mockups
        pat.first_name = 'Rahul'
        pat.last_name = 'Kumar'
        pat.age = 28
        pat.blood_group = 'O+'
        pat.address = '123, Green Street, Chennai - 600001'
        pat.registered_on = datetime.date(2024, 1, 10)
        db.session.commit()
        print("-> Patient profile updated to match EHR mockup.")

    # 7. Seed EHR Details (Vitals matching Slide 6)
    ehr = EHRDetail.query.filter_by(patient_id=user_patient_id).first()
    if not ehr:
        ehr_obj = EHRDetail(
            patient_id=user_patient_id,
            height=175,
            weight=72,
            bmi=23.5,
            smoking_status='No',
            alcohol_status='Occasional',
            chronic_diseases='No',
            remarks='Patient is healthy.'
        )
        db.session.add(ehr_obj)
        db.session.commit()
        print("-> EHR Details (vitals) seeded.")

    # 8. Seed Allergies
    allergy = Allergy.query.filter_by(patient_id=user_patient_id).first()
    if not allergy:
        all_obj = Allergy(
            patient_id=user_patient_id,
            allergen='Penicillin',
            reaction='Rash',
            added_on=datetime.date(2024, 1, 10)
        )
        db.session.add(all_obj)
        db.session.commit()
        print("-> Allergy record seeded.")

    # 9. Seed Active Medications
    med = PatientMedication.query.filter_by(patient_id=user_patient_id).first()
    if not med:
        m1 = PatientMedication(patient_id=user_patient_id, medicine='Paracetamol', dosage='500 mg', frequency='Twice a day', start_date=datetime.date(2024, 5, 15))
        m2 = PatientMedication(patient_id=user_patient_id, medicine='Vitamin D3', dosage='60,000 IU', frequency='Once a week', start_date=datetime.date(2024, 5, 15))
        db.session.add_all([m1, m2])
        db.session.commit()
        print("-> Active medications seeded.")

    # 10. Seed Consultations
    consult = Consultation.query.filter_by(patient_id=user_patient_id).first()
    if not consult:
        c1 = Consultation(patient_id=user_patient_id, doctor_id=user_doctor_id, consultation_date=datetime.date(2024, 5, 20), symptoms='Fever, Cough, Headache and Body Pain', diagnosis='Viral Fever', treatment_notes='Paracetamol 500 mg - Twice a day. Drink plenty of water and take rest.')
        c2 = Consultation(patient_id=user_patient_id, doctor_id=user_doctor_id, consultation_date=datetime.date(2024, 2, 10), symptoms='Acidity and stomach fullness', diagnosis='Acidity', treatment_notes='Avoid spicy food, take antacids after meals.')
        c3 = Consultation(patient_id=user_patient_id, doctor_id=user_doctor_id, consultation_date=datetime.date(2023, 12, 5), symptoms='High temperature and chills', diagnosis='Fever', treatment_notes='Recovered after medication.')
        db.session.add_all([c1, c2, c3])
        db.session.commit()
        print("-> Consultations seeded.")

    # 11. Seed Prescriptions & Prescription Items
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
