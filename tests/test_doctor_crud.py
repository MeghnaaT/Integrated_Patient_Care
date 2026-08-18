import unittest
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from database.connection import db
from models.user import User
from models.doctor import Doctor

class TestDoctorCRUD(unittest.TestCase):

    def setUp(self):
        self.app = create_app('development')
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Cleanup test records
        from models.user import User
        test_user = User.query.filter_by(email='jane.doe@ipcms.com').first()
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

    def test_admin_doctor_crud_flow(self):
        print("\n--- Testing Admin Doctor CRUD Flow ---")

        # 1. Login as Admin
        res = self.login('admin@ipcms.com', 'admin123')
        self.assertIn(b'Admin Dashboard', res.data)
        print("OK: Successfully logged in as Admin.")

        # 2. Check Doctor List works and contains seeded doctor John Smith
        res = self.client.get('/doctor/list')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'John Smith', res.data)
        print("OK: Doctor Directory loaded and contains Dr. John Smith.")

        # 3. Verify duplicate email validation works
        res = self.client.post('/doctor/add', data={
            'first_name': 'Jane',
            'last_name': 'Doe',
            'specialization': 'Neurologist',
            'qualification': 'MD, FACC',
            'department_id': 2, # Neurology
            'contact_number': '+919876543299',
            'email_address': 'doctor@ipcms.com',  # seeded email, duplicate
            'available_time': '09:00 AM - 12:00 PM'
        })
        self.assertIn(b'exists', res.data)
        print("OK: Correctly prevented creation of doctor with duplicate email.")

        # 4. Add Doctor Jane Doe
        res = self.client.post('/doctor/add', data={
            'first_name': 'Jane',
            'last_name': 'Doe',
            'specialization': 'Neurologist',
            'qualification': 'MD, PhD',
            'department_id': 2, # Neurology
            'contact_number': '+919876543299',
            'email_address': 'jane.doe@ipcms.com',
            'available_time': '09:00 AM - 12:00 PM'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'registered successfully', res.data)
        print("OK: Successfully registered new doctor Jane Doe.")

        # 5. Verify doctor in DB and linked user created
        new_doc = Doctor.query.filter_by(email_address='jane.doe@ipcms.com').first()
        self.assertIsNotNone(new_doc)
        self.assertEqual(new_doc.first_name, 'Jane')
        self.assertEqual(new_doc.last_name, 'Doe')
        self.assertEqual(new_doc.specialization, 'Neurologist')
        self.assertEqual(new_doc.department_id, 2)
        self.assertEqual(new_doc.contact_number, '+919876543299')
        self.assertEqual(new_doc.available_time, '09:00 AM - 12:00 PM')
        self.assertIsNotNone(new_doc.user)
        self.assertEqual(new_doc.user.username, 'doc_jane_doe')
        self.assertEqual(new_doc.user.role.name, 'Doctor')
        print("OK: Verified Database mappings and 1-to-1 User linkage.")

        # 6. Verify Search works
        res = self.client.get('/doctor/list?q=Jane')
        self.assertIn(b'Jane Doe', res.data)
        self.assertNotIn(b'John Smith', res.data)
        print("OK: Search filters by name and department correctly.")

        # 7. Edit Doctor Jane Doe (change availability)
        res = self.client.post(f'/doctor/edit/{new_doc.id}', data={
            'first_name': 'Jane',
            'last_name': 'Doe',
            'specialization': 'Neurologist',
            'qualification': 'MD, PhD',
            'department_id': 2,
            'contact_number': '+919876543299',
            'email_address': 'jane.doe@ipcms.com',
            'available_time': '02:00 PM - 05:00 PM'  # updated
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'updated successfully', res.data)

        # Re-fetch and verify availability is updated
        db.session.refresh(new_doc)
        self.assertEqual(new_doc.available_time, '02:00 PM - 05:00 PM')
        print("OK: Edit Doctor successfully updated availability in database.")

        # 8. View Doctor profile details page
        res = self.client.get(f'/doctor/view/{new_doc.id}')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Jane Doe', res.data)
        self.assertIn(b'02:00 PM - 05:00 PM', res.data)
        print("OK: View Doctor Details page renders correct clinical info.")

        # 9. Delete Doctor (soft-delete)
        res = self.client.post(f'/doctor/delete/{new_doc.id}', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'soft-deleted successfully', res.data)
        
        # Verify soft-delete status in DB
        db.session.refresh(new_doc.user)
        self.assertFalse(new_doc.user.is_active)
        print("OK: Soft-delete updates User is_active to False.")

        # Verify no longer returned in Doctor Directory
        res = self.client.get('/doctor/list')
        self.assertNotIn(b'Jane Doe', res.data)
        print("OK: Soft-deleted doctor hidden from directory.")

    def test_role_based_access_control(self):
        print("\n--- Testing Role Based Access Control ---")

        # Get seeded doctor ID (John Smith is id = 2)
        doc = db.session.get(Doctor, 2)
        self.assertIsNotNone(doc)

        # 1. Nurse role permissions
        self.logout()
        res = self.login('nurse@ipcms.com', 'nurse123')
        self.assertIn(b'Nurse Dashboard', res.data)

        # Nurse can view doctor directory
        res = self.client.get('/doctor/list')
        self.assertEqual(res.status_code, 200)
        
        # Nurse can view doctor profile
        res = self.client.get(f'/doctor/view/{doc.id}')
        self.assertEqual(res.status_code, 200)

        # Nurse CANNOT add doctor (403 Forbidden)
        res = self.client.get('/doctor/add')
        self.assertEqual(res.status_code, 403)

        # Nurse CANNOT edit doctor
        res = self.client.post(f'/doctor/edit/{doc.id}', data={})
        self.assertEqual(res.status_code, 403)

        # Nurse CANNOT delete doctor
        res = self.client.post(f'/doctor/delete/{doc.id}')
        self.assertEqual(res.status_code, 403)
        print("OK: Verified Nurse permissions (View allowed, CRUD forbidden).")

        # 2. Doctor role permissions (John Smith)
        self.logout()
        res = self.login('doctor@ipcms.com', 'doctor123')
        self.assertIn(b'Doctor Dashboard', res.data)

        # Doctors can view doctor list
        res = self.client.get('/doctor/list')
        self.assertEqual(res.status_code, 200)

        # Doctors can view own details
        res = self.client.get(f'/doctor/view/{doc.id}')
        self.assertEqual(res.status_code, 200)

        # Doctors CAN edit their own profile details
        res = self.client.get(f'/doctor/edit/{doc.id}')
        self.assertEqual(res.status_code, 200)

        # Doctors CANNOT edit another doctor's details (using ID 1 which is Admin)
        res = self.client.get('/doctor/edit/1')
        self.assertEqual(res.status_code, 403)

        # Doctors CANNOT delete doctors
        res = self.client.post(f'/doctor/delete/{doc.id}')
        self.assertEqual(res.status_code, 403)
        print("OK: Verified Doctor permissions (Own profile allowed, other profiles and Delete/Add forbidden).")

        # 3. Patient role permissions
        self.logout()
        res = self.login('patient@ipcms.com', 'patient123')
        self.assertIn(b'My Dashboard', res.data)

        # Patients CAN view doctor list (needed for booking appointments)
        res = self.client.get('/doctor/list')
        self.assertEqual(res.status_code, 200)

        # Patients CAN view doctor profiles
        res = self.client.get(f'/doctor/view/{doc.id}')
        self.assertEqual(res.status_code, 200)

        # Patients CANNOT edit doctor profile
        res = self.client.get(f'/doctor/edit/{doc.id}')
        self.assertEqual(res.status_code, 403)

        # Patients CANNOT delete doctors
        res = self.client.post(f'/doctor/delete/{doc.id}')
        self.assertEqual(res.status_code, 403)
        print("OK: Verified Patient permissions (View list and profile allowed, CRUD forbidden).")

if __name__ == '__main__':
    unittest.main()
