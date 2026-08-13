# =============================================================================
# tests/test_milestone4_day4.py — Milestone 4 Day 4 Test Suite
# =============================================================================

import unittest
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from database.connection import db
from models.patient import Patient
from models.user import User
from services.testing_performance_service import measure_database_query_speed, get_performance_optimization_metrics

class Milestone4Day4TestCase(unittest.TestCase):

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

    # -------------------------------------------------------------------------
    # 1. Functional Testing Across Core Hospital Modules
    # -------------------------------------------------------------------------
    def test_01_functional_modules_health(self):
        """Functional testing across Login, Patient, Doctor, Appointment, Consultation, EHR, Rx, Lab, Pharmacy, Billing, Notifications, Reports, Dashboard."""
        self.login('admin@ipcms.com', 'admin123')

        routes_to_test = [
            '/admin/dashboard',
            '/patient/list',
            '/doctor/list',
            '/nurse/list',
            '/appointment/list',
            '/consultations/history/4',
            '/ehr/4',
            '/prescriptions/list',
            '/laboratory/reports',
            '/pharmacy/dashboard',
            '/billing/patient-billing',
            '/notifications/dashboard',
            '/reports/admin',
            '/dashboard-overview',
            '/system-integration',
            '/testing-performance'
        ]

        for route in routes_to_test:
            res = self.client.get(route, follow_redirects=True)
            self.assertEqual(res.status_code, 200, f"Failed route health check on {route}")

        self.logout()

    # -------------------------------------------------------------------------
    # 2. Security Testing (Auth, RBAC, SQLi, XSS, CSRF, IDOR)
    # -------------------------------------------------------------------------
    def test_02_security_authentication_and_protected_routes(self):
        """Security Test: Verify unauthenticated users are redirected to login."""
        protected_routes = ['/admin/dashboard', '/patient/list', '/testing-performance', '/reports/admin']
        for route in protected_routes:
            res = self.client.get(route)
            self.assertEqual(res.status_code, 302, f"Unprotected route leak on {route}")

    def test_03_security_rbac_authorization(self):
        """Security Test: Verify Patient role is forbidden on administrative routes."""
        self.login('patient@ipcms.com', 'patient123')
        forbidden_routes = ['/doctor/add', '/nurse/add', '/reports/admin', '/testing-performance']
        for route in forbidden_routes:
            res = self.client.get(route)
            self.assertEqual(res.status_code, 403, f"RBAC permission leak on {route}")
        self.logout()

    def test_04_security_sqli_resistance(self):
        """Security Test: Verify SQL Injection payload resistance."""
        sqli_payload = "' OR '1'='1"
        res = self.client.post('/auth/login', data={
            'email': sqli_payload,
            'password': 'password'
        }, follow_redirects=True)
        # Must fail login cleanly without 500 DB syntax error
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Sign In', res.data)

    def test_05_security_idor_checks(self):
        """Security Test: Verify IDOR prevention on private patient medical report."""
        self.login('patient@ipcms.com', 'patient123')
        # Patient ID 4 attempts to view Patient ID 1's report -> Must return 403 Forbidden
        res = self.client.get('/reports/patient-report/1')
        self.assertEqual(res.status_code, 403)
        self.logout()

    # -------------------------------------------------------------------------
    # 3. Performance Testing (< 300 ms API & Query latency)
    # -------------------------------------------------------------------------
    def test_06_performance_api_response_latency(self):
        """Performance Test: Measure REST API response time (< 300 ms target)."""
        start = time.time()
        res = self.client.get('/api/v1/patients')
        elapsed_ms = (time.time() - start) * 1000.0

        self.assertEqual(res.status_code, 200)
        self.assertLess(elapsed_ms, 300.0, f"API response latency {elapsed_ms}ms exceeded 300ms limit")

    def test_07_performance_database_query_speed(self):
        """Performance Test: Measure database query speed (< 100 ms target)."""
        db_speed = measure_database_query_speed()
        self.assertLess(db_speed, 100.0, f"Database query speed {db_speed}ms exceeded 100ms limit")

if __name__ == '__main__':
    unittest.main()
