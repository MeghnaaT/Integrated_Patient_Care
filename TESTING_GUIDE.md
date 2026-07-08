# Testing Guide — IPCMS

This document provides a guide on how to run automated unit and integration tests for the **Integrated Patient Care Management System (IPCMS)**.

---

## 1. Test Architecture

The IPCMS test suite is written using Python's standard `unittest` library. The tests are located in the [tests/](file:///d:/Meghna/Integrated_Patient_Care/tests) folder:

* [test_patient_crud.py](file:///d:/Meghna/Integrated_Patient_Care/tests/test_patient_crud.py): Tests patient demographic creation, user credentials syncing, searching, pagination, duplicate validation, and patient RBAC constraints.
* [test_doctor_crud.py](file:///d:/Meghna/Integrated_Patient_Care/tests/test_doctor_crud.py): Tests doctor clinical profiles, department links, available time validation, soft deletions, and doctor RBAC constraints.
* [test_nurse_crud.py](file:///d:/Meghna/Integrated_Patient_Care/tests/test_nurse_crud.py): Tests nurse credentials syncing, custom shift column configurations, and nurse RBAC constraints.
* [test_appointment_crud.py](file:///d:/Meghna/Integrated_Patient_Care/tests/test_appointment_crud.py): Tests appointment slots bookings, overlap collisions checks, past date boundaries, rescheduled bookings, and schedule timetables.
* [test_dashboards.py](file:///d:/Meghna/Integrated_Patient_Care/tests/test_dashboards.py): Validates Admin, Doctor, Nurse, and Patient dashboard statistic metrics and ChartJS components.

---

## 2. Running the Tests

Ensure your virtual environment is active:
```powershell
.venv\Scripts\activate
```

### Run All Tests
Execute Python's unittest discovery engine from the project root:
```powershell
python -m unittest discover -s tests -p "test_*.py"
```

### Run a Specific Module Test
To run a single test module, specify the module path:
```powershell
python -m unittest tests.test_appointment_crud
```

### Run a Specific Test Method
To execute a single test case within a module:
```powershell
python -m unittest tests.test_appointment_crud.TestAppointmentCRUD.test_admin_appointment_crud_flow
```

---

## 3. Test Isolation Design

To prevent conflicts and duplicate email violations between runs, the tests use:
* **Transactions rollback:** SQLAlchemy sessions rollback any local edits at teardown.
* **Proactive cleanup in `setUp`:** Each test module executes a deletion query at setup targeting its specific test emails (`jane.doe@ipcms.com`, `ellen.ripley@ipcms.com`, `ramesh.sinha@ipcms.com`) and test bookings (patient 4 / doctor 2). This ensures tests can run continuously and independently.
