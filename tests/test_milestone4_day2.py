# =============================================================================
# tests/test_milestone4_day2.py — Milestone 4 Day 2 Test Suite
# =============================================================================

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from database.connection import db
from services.report_export_service import fetch_report_data, generate_report_csv

class Milestone4Day2TestCase(unittest.TestCase):

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

    def login(self, email, password):
        return self.client.post('/auth/login', data={
            'email': email,
            'password': password,
            'remember_me': False
        }, follow_redirects=True)

    def logout(self):
        return self.client.get('/auth/logout', follow_redirects=True)

    def test_01_fetch_all_12_administrative_reports(self):
        """Test fetch_report_data for all 12 report types."""
        reports = [
            'patient', 'appointment', 'consultation', 'prescription',
            'doctor_performance', 'department', 'monthly', 'billing',
            'laboratory', 'pharmacy', 'notification', 'satisfaction'
        ]

        for r_type in reports:
            res = fetch_report_data(report_type=r_type)
            self.assertIn('rows', res)
            self.assertIn('summary_stats', res)
            self.assertIn('total_items', res)

    def test_02_csv_export_generation(self):
        """Test CSV string generator for report export."""
        res = fetch_report_data(report_type='patient')
        csv_str = generate_report_csv('patient', res)
        self.assertIsInstance(csv_str, str)
        self.assertIn('Name', csv_str)

    def test_03_admin_reports_hub_routes(self):
        """Test /reports/admin endpoints for Admin user."""
        self.login('admin@ipcms.com', 'admin123')
        
        # Test Hub rendering
        res = self.client.get('/reports/admin?report_type=patient')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Administrative Reporting', res.data)

        # Test CSV export endpoint
        res_csv = self.client.get('/reports/export/csv?report_type=appointment')
        self.assertEqual(res_csv.status_code, 200)
        self.assertIn('text/csv', res_csv.content_type)

        # Test Excel export endpoint
        res_xls = self.client.get('/reports/export/excel?report_type=billing')
        self.assertEqual(res_xls.status_code, 200)
        self.assertIn('application/vnd.ms-excel', res_xls.content_type)

        # Test PDF print endpoint
        res_pdf = self.client.get('/reports/export/pdf?report_type=consultation')
        self.assertEqual(res_pdf.status_code, 200)
        self.assertIn(b'CITY CARE HOSPITAL', res_pdf.data)

        self.logout()

    def test_04_access_control(self):
        """Test role-based access control on administrative report endpoints."""
        # Patient forbidden (403)
        self.login('patient@ipcms.com', 'patient123')
        res = self.client.get('/reports/admin')
        self.assertEqual(res.status_code, 403)
        self.logout()

if __name__ == '__main__':
    unittest.main()
