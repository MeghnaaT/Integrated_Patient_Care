# =============================================================================
# models/consultation.py — Consultation Model
# =============================================================================

from database.connection import db

class Consultation(db.Model):
    __tablename__ = 'consultations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    consultation_date = db.Column(db.Date, nullable=False)
    symptoms = db.Column(db.Text, nullable=False)
    diagnosis = db.Column(db.Text, nullable=False)
    treatment_notes = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationships
    patient = db.relationship('Patient', backref=db.backref('consultations', cascade='all, delete-orphan', lazy=True))
    doctor = db.relationship('Doctor', backref=db.backref('consultations', cascade='all, delete-orphan', lazy=True))
    prescription = db.relationship('Prescription', backref='consultation', uselist=False, lazy=True)

    def __repr__(self):
        return f"<Consultation id={self.id} patient_id={self.patient_id} diagnosis={self.diagnosis}>"
