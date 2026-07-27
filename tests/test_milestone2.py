# =============================================================================
# tests/test_milestone2.py — Test Suite for Milestone 2 Clinical Management
# =============================================================================

import unittest
import datetime
from app import create_app
from database.connection import db
from models.user import User
from models.patient import Patient
from models.doctor import Doctor
from models.ehr_detail import EHRDetail, Allergy, PatientMedication
from models.consultation import Consultation
from models.prescription import Prescription, PrescriptionItem
from models.lab_report import LabReport
from services.ehr_service import get_or_create_ehr_detail, add_allergy, add_patient_medication
from services.consultation_service import create_consultation, get_consultations_by_patient
from services.prescription_service import create_prescription, get_prescriptions_by_patient
from services.lab_service import create_lab_report, get_lab_reports_by_patient
from services.medical_history_service import get_complete_patient_history
from services.report_search_service import search_patients_by_id_or_name

class Milestone2TestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app('default')
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        db.session.remove()
        self.app_context.pop()

    def test_01_ehr_service(self):
        """Test EHR vitals, allergy, and active medication services."""
        patient = Patient.query.first()
        self.assertIsNotNone(patient, "Patient record should exist.")

        # Test EHR detail
        ehr = get_or_create_ehr_detail(patient.id)
        self.assertIsNotNone(ehr)
        self.assertEqual(ehr.patient_id, patient.id)

        # Test Allergy addition
        allergy = add_allergy(patient.id, "Sulfa Drugs", "Hives", datetime.date.today())
        self.assertEqual(allergy.allergen, "Sulfa Drugs")

        # Test Medication addition
        med = add_patient_medication(patient.id, "Amoxicillin 500mg", "500 mg", "Three times a day", datetime.date.today())
        self.assertEqual(med.medicine, "Amoxicillin 500mg")

    def test_02_consultation_service(self):
        """Test Consultation creation and history retrieval."""
        patient = Patient.query.first()
        doctor = Doctor.query.first()

        consultation = create_consultation(
            patient_id=patient.id,
            doctor_id=doctor.id,
            consultation_date=datetime.date.today(),
            symptoms="Mild fever and sore throat",
            diagnosis="Pharyngitis",
            treatment_notes="Warm fluids and rest."
        )
        self.assertIsNotNone(consultation.id)
        self.assertEqual(consultation.diagnosis, "Pharyngitis")

        consults = get_consultations_by_patient(patient.id)
        self.assertGreaterEqual(len(consults), 1)

    def test_03_prescription_service(self):
        """Test Prescription creation with items."""
        patient = Patient.query.first()
        doctor = Doctor.query.first()

        items_data = [
            {'medicine_name': 'Azithromycin 500mg', 'dosage': '500 mg', 'frequency': 'Once a Day', 'duration': '3 Days'}
        ]
        presc = create_prescription(
            patient_id=patient.id,
            doctor_id=doctor.id,
            prescription_date=datetime.date.today(),
            special_instructions="Take after breakfast.",
            items_data=items_data
        )
        self.assertIsNotNone(presc.id)
        self.assertEqual(len(presc.items), 1)

    def test_04_lab_service(self):
        """Test Lab report creation."""
        patient = Patient.query.first()
        doctor = Doctor.query.first()

        report = create_lab_report(
            patient_id=patient.id,
            doctor_id=doctor.id,
            test_name="Urine Routine",
            test_date=datetime.date.today(),
            result="Normal",
            remarks="No abnormalities detected."
        )
        self.assertIsNotNone(report.id)
        self.assertEqual(report.test_name, "Urine Routine")

    def test_05_medical_history_aggregation(self):
        """Test complete patient medical history compilation."""
        patient = Patient.query.first()
        history = get_complete_patient_history(patient.id)
        self.assertIn('patient', history)
        self.assertIn('ehr', history)
        self.assertIn('allergies', history)
        self.assertIn('consultations', history)

    def test_06_search_patients(self):
        """Test patient search by ID and name."""
        results = search_patients_by_id_or_name("Rahul")
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0].first_name, "Rahul")

if __name__ == '__main__':
    unittest.main()
