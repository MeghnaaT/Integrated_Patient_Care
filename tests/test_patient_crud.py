import unittest
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from database.connection import db
from models.user import User
from models.patient import Patient

class TestPatientCRUD(unittest.TestCase):

    def setUp(self):
        self.app = create_app('development')
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Cleanup test records
        from models.user import User
        test_user = User.query.filter_by(email='ramesh.sinha@ipcms.com').first()
        if test_user:
            db.session.delete(test_user)
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

    def test_admin_patient_crud_flow(self):
        print("\n--- Testing Admin Patient CRUD Flow ---")

        # 1. Login as Admin
        res = self.login('admin@ipcms.com', 'admin123')
        self.assertIn(b'Admin Dashboard', res.data)
        print("OK: Successfully logged in as Admin.")

        # 2. Check Patient List works and contains seeded patient Ravi Kumar
        res = self.client.get('/patient/list')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Ravi Kumar', res.data)
        print("OK: Patient Directory loaded and contains Ravi Kumar.")

        # 3. Verify duplicate email validation works
        res = self.client.post('/patient/add', data={
            'first_name': 'Ramesh',
            'last_name': 'Sinha',
            'age': 40,
            'gender': 'Male',
            'blood_group': 'B+',
            'phone_number': '9876543299',
            'email': 'patient@ipcms.com',  # seeded email, duplicate
            'address': 'MG Road, Bangalore'
        })
        self.assertIn(b'exists', res.data)
        print("OK: Correctly prevented creation of patient with duplicate email.")

        # 4. Add Patient Ramesh Sinha
        res = self.client.post('/patient/add', data={
            'first_name': 'Ramesh',
            'last_name': 'Sinha',
            'age': 40,
            'gender': 'Male',
            'blood_group': 'B+',
            'phone_number': '9876543299',
            'email': 'ramesh.sinha@ipcms.com',
            'address': 'MG Road, Bangalore'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'registered successfully', res.data)
        print("OK: Successfully registered new patient Ramesh Sinha.")

        # 5. Verify patient in DB and linked user created
        new_pat = Patient.query.filter_by(email='ramesh.sinha@ipcms.com').first()
        self.assertIsNotNone(new_pat)
        self.assertEqual(new_pat.first_name, 'Ramesh')
        self.assertEqual(new_pat.last_name, 'Sinha')
        self.assertEqual(new_pat.age, 40)
        self.assertIsNotNone(new_pat.user)
        self.assertEqual(new_pat.user.username, 'pat_ramesh_sinha')
        self.assertEqual(new_pat.user.role.name, 'Patient')
        print("OK: Verified Database mappings and 1-to-1 User linkage.")

        # 6. Verify Search works
        res = self.client.get('/patient/list?q=Ramesh')
        self.assertIn(b'Ramesh Sinha', res.data)
        self.assertNotIn(b'Ravi Kumar', res.data)
        print("OK: Search functionality filters correct patients.")

        # 7. Edit Patient Ramesh Sinha
        res = self.client.post(f'/patient/edit/{new_pat.id}', data={
            'first_name': 'Ramesh',
            'last_name': 'Sinha',
            'age': 41,  # updated age
            'gender': 'Male',
            'blood_group': 'B+',
            'phone_number': '9876543299',
            'email': 'ramesh.sinha@ipcms.com',
            'address': 'New MG Road, Bangalore'  # updated address
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'updated successfully', res.data)

        # Re-fetch and verify updated age
        db.session.refresh(new_pat)
        self.assertEqual(new_pat.age, 41)
        print("OK: Edit Patient successfully updated database record.")

        # 8. View Patient details page
        res = self.client.get(f'/patient/view/{new_pat.id}')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Ramesh Sinha', res.data)
        self.assertIn(b'New MG Road', res.data)
        print("OK: View Details page renders correct demographics.")

        # 9. Delete Patient (soft-delete)
        res = self.client.post(f'/patient/delete/{new_pat.id}', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'soft-deleted successfully', res.data)
        
        # Verify soft-delete status in DB
        db.session.refresh(new_pat.user)
        self.assertFalse(new_pat.user.is_active)
        print("OK: Soft-delete updates User is_active to False.")

        # Verify no longer returned in Patient Directory
        res = self.client.get('/patient/list')
        self.assertNotIn(b'Ramesh Sinha', res.data)
        print("OK: Soft-deleted patient hidden from directory.")

    def test_role_based_access_control(self):
        print("\n--- Testing Role Based Access Control ---")

        # 1. Doctor role permissions
        self.logout()
        res = self.login('doctor@ipcms.com', 'doctor123')
        self.assertIn(b'Doctor Dashboard', res.data)

        # Doctor can view patient list
        res = self.client.get('/patient/list')
        self.assertEqual(res.status_code, 200)

        # Doctor CANNOT add patient (403 Forbidden)
        res = self.client.get('/patient/add')
        self.assertEqual(res.status_code, 403)

        # Doctor CANNOT edit patient
        res = self.client.post('/patient/edit/4', data={})
        self.assertEqual(res.status_code, 403)

        # Doctor CANNOT delete patient
        res = self.client.post('/patient/delete/4')
        self.assertEqual(res.status_code, 403)
        print("OK: Verified Doctor permissions (View allowed, CRUD forbidden).")

        # 2. Patient role permissions (Ravi Kumar has ID 4)
        self.logout()
        res = self.login('patient@ipcms.com', 'patient123')
        self.assertIn(b'My Dashboard', res.data)

        # Patient CANNOT view patient list
        res = self.client.get('/patient/list')
        self.assertEqual(res.status_code, 403)

        # Patient CAN edit their own profile details
        res = self.client.get('/patient/edit/4')
        self.assertEqual(res.status_code, 200)

        # Patient CANNOT edit another patient's details
        res = self.client.get('/patient/edit/1')  # Admin user ID or other patient ID
        self.assertEqual(res.status_code, 403)

        # Patient CANNOT delete patients
        res = self.client.post('/patient/delete/4')
        self.assertEqual(res.status_code, 403)
        print("OK: Verified Patient permissions (Own profile allowed, other profiles and Directory forbidden).")

if __name__ == '__main__':
    unittest.main()
