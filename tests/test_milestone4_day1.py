# =============================================================================
# tests/test_milestone4_day1.py — Milestone 4 Day 1 Test Suite
# =============================================================================

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from database.connection import db
from services.analytics_service import get_executive_analytics_summary
from models.user import User

class Milestone4Day1TestCase(unittest.TestCase):

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

    def test_01_analytics_service_dynamic_queries(self):
        """Test that get_executive_analytics_summary returns all 9 metric cards and chart datasets."""
        summary = get_executive_analytics_summary()

        # Verify 9 Cards
        self.assertIn('total_patients', summary)
        self.assertIn('active_doctors', summary)
        self.assertIn('todays_appointments', summary)
        self.assertIn('completed_consultations', summary)
        self.assertIn('cancelled_appointments', summary)
        self.assertIn('pending_lab_reports', summary)
        self.assertIn('total_bills', summary)
        self.assertIn('unread_notifications', summary)
        self.assertIn('revenue_summary', summary)

        # Verify Revenue Breakdown
        rev = summary['revenue_summary']
        self.assertIn('total_revenue', rev)
        self.assertIn('consultation_revenue', rev)
        self.assertIn('lab_revenue', rev)
        self.assertIn('pharmacy_revenue', rev)

        # Verify Chart Datasets
        self.assertIn('monthly_registrations', summary)
        self.assertIn('appointment_trends', summary)
        self.assertIn('doctor_consultations', summary)
        self.assertIn('demographics', summary)
        self.assertIn('disease_distribution', summary)
        self.assertIn('lab_statistics', summary)
        self.assertIn('revenue_analysis', summary)
        self.assertIn('recent_logs', summary)

    def test_02_dashboard_overview_route_authorization(self):
        """Test access control on /dashboard-overview."""
        # 1. Anonymous user redirected to login
        res = self.client.get('/dashboard-overview')
        self.assertEqual(res.status_code, 302)

        # 2. Patient role forbidden (403)
        self.login('patient@ipcms.com', 'patient123')
        res = self.client.get('/dashboard-overview')
        self.assertEqual(res.status_code, 403)
        self.logout()

        # 3. Admin role allowed (200)
        self.login('admin@ipcms.com', 'admin123')
        res = self.client.get('/dashboard-overview')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Analytics Dashboard', res.data)
        self.logout()

    def test_03_dashboard_overview_data_json(self):
        """Test /dashboard-overview/data JSON endpoint."""
        self.login('admin@ipcms.com', 'admin123')
        res = self.client.get('/dashboard-overview/data')
        self.assertEqual(res.status_code, 200)

        json_data = res.get_json()
        self.assertEqual(json_data['status'], 'success')
        self.assertIn('analytics', json_data)
        self.logout()

if __name__ == '__main__':
    unittest.main()
