from database.connection import db
from models.role import Role
from models.user import User
from models.department import Department
from models.patient import Patient
from models.doctor import Doctor
from models.nurse import Nurse
from models.appointment import Appointment
from models.medical_record import MedicalRecord
from models.ehr_detail import EHRDetail, Allergy, PatientMedication
from models.consultation import Consultation
from models.prescription import Prescription, PrescriptionItem
from models.lab_report import LabReport

# Expose all models for migrations and dynamic loading
__all__ = [
    'db',
    'Role',
    'User',
    'Department',
    'Patient',
    'Doctor',
    'Nurse',
    'Appointment',
    'MedicalRecord',
    'EHRDetail',
    'Allergy',
    'PatientMedication',
    'Consultation',
    'Prescription',
    'PrescriptionItem',
    'LabReport'
]
