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

from models import User, Role, Patient, Doctor, Nurse, Department, Appointment, MedicalRecord

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
                    DATABASE RELATIONSHIPS EXPLANATION
================================================================================
1. Role <-> User (One-to-Many):
   - A single Role (e.g. 'Doctor', 'Patient') can be assigned to multiple Users.
   - mapped via users.role_id FK pointing to roles.id.
   - ON DELETE RESTRICT prevents deleting a role if active users still hold it.

2. User <-> Patient / Doctor / Nurse (One-to-One / Shared Primary Keys):
   - Each medical staff or patient profile is linked to exactly one User credential account.
   - patients.id, doctors.id, and nurses.id act as both Primary Keys and Foreign Keys 
     referencing users.id.
   - ON DELETE CASCADE propagates user deletions to the demographics profiles.

3. Department <-> Doctor / Nurse (One-to-Many):
   - Multiple doctors and nurses belong to a single department (e.g. 'Cardiology').
   - department_id FK in doctors and nurses tables references departments.id.
   - ON DELETE RESTRICT protects department structure deletions if personnel exist.

4. Patient & Doctor <-> Appointment (Many-to-One):
   - An appointment serves as an associative entity. A patient has many appointments,
     and a doctor has many appointments.
   - appointments.patient_id FK references patients.id.
   - appointments.doctor_id FK references doctors.id.
   - ON DELETE CASCADE clears bookings if either profile is removed.

5. Patient & Doctor <-> MedicalRecord (Many-to-One):
   - Similar to appointments, a medical record (EHR) binds a patient to the consulting
     doctor who recorded the diagnosis.
   - medical_records.patient_id FK references patients.id.
   - medical_records.doctor_id FK references doctors.id.
   - ON DELETE CASCADE removes EHR notes if profiles are deleted.
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
        # Creating passwords using Werkzeug's default password hashing (scrypt method)
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

    # 6. Seed Patient Demographics
    pat = db.session.get(Patient, user_patient_id)
    if not pat:
        patient_record = Patient(
            id=user_patient_id,
            first_name='Ravi',
            last_name='Kumar',
            age=32,
            gender='Male',
            blood_group='O+',
            phone_number='9876543210',
            email='patient@ipcms.com',
            address='123, MG Road, Bangalore, Karnataka',
            medical_history='No known allergies',
            registered_on=datetime.date(2024, 5, 10)
        )
        db.session.add(patient_record)
        db.session.commit()
        print("-> Patient demographics profiles seeded.")
    else:
        print("-> Patient profiles already exist.")

    # 7. Seed Appointments
    appt = Appointment.query.filter_by(patient_id=user_patient_id, doctor_id=user_doctor_id).first()
    if not appt:
        appointment_record = Appointment(
            patient_id=user_patient_id,
            doctor_id=user_doctor_id,
            appointment_date=datetime.date(2026, 7, 15),
            appointment_time=datetime.time(10, 30, 0),
            status='Confirmed'
        )
        db.session.add(appointment_record)
        db.session.commit()
        print("-> Appointments seeded.")
    else:
        print("-> Appointments already exist.")

    # 8. Seed Medical Records
    rec = MedicalRecord.query.filter_by(patient_id=user_patient_id, doctor_id=user_doctor_id).first()
    if not rec:
        medical_record = MedicalRecord(
            patient_id=user_patient_id,
            doctor_id=user_doctor_id,
            visit_date=datetime.date(2026, 7, 1),
            symptoms='Mild chest discomfort and fatigue',
            diagnosis='Normal sinus rhythm, fatigue due to workload stress',
            treatment_plan='Rest, low-sodium diet, check back if symptoms persist'
        )
        db.session.add(medical_record)
        db.session.commit()
        print("-> Medical records (EHR) seeded.")
    else:
        print("-> Medical records already exist.")

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
