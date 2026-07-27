# =============================================================================
# models/prescription.py — Prescription and PrescriptionItem Models
# =============================================================================

from database.connection import db

class Prescription(db.Model):
    __tablename__ = 'prescriptions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    consultation_id = db.Column(db.Integer, db.ForeignKey('consultations.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    prescription_date = db.Column(db.Date, nullable=False)
    special_instructions = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationships
    patient = db.relationship('Patient', backref=db.backref('prescriptions', cascade='all, delete-orphan', lazy=True))
    doctor = db.relationship('Doctor', backref=db.backref('prescriptions', cascade='all, delete-orphan', lazy=True))
    items = db.relationship('PrescriptionItem', backref='prescription', cascade='all, delete-orphan', lazy=True)

    def __repr__(self):
        return f"<Prescription id={self.id} patient_id={self.patient_id} date={self.prescription_date}>"


class PrescriptionItem(db.Model):
    __tablename__ = 'prescription_items'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    medicine_name = db.Column(db.String(150), nullable=False)
    dosage = db.Column(db.String(100), nullable=False)
    frequency = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<PrescriptionItem medicine={self.medicine_name} dosage={self.dosage}>"
