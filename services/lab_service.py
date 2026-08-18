# =============================================================================
# services/lab_service.py — Laboratory Service Layer
# =============================================================================

from typing import List, Optional
from database.connection import db
from models.lab_report import LabReport

def create_lab_report(patient_id: int, doctor_id: int, test_name: str, test_date, result: str, remarks: Optional[str] = None) -> LabReport:
    """Create and persist a lab test report."""
    report = LabReport(
        patient_id=patient_id,
        doctor_id=doctor_id,
        test_name=test_name,
        test_date=test_date,
        result=result,
        remarks=remarks
    )
    db.session.add(report)

    # Trigger Lab Notification
    from services.notification_service import send_notification
    from models.doctor import Doctor
    doctor = db.session.get(Doctor, doctor_id)
    doc_info = f"Dr. {doctor.full_name}" if doctor else f"Doctor ID: {doctor_id}"
    date_str = test_date.strftime('%Y-%m-%d') if hasattr(test_date, 'strftime') else test_date
    msg = f"Your lab report for test '{test_name}' is available. Result: {result}. Date: {date_str}. Ordered by: {doc_info}."
    send_notification(patient_id, 'Lab Report', msg, commit=False)

    db.session.commit()
    return report

def get_lab_report_by_id(report_id: int) -> Optional[LabReport]:
    """Retrieve lab report by ID."""
    return db.session.get(LabReport, report_id)

def get_lab_reports_by_patient(patient_id: int) -> List[LabReport]:
    """Get all lab reports for a patient."""
    return LabReport.query.filter_by(patient_id=patient_id).order_by(LabReport.test_date.desc()).all()

def get_recent_lab_reports(limit: int = 10) -> List[LabReport]:
    """Get recent lab reports across the hospital."""
    return LabReport.query.order_by(LabReport.created_at.desc()).limit(limit).all()
