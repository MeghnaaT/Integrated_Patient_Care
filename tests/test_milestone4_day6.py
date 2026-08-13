# =============================================================================
# tests/test_milestone4_day6.py — Milestone 4 Day 6 Patient Feedback Test Suite
# =============================================================================

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from database.connection import db
from models.feedback import Feedback
from services.feedback_service import create_feedback, can_patient_submit_feedback, get_feedback_satisfaction_statistics

class Milestone4Day6TestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app('default')
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

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

    def test_01_create_patient_feedback_workflow(self):
        """Test submitting 1-5 star patient feedback and verifying database record."""
        data = {
            'patient_id': 4,
            'service_type': 'Doctor Performance',
            'doctor_id': 2,
            'department_id': 1,
            'rating': 5,
            'comment': 'Outstanding medical consultation and clear advice.'
        }
        fbk = create_feedback(data)
        self.assertIsNotNone(fbk.id)
        self.assertTrue(fbk.feedback_code.startswith('FBK'))
        self.assertEqual(fbk.rating, 5)
        self.assertEqual(fbk.comment, 'Outstanding medical consultation and clear advice.')

    def test_02_invalid_rating_validation(self):
        """Test rejecting invalid star ratings (<1 or >5)."""
        data = {
            'patient_id': 4,
            'service_type': 'Hospital Service',
            'rating': 6,
            'comment': 'Invalid rating test'
        }
        with self.assertRaises(ValueError):
            create_feedback(data)

    def test_03_patient_feedback_routes_and_access(self):
        """Test patient feedback submission, history, and admin dashboard routes."""
        # Patient submits feedback via UI
        self.login('patient@ipcms.com', 'patient123')
        
        res_submit = self.client.get('/feedback/submit')
        self.assertEqual(res_submit.status_code, 200)

        res_history = self.client.get('/feedback/my-feedback')
        self.assertEqual(res_history.status_code, 200)
        self.assertIn(b'My Submitted Feedback', res_history.data)

        self.logout()

        # Admin views feedback dashboard
        self.login('admin@ipcms.com', 'admin123')
        res_admin = self.client.get('/feedback/admin')
        self.assertEqual(res_admin.status_code, 200)
        self.assertIn(b'Patient Feedback', res_admin.data)

        # Admin exports feedback CSV
        res_csv = self.client.get('/feedback/export/csv')
        self.assertEqual(res_csv.status_code, 200)
        self.assertIn(b'Feedback Code', res_csv.data)

        self.logout()

    def test_04_satisfaction_statistics_calculation(self):
        """Test patient satisfaction score and ratings statistics calculation."""
        stats = get_feedback_satisfaction_statistics()
        self.assertIn('overall_avg_rating', stats)
        self.assertIn('satisfaction_score_pct', stats)
        self.assertIn('total_reviews', stats)
        self.assertIn('rating_breakdown', stats)

if __name__ == '__main__':
    unittest.main()
