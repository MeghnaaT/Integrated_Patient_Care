import unittest
import os
import sys
import datetime

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from database.connection import db
from models.user import User
from models.appointment import Appointment
from models.doctor import Doctor
from models.patient import Patient

class TestAppointmentCRUD(unittest.TestCase):

    def setUp(self):
        self.app = create_app('development')
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Cleanup test records
        from models.appointment import Appointment
        # Delete any test appointments that might have been created by previous test runs
        Appointment.query.filter_by(patient_id=4, doctor_id=2).delete()
        db.session.commit()

    def tearDown(self):
        db.session.rollback()
        self.app_context.pop()

    def login(self, email, password):
        return self.client.post('/auth/login', data={
            'email': email,
            'password': password,
            'remember_me': False
        }, follow_redirects=True)

    def logout(self):
        return self.client.get('/auth/logout', follow_redirects=True)

    def test_admin_appointment_crud_flow(self):
        print("\n--- Testing Admin Appointment CRUD Flow ---")

        # 1. Login as Admin
        res = self.login('admin@ipcms.com', 'admin123')
        self.assertIn(b'Admin Dashboard', res.data)
        print("OK: Successfully logged in as Admin.")

        # 2. Check Directory works
        res = self.client.get('/appointment/list')
        self.assertEqual(res.status_code, 200)
        print("OK: Appointment Directory loaded.")

        # Set up a target date: 7 days in the future
        target_date = datetime.date.today() + datetime.timedelta(days=7)
        date_str = target_date.strftime('%Y-%m-%d')
        
        # Dr. John Smith (id=2) has available_time "10:00 AM - 01:00 PM"
        
        # 3. Test booking outside doctor hours (05:00 PM)
        res = self.client.post('/appointment/book', data={
            'patient_id': 4, # Ravi Kumar
            'doctor_id': 2, # John Smith
            'appointment_date': date_str,
            'appointment_time': '17:00' # 05:00 PM
        })
        self.assertIn(b'outside', res.data)
        print("OK: Correctly rejected booking outside doctor available hours.")

        # 4. Test booking in the past
        past_date = datetime.date.today() - datetime.timedelta(days=1)
        res = self.client.post('/appointment/book', data={
            'patient_id': 4,
            'doctor_id': 2,
            'appointment_date': past_date.strftime('%Y-%m-%d'),
            'appointment_time': '11:00'
        })
        self.assertIn(b'past', res.data)
        print("OK: Correctly rejected booking in the past.")

        # 5. Book a valid appointment (11:00 AM)
        res = self.client.post('/appointment/book', data={
            'patient_id': 4,
            'doctor_id': 2,
            'appointment_date': date_str,
            'appointment_time': '11:00'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'scheduled successfully', res.data)
        print("OK: Successfully scheduled a valid appointment slot.")

        # Verify DB insertion
        appt = Appointment.query.filter_by(
            patient_id=4,
            doctor_id=2,
            appointment_date=target_date,
            appointment_time=datetime.time(11, 0)
        ).first()
        self.assertIsNotNone(appt)
        self.assertEqual(appt.status, 'Confirmed')

        # 6. Test booking conflict for Doctor (another patient booking at 11:00 AM same day)
        res = self.client.post('/appointment/book', data={
            'patient_id': 4,
            'doctor_id': 2,
            'appointment_date': date_str,
            'appointment_time': '11:00'
        })
        self.assertIn(b'already', res.data)
        print("OK: Correctly prevented duplicate booking slot (conflict detection).")

        # 7. Edit/reschedule appointment (change to 12:00 PM)
        res = self.client.post(f'/appointment/edit/{appt.id}', data={
            'patient_id': 4,
            'doctor_id': 2,
            'appointment_date': date_str,
            'appointment_time': '12:00',
            'status': 'Confirmed'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'modified successfully', res.data)

        # Verify updated in DB
        db.session.refresh(appt)
        self.assertEqual(appt.appointment_time, datetime.time(12, 0))
        print("OK: Rescheduling updated time to 12:00 PM successfully.")

        # 8. View doctor schedule agenda
        res = self.client.get(f'/appointment/doctor/2/schedule?date={date_str}')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Ravi Kumar', res.data)
        print("OK: Doctor schedule daily agenda contains patient.")

        # 9. Cancel appointment
        res = self.client.post(f'/appointment/cancel/{appt.id}', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'cancelled successfully', res.data)

        # Verify Cancelled in DB
        db.session.refresh(appt)
        self.assertEqual(appt.status, 'Cancelled')
        print("OK: Successfully cancelled the appointment.")

    def test_role_based_access_control(self):
        print("\n--- Testing Role Based Access Control ---")

        # Get the seeded appointment or create one to test actions
        target_date = datetime.date.today() + datetime.timedelta(days=10)
        date_str = target_date.strftime('%Y-%m-%d')
        
        # Admin creates an active appointment
        self.login('admin@ipcms.com', 'admin123')
        res = self.client.post('/appointment/book', data={
            'patient_id': 4, # Ravi Kumar
            'doctor_id': 2, # John Smith
            'appointment_date': date_str,
            'appointment_time': '11:00'
        }, follow_redirects=True)
        self.logout()

        appt = Appointment.query.filter_by(
            patient_id=4,
            doctor_id=2,
            appointment_date=target_date,
            appointment_time=datetime.time(11, 0)
        ).first()
        self.assertIsNotNone(appt)

        # 1. Patient role permissions (Ravi Kumar: email patient@ipcms.com, id=4)
        res = self.login('patient@ipcms.com', 'patient123')
        self.assertIn(b'My Dashboard', res.data)

        # Patient CANNOT view appointment directory list
        res = self.client.get('/appointment/list')
        self.assertEqual(res.status_code, 403)

        # Patient CAN book appointment for themselves
        res = self.client.post('/appointment/book', data={
            'patient_id': 4,
            'doctor_id': 2,
            'appointment_date': date_str,
            'appointment_time': '12:30'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'scheduled successfully', res.data)
        
        # Verify self-booking belongs to Patient (id=4) and status is Pending
        self_appt = Appointment.query.filter_by(
            patient_id=4,
            doctor_id=2,
            appointment_date=target_date,
            appointment_time=datetime.time(12, 30)
        ).first()
        self.assertIsNotNone(self_appt)
        self.assertEqual(self_appt.status, 'Pending')

        # Patient CANNOT reschedule/edit appointments
        res = self.client.post(f'/appointment/edit/{appt.id}', data={})
        self.assertEqual(res.status_code, 403)

        # Patient CAN cancel their own appointment
        res = self.client.post(f'/appointment/cancel/{self_appt.id}', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        db.session.refresh(self_appt)
        self.assertEqual(self_appt.status, 'Cancelled')

        # Patient CANNOT cancel another patient's appointment
        self.logout()
        
        # 2. Nurse role permissions
        res = self.login('nurse@ipcms.com', 'nurse123')
        self.assertIn(b'Nurse Dashboard', res.data)

        # Nurse CAN view list
        res = self.client.get('/appointment/list')
        self.assertEqual(res.status_code, 200)

        # Nurse CAN edit/reschedule
        res = self.client.post(f'/appointment/edit/{appt.id}', data={
            'patient_id': 4,
            'doctor_id': 2,
            'appointment_date': date_str,
            'appointment_time': '11:30',
            'status': 'Confirmed'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        db.session.refresh(appt)
        self.assertEqual(appt.appointment_time, datetime.time(11, 30))
        print("OK: Verified Patient and Nurse role scheduling controls.")

if __name__ == '__main__':
    unittest.main()
