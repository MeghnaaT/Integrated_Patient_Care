# =============================================================================
# tests/test_patient_portal.py — Step 4 Patient Self-Service Portal Test Suite
# =============================================================================

import unittest
import os
import sys
import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from database.connection import db
from models.user import User
from models.patient import Patient
from models.doctor import Doctor
from models.appointment import Appointment
from models.medical_record import MedicalRecord
from models.prescription import Prescription, PrescriptionItem
from models.lab_report import LabReport
from models.billing import Bill
from models.feedback import Feedback

class PatientPortalTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app('default')
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        # Clean up test data from previous runs to ensure test isolation
        self._cleanup_test_data()

    def _cleanup_test_data(self):
        """Remove test-generated records that may persist across test runs."""
        from models.billing import Bill
        from models.lab_report import LabReport
        # Remove test appointments created by patient tests
        Appointment.query.filter_by(patient_id=4, doctor_id=2).filter(
            Appointment.status.in_(['Pending', 'Confirmed'])
        ).delete(synchronize_session=False)
        # Remove test bill if it exists
        Bill.query.filter_by(bill_number='INV9999').delete(synchronize_session=False)
        db.session.commit()

    def tearDown(self):
        db.session.rollback()
        self.app_context.pop()

    def login_as_patient(self):
        self.client.post('/auth/login', data={'email': 'patient@ipcms.com', 'password': 'patient123'})

    def login_as_admin(self):
        self.client.post('/auth/login', data={'email': 'admin@ipcms.com', 'password': 'admin123'})

    def test_01_patient_dashboard_loads(self):
        """1. Patient dashboard loads with patient statistics."""
        self.login_as_patient()
        res = self.client.get('/patient/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'My Dashboard', res.data)
        self.assertIn(b'Appointments', res.data)

    def test_02_patient_doctors_directory_works(self):
        """2. Patient can access Doctors Directory."""
        self.login_as_patient()
        res = self.client.get('/doctor/list')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Doctor Directory', res.data)

    def test_03_patient_can_search_doctors(self):
        """3. Patient can search doctors by name."""
        self.login_as_patient()
        res = self.client.get('/doctor/list?q=Smith')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'John Smith', res.data)

    def test_04_patient_can_view_doctor_details(self):
        """4. Patient can view doctor profile/details."""
        self.login_as_patient()
        res = self.client.get('/doctor/view/2')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Dr. John Smith', res.data)

    def test_05_patient_can_book_valid_appointment(self):
        """5. Patient can book a valid appointment for themselves."""
        self.login_as_patient()
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        res = self.client.post('/appointment/book', data={
            'patient_id': 4,
            'doctor_id': 2,
            'appointment_date': tomorrow.strftime('%Y-%m-%d'),
            'appointment_time': '10:00'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Appointment scheduled successfully!', res.data)

    def test_06_invalid_appointment_time_rejected(self):
        """6. Booking an appointment outside doctor hours is rejected."""
        self.login_as_patient()
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        res = self.client.post('/appointment/book', data={
            'patient_id': 4,
            'doctor_id': 2,
            'appointment_date': tomorrow.strftime('%Y-%m-%d'),
            'appointment_time': '07:00',  # Doctor available 10:00 AM - 01:00 PM
        }, follow_redirects=True)
        # Actual message: "Selected time falls outside of Dr. Smith's available hours"
        self.assertIn(b'outside', res.data)

    def test_07_conflicting_appointment_rejected(self):
        """7. Booking an appointment slot that is already booked is rejected."""
        self.login_as_patient()
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        # First booking
        self.client.post('/appointment/book', data={
            'patient_id': 4,
            'doctor_id': 2,
            'appointment_date': tomorrow.strftime('%Y-%m-%d'),
            'appointment_time': '11:00'
        })
        # Duplicate booking
        res = self.client.post('/appointment/book', data={
            'patient_id': 4,
            'doctor_id': 2,
            'appointment_date': tomorrow.strftime('%Y-%m-%d'),
            'appointment_time': '11:00'
        }, follow_redirects=True)
        # Actual message: "This doctor is already scheduled for another consultation at this exact date and time."
        self.assertIn(b'already scheduled', res.data)

    def test_08_patient_can_view_own_appointments(self):
        """8. Patient can view dedicated My Appointments page."""
        self.login_as_patient()
        res = self.client.get('/appointment/my-appointments')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'My Appointments', res.data)

    def test_09_patient_can_cancel_own_appointment(self):
        """9. Patient can cancel their own scheduled appointment."""
        self.login_as_patient()
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        appt = Appointment(
            patient_id=4,
            doctor_id=2,
            appointment_date=tomorrow,
            appointment_time=datetime.time(14, 0),
            status='Confirmed'
        )
        db.session.add(appt)
        db.session.commit()

        res = self.client.post(f'/appointment/cancel/{appt.id}', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'cancelled successfully', res.data)

    def test_10_patient_can_view_own_ehr(self):
        """10. Patient can view their own EHR."""
        self.login_as_patient()
        res = self.client.get('/ehr/4')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'EHR - Rahul Kumar', res.data)

    def test_11_patient_cannot_view_another_patient_ehr(self):
        """11. Patient cannot view another patient's EHR (HTTP 403)."""
        self.login_as_patient()
        res = self.client.get('/ehr/5')
        self.assertEqual(res.status_code, 403)

    def test_12_patient_can_view_own_prescriptions(self):
        """12. Patient can view their own prescriptions list."""
        self.login_as_patient()
        res = self.client.get('/prescriptions/list')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Prescriptions Management', res.data)

    def test_13_patient_cannot_view_another_patient_prescription(self):
        """13. Patient cannot view another patient's prescription (HTTP 403)."""
        # Create prescription for patient ID 5
        p = Prescription(
            patient_id=5,
            doctor_id=2,
            prescription_date=datetime.date.today(),
            special_instructions='Take after meals'
        )
        db.session.add(p)
        db.session.commit()

        self.login_as_patient() # Logged in as Patient 4
        res = self.client.get(f'/prescriptions/view/{p.id}')
        self.assertEqual(res.status_code, 403)

    def test_14_patient_can_view_own_lab_reports(self):
        """14. Patient can view their own lab reports."""
        self.login_as_patient()
        res = self.client.get('/laboratory/reports')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Laboratory Management', res.data)

    def test_15_patient_cannot_view_another_patient_lab_report(self):
        """15. Patient cannot view another patient's lab report (HTTP 403)."""
        lr = LabReport(
            patient_id=5,
            doctor_id=2,
            test_name='Complete Blood Count (CBC)',
            test_date=datetime.date.today(),
            result='Hemoglobin: 14.5 g/dL'
        )
        db.session.add(lr)
        db.session.commit()

        self.login_as_patient() # Logged in as Patient 4
        res = self.client.get(f'/laboratory/view/{lr.id}')
        self.assertEqual(res.status_code, 403)

    def test_16_patient_can_view_own_invoices(self):
        """16. Patient can view dedicated My Invoices page."""
        self.login_as_patient()
        res = self.client.get('/billing/my-invoices')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'My Invoices &amp; Billing', res.data)

    def test_17_patient_cannot_view_another_patient_invoice(self):
        """17. Patient cannot view another patient's invoice (HTTP 403)."""
        import datetime as dt
        today = dt.date.today()
        b = Bill(
            bill_number='INV9999',
            patient_id=5,  # Other patient
            sub_total=500.0,
            total_amount=550.0,
            discount=0.0,
            tax_amount=50.0,
            payment_method='Cash',
            payment_status='Paid',
            bill_date=today,
            due_date=today
        )
        db.session.add(b)
        db.session.commit()

        self.login_as_patient()  # Logged in as Patient 4
        res = self.client.get(f'/billing/invoice/{b.id}')
        self.assertEqual(res.status_code, 403)

    def test_18_patient_can_submit_eligible_feedback(self):
        """18. Patient can submit feedback for received consultation service."""
        self.login_as_patient()
        res = self.client.post('/feedback/submit', data={
            'service_type': 'Doctor Performance',
            'doctor_id': 2,
            'rating': 5,
            'comment': 'Great consultation and attentive care.'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'My Submitted Feedback', res.data)

    def test_19_patient_can_view_own_feedback(self):
        """19. Patient can view own feedback history."""
        self.login_as_patient()
        res = self.client.get('/feedback/my-feedback')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'My Submitted Feedback', res.data)

    def test_20_patient_cannot_access_admin_tools(self):
        """20. Patient cannot access Admin-only system tools (HTTP 403)."""
        self.login_as_patient()
        for endpoint in ['/system-integration', '/testing-performance', '/reports/admin', '/feedback/admin']:
            res = self.client.get(endpoint)
            self.assertEqual(res.status_code, 403)

if __name__ == '__main__':
    unittest.main()
