# =============================================================================
# tests/test_notifications_workflow.py — Event-Driven Notifications Tests
# =============================================================================

import unittest
import os
import sys
import datetime
from werkzeug.security import generate_password_hash

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from database.connection import db
from models.user import User
from models.role import Role
from models.patient import Patient
from models.doctor import Doctor
from models.appointment import Appointment
from models.lab_report import LabReport
from models.prescription import Prescription
from models.notification import Notification

class NotificationsWorkflowTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app('default')
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.created_notifs = []
        self.created_appts = []
        self.created_reports = []
        self.created_prescriptions = []
        Notification.query.filter_by(patient_id=4).delete()
        db.session.commit()

    def tearDown(self):
        # Clean up only the specific records we created to keep seed data intact
        for x in self.created_notifs:
            db.session.delete(x)
        for x in self.created_appts:
            db.session.delete(x)
        for x in self.created_reports:
            db.session.delete(x)
        for x in self.created_prescriptions:
            db.session.delete(x)
        db.session.commit()
        db.session.rollback()
        self.app_context.pop()

    def test_01_appointment_booking_notification(self):
        """1. Successful appointment booking triggers patient notification."""
        from services.appointment_service import book_appointment
        
        initial_notifs_count = Notification.query.filter_by(patient_id=4).count()

        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        data = {
            'patient_id': 4,
            'doctor_id': 2,
            'appointment_date': tomorrow,
            'appointment_time': datetime.time(11, 0),
            'status': 'Confirmed'
        }
        appt, err = book_appointment(data)
        self.assertIsNotNone(appt)
        self.created_appts.append(appt)

        # Track the new notification created by service
        new_notif = Notification.query.filter_by(patient_id=4).order_by(Notification.id.desc()).first()
        if new_notif:
            self.created_notifs.append(new_notif)

        # Verify notification count increased by 1
        self.assertEqual(Notification.query.filter_by(patient_id=4).count(), initial_notifs_count + 1)
        self.assertEqual(new_notif.type, 'Appointment Reminder')
        self.assertIn("booked", new_notif.message)

    def test_02_lab_result_notification(self):
        """2. Lab report creation triggers patient notification."""
        from services.lab_service import create_lab_report
        
        initial_notifs_count = Notification.query.filter_by(patient_id=4, type='Lab Report').count()

        today = datetime.date.today()
        report = create_lab_report(
            patient_id=4,
            doctor_id=2,
            test_name='Serum Iron',
            test_date=today,
            result='75 ug/dL',
            remarks='Within normal range'
        )
        self.assertIsNotNone(report)
        self.created_reports.append(report)

        new_notif = Notification.query.filter_by(patient_id=4, type='Lab Report').order_by(Notification.id.desc()).first()
        if new_notif:
            self.created_notifs.append(new_notif)

        # Verify notification
        self.assertEqual(Notification.query.filter_by(patient_id=4, type='Lab Report').count(), initial_notifs_count + 1)
        self.assertIn("Serum Iron", new_notif.message)
        self.assertIn("75 ug/dL", new_notif.message)

    def test_03_prescription_notification(self):
        """3. Prescription creation triggers patient notification."""
        from services.prescription_service import create_prescription
        
        initial_notifs_count = Notification.query.filter_by(patient_id=4, type='Prescription Ready').count()

        today = datetime.date.today()
        items = [
            {'medicine_name': 'Vitamin C', 'dosage': '500 mg', 'frequency': 'Once daily', 'duration': '10 days'}
        ]
        pres = create_prescription(
            patient_id=4,
            doctor_id=2,
            prescription_date=today,
            special_instructions='Take with water',
            items_data=items
        )
        self.assertIsNotNone(pres)
        self.created_prescriptions.append(pres)

        new_notif = Notification.query.filter_by(patient_id=4, type='Prescription Ready').order_by(Notification.id.desc()).first()
        if new_notif:
            self.created_notifs.append(new_notif)

        # Verify notification
        self.assertEqual(Notification.query.filter_by(patient_id=4, type='Prescription Ready').count(), initial_notifs_count + 1)
        self.assertIn("prescription", new_notif.message.lower())

    def test_04_appointment_status_and_reschedule_notification(self):
        """4. Appointment rescheduling and cancellation trigger patient notifications."""
        from services.appointment_service import book_appointment, update_appointment, cancel_appointment
        
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        data = {
            'patient_id': 4,
            'doctor_id': 2,
            'appointment_date': tomorrow,
            'appointment_time': datetime.time(11, 0),
            'status': 'Confirmed'
        }
        appt, err = book_appointment(data)
        self.assertIsNotNone(appt)
        self.created_appts.append(appt)
        
        # Clear booking notification from tracking so count represents updates
        booking_notif = Notification.query.filter_by(patient_id=4).order_by(Notification.id.desc()).first()
        if booking_notif:
            self.created_notifs.append(booking_notif)

        initial_notifs_count = Notification.query.filter_by(patient_id=4).count()

        # Reschedule appointment (time changes)
        update_data = {
            'appointment_time': datetime.time(12, 0)
        }
        updated, err = update_appointment(appt.id, update_data)
        self.assertIsNotNone(updated)
        
        resched_notif = Notification.query.filter_by(patient_id=4).order_by(Notification.id.desc()).first()
        if resched_notif and resched_notif not in self.created_notifs:
            self.created_notifs.append(resched_notif)

        self.assertEqual(Notification.query.filter_by(patient_id=4).count(), initial_notifs_count + 1)
        self.assertIn("rescheduled", resched_notif.message.lower())
        
        # Track notifications before cancel
        initial_notifs_count2 = Notification.query.filter_by(patient_id=4).count()

        # Cancel appointment
        cancelled = cancel_appointment(appt.id)
        self.assertEqual(cancelled.status, 'Cancelled')

        cancel_notif = Notification.query.filter_by(patient_id=4).order_by(Notification.id.desc()).first()
        if cancel_notif and cancel_notif not in self.created_notifs:
            self.created_notifs.append(cancel_notif)

        self.assertEqual(Notification.query.filter_by(patient_id=4).count(), initial_notifs_count2 + 1)
        self.assertIn("cancelled", cancel_notif.message.lower())

    def test_05_duplicate_notification_protection(self):
        """5. Concurrent or retried notification calls do not create duplicates."""
        from services.notification_service import send_notification
        
        initial_count = Notification.query.filter_by(patient_id=4, message='This is a unique test notification message.').count()

        # First send
        n1 = send_notification(4, 'General Info', 'This is a unique test notification message.', commit=True)
        self.assertIsNotNone(n1)
        if n1 not in self.created_notifs:
            self.created_notifs.append(n1)

        # Second send within 10 seconds with identical attributes
        n2 = send_notification(4, 'General Info', 'This is a unique test notification message.', commit=True)
        self.assertEqual(n1.id, n2.id)

        # Verify only 1 new notification exists in DB
        self.assertEqual(Notification.query.filter_by(patient_id=4, message='This is a unique test notification message.').count(), initial_count + 1)

    def test_06_transactional_rollback_notification(self):
        """6. Failure in main transaction rolls back notification additions."""
        from services.notification_service import send_notification
        
        initial_count = Notification.query.filter_by(message='Rollback test notification.').count()

        # Create a notification in session without committing
        send_notification(4, 'General Info', 'Rollback test notification.', commit=False)
        
        # Verify it has been flushed and exists in DB transaction state
        self.assertEqual(Notification.query.filter_by(message='Rollback test notification.').count(), initial_count + 1)
        
        # Rollback transaction
        db.session.rollback()
        
        # Verify it is gone from database
        self.assertEqual(Notification.query.filter_by(message='Rollback test notification.').count(), initial_count)

if __name__ == '__main__':
    unittest.main()
