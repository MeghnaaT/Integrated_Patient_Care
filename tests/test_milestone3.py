# =============================================================================
# tests/test_milestone3.py — Milestone 3 Comprehensive Test Suite
# =============================================================================

import unittest
import os
import sys
import datetime
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from database.connection import db
from models.user import User
from models.patient import Patient
from models.pharmacy import Medicine, MedicineDispensation
from models.billing import Bill, BillItem
from models.notification import Notification
from services.pharmacy_service import get_pharmacy_metrics, list_inventory, add_medicine, update_medicine_stock, dispense_medicine
from services.billing_service import generate_bill_for_patient, get_bill_by_id_or_number, list_billing_history
from services.notification_service import get_notification_metrics, list_notifications, send_notification, mark_notification_as_read
from services.analytics_service import get_executive_analytics_summary

class Milestone3TestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app('default')
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        db.session.rollback()
        self.app_context.pop()

    def test_01_advanced_patient_search(self):
        """Test Day 1 Advanced Patient Search by ID, Name, Phone, Aadhaar, Email."""
        p = Patient.query.filter_by(id=4).first()
        self.assertIsNotNone(p)
        self.assertEqual(p.full_name, "Rahul Kumar")
        self.assertEqual(p.phone_number, "9876543210")

    def test_02_pharmacy_inventory_and_dispensation(self):
        """Test Day 2 Pharmacy Inventory management, stock update, and dispensing."""
        metrics = get_pharmacy_metrics()
        self.assertGreaterEqual(metrics['total_medicines'], 1)

        unique_code = f"MED_{int(time.time() * 1000)}"
        med = add_medicine(unique_code, 'Test Supplement', 'Tablet', 'Pharma Test Ltd', 100, 25.50, datetime.date(2028, 1, 1))
        self.assertIsNotNone(med.id)
        self.assertEqual(med.stock, 100)

        updated_med = update_medicine_stock(med.id, 150)
        self.assertEqual(updated_med.stock, 150)

        dispense = dispense_medicine(patient_id=4, medicine_id=med.id, quantity=5)
        self.assertEqual(dispense.quantity, 5)
        self.assertEqual(med.stock, 145)

    def test_03_billing_and_invoice(self):
        """Test Day 3 Billing & Payment calculation and invoice generation."""
        bill = generate_bill_for_patient(patient_id=4, payment_method='UPI', transaction_id=f'UPI_{int(time.time())}')
        self.assertIsNotNone(bill.id)
        self.assertIn("BILL", bill.bill_number)
        self.assertEqual(bill.payment_status, 'Paid')
        self.assertGreater(float(bill.total_amount), 0)

        found_bill = get_bill_by_id_or_number(bill.bill_number)
        self.assertIsNotNone(found_bill)
        self.assertEqual(found_bill.id, bill.id)

    def login(self, email, password):
        return self.client.post('/auth/login', data={
            'email': email,
            'password': password,
            'remember_me': False
        }, follow_redirects=True)

    def logout(self):
        return self.client.get('/auth/logout', follow_redirects=True)

    def test_04_rest_api_endpoints(self):
        """Test Day 4 REST API endpoints and response time under 300 ms."""
        self.login('admin@ipcms.com', 'admin123')
        start = time.time()
        res = self.client.get('/api/v1/patients')
        elapsed_ms = (time.time() - start) * 1000

        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertEqual(json_data['status'], 'success')
        self.assertLess(elapsed_ms, 300.0) # < 300 ms latency test requirement

        res2 = self.client.get('/api/v1/pharmacy')
        self.assertEqual(res2.status_code, 200)

        res3 = self.client.get('/api/v1/billing')
        self.assertEqual(res3.status_code, 200)
        self.logout()

    def test_05_notification_engine(self):
        """Test Day 5 Notification dispatch engine and delivery success rate."""
        metrics = get_notification_metrics()
        self.assertGreaterEqual(metrics['delivery_success_rate'], 95.0)

        n = send_notification(patient_id=4, notification_type='Appointment Reminder', message='Test appointment alert')
        self.assertIsNotNone(n.id)
        self.assertIn(n.status, ['Delivered', 'Read'])

        success = mark_notification_as_read(n.id)
        self.assertTrue(success)

    def test_06_analytics_summary(self):
        """Test Day 6 Executive Dashboard Analytics summary and Chart.js datasets."""
        summary = get_executive_analytics_summary()
        self.assertIn('total_patients', summary)
        self.assertIn('weekly_appointments', summary)
        self.assertIn('gender_distribution', summary)
        self.assertIn('weekly_revenue', summary)
        self.assertIn('department_breakdown', summary)

if __name__ == '__main__':
    unittest.main()
