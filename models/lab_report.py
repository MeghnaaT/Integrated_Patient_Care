# =============================================================================
# models/lab_report.py — LabReport Model
# =============================================================================

from database.connection import db

class LabReport(db.Model):
    __tablename__ = 'lab_reports'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    test_name = db.Column(db.String(150), nullable=False)
    test_date = db.Column(db.Date, nullable=False)
    result = db.Column(db.String(255), nullable=False) # e.g. Normal, Borderline, High, etc.
    remarks = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationships
    patient = db.relationship('Patient', backref=db.backref('lab_reports', cascade='all, delete-orphan', lazy=True))
    doctor = db.relationship('Doctor', backref=db.backref('lab_reports', cascade='all, delete-orphan', lazy=True))

    def __repr__(self):
        return f"<LabReport id={self.id} test={self.test_name} result={self.result}>"
