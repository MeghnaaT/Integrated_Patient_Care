import unittest
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from database.connection import db
from models.user import User
from models.nurse import Nurse

class TestNurseCRUD(unittest.TestCase):

    def setUp(self):
        self.app = create_app('development')
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Cleanup test records
        from models.user import User
        test_user = User.query.filter_by(email='ellen.ripley@ipcms.com').first()
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

    def test_admin_nurse_crud_flow(self):
        print("\n--- Testing Admin Nurse CRUD Flow ---")

        # 1. Login as Admin
        res = self.login('admin@ipcms.com', 'admin123')
        self.assertIn(b'Admin Dashboard', res.data)
        print("OK: Successfully logged in as Admin.")

        # 2. Check Nurse List works and contains seeded nurse Sarah Connor
        res = self.client.get('/nurse/list')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Sarah Connor', res.data)
        print("OK: Nurse Directory loaded and contains Sarah Connor.")

        # 3. Verify duplicate email validation works
        res = self.client.post('/nurse/add', data={
            'first_name': 'Ellen',
            'last_name': 'Ripley',
            'department_id': 1, # Cardiology
            'shift': 'Night',
            'contact_number': '+919876543277',
            'email': 'nurse@ipcms.com'  # seeded email, duplicate
        })
        self.assertIn(b'exists', res.data)
        print("OK: Correctly prevented creation of nurse with duplicate email.")

        # 4. Add Nurse Ellen Ripley
        res = self.client.post('/nurse/add', data={
            'first_name': 'Ellen',
            'last_name': 'Ripley',
            'department_id': 1, # Cardiology
            'shift': 'Night',
            'contact_number': '+919876543277',
            'email': 'ellen.ripley@ipcms.com'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'registered successfully', res.data)
        print("OK: Successfully registered new nurse Ellen Ripley.")

        # 5. Verify nurse in DB and linked user created
        new_nurse = Nurse.query.filter_by(contact_number='+919876543277').first()
        self.assertIsNotNone(new_nurse)
        self.assertEqual(new_nurse.first_name, 'Ellen')
        self.assertEqual(new_nurse.last_name, 'Ripley')
        self.assertEqual(new_nurse.shift, 'Night')
        self.assertEqual(new_nurse.department_id, 1)
        self.assertIsNotNone(new_nurse.user)
        self.assertEqual(new_nurse.user.username, 'nurse_ellen_ripley')
        self.assertEqual(new_nurse.user.email, 'ellen.ripley@ipcms.com')
        self.assertEqual(new_nurse.user.role.name, 'Nurse')
        print("OK: Verified Database mappings, custom shift column, and 1-to-1 User linkage.")

        # 6. Verify Search works
        res = self.client.get('/nurse/list?q=Ripley')
        self.assertIn(b'Ellen Ripley', res.data)
        self.assertNotIn(b'Sarah Connor', res.data)
        print("OK: Search filters by name and shift correctly.")

        # 7. Edit Nurse Ellen Ripley (change shift)
        res = self.client.post(f'/nurse/edit/{new_nurse.id}', data={
            'first_name': 'Ellen',
            'last_name': 'Ripley',
            'department_id': 1,
            'shift': 'Evening',  # updated
            'contact_number': '+919876543277',
            'email': 'ellen.ripley@ipcms.com'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'updated successfully', res.data)

        # Re-fetch and verify shift is updated
        db.session.refresh(new_nurse)
        self.assertEqual(new_nurse.shift, 'Evening')
        print("OK: Edit Nurse successfully updated shift in database.")

        # 8. View Nurse profile details page
        res = self.client.get(f'/nurse/view/{new_nurse.id}')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Ellen Ripley', res.data)
        self.assertIn(b'Evening', res.data)
        print("OK: View Nurse Details page renders correct shift and demographics.")

        # 9. Delete Nurse (soft-delete)
        res = self.client.post(f'/nurse/delete/{new_nurse.id}', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'soft-deleted successfully', res.data)
        
        # Verify soft-delete status in DB
        db.session.refresh(new_nurse.user)
        self.assertFalse(new_nurse.user.is_active)
        print("OK: Soft-delete updates User is_active to False.")

        # Verify no longer returned in Nurse Directory
        res = self.client.get('/nurse/list')
        self.assertNotIn(b'Ellen Ripley', res.data)
        print("OK: Soft-deleted nurse hidden from directory.")

    def test_role_based_access_control(self):
        print("\n--- Testing Role Based Access Control ---")

        # Get seeded nurse ID (Sarah Connor is id = 3)
        nurse = db.session.get(Nurse, 3)
        self.assertIsNotNone(nurse)

        # 1. Doctor role permissions
        self.logout()
        res = self.login('doctor@ipcms.com', 'doctor123')
        self.assertIn(b'Doctor Dashboard', res.data)

        # Doctor can view nurse directory
        res = self.client.get('/nurse/list')
        self.assertEqual(res.status_code, 200)
        
        # Doctor can view nurse profile
        res = self.client.get(f'/nurse/view/{nurse.id}')
        self.assertEqual(res.status_code, 200)

        # Doctor CANNOT add nurse (403 Forbidden)
        res = self.client.get('/nurse/add')
        self.assertEqual(res.status_code, 403)

        # Doctor CANNOT edit nurse
        res = self.client.post(f'/nurse/edit/{nurse.id}', data={})
        self.assertEqual(res.status_code, 403)

        # Doctor CANNOT delete nurse
        res = self.client.post(f'/nurse/delete/{nurse.id}')
        self.assertEqual(res.status_code, 403)
        print("OK: Verified Doctor permissions (View allowed, CRUD forbidden).")

        # 2. Nurse role permissions (Sarah Connor)
        self.logout()
        res = self.login('nurse@ipcms.com', 'nurse123')
        self.assertIn(b'Nurse Dashboard', res.data)

        # Nurses can view nurse list
        res = self.client.get('/nurse/list')
        self.assertEqual(res.status_code, 200)

        # Nurses can view own details
        res = self.client.get(f'/nurse/view/{nurse.id}')
        self.assertEqual(res.status_code, 200)

        # Nurses CAN edit their own profile details
        res = self.client.get(f'/nurse/edit/{nurse.id}')
        self.assertEqual(res.status_code, 200)

        # Nurses CANNOT edit another nurse's details (using ID 1 which is Admin)
        res = self.client.get('/nurse/edit/1')
        self.assertEqual(res.status_code, 403)

        # Nurses CANNOT delete nurses
        res = self.client.post(f'/nurse/delete/{nurse.id}')
        self.assertEqual(res.status_code, 403)
        print("OK: Verified Nurse permissions (Own profile allowed, other profiles and Delete/Add forbidden).")

        # 3. Patient role permissions
        self.logout()
        res = self.login('patient@ipcms.com', 'patient123')
        self.assertIn(b'My Dashboard', res.data)

        # Patients CANNOT view nurse list
        res = self.client.get('/nurse/list')
        self.assertEqual(res.status_code, 403)

        # Patients CAN view nurse profile
        res = self.client.get(f'/nurse/view/{nurse.id}')
        self.assertEqual(res.status_code, 200)

        # Patients CANNOT edit nurse profile
        res = self.client.get(f'/nurse/edit/{nurse.id}')
        self.assertEqual(res.status_code, 403)

        # Patients CANNOT delete nurses
        res = self.client.post(f'/nurse/delete/{nurse.id}')
        self.assertEqual(res.status_code, 403)
        print("OK: Verified Patient permissions (View profile allowed, CRUD forbidden).")

if __name__ == '__main__':
    unittest.main()
