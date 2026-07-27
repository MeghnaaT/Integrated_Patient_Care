# =============================================================================
# models/ehr_detail.py — EHR Detail, Allergy, and PatientMedication Models
# =============================================================================

from database.connection import db

class EHRDetail(db.Model):
    __tablename__ = 'ehr_details'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, unique=True)
    height = db.Column(db.Integer, nullable=True) # cm
    weight = db.Column(db.Integer, nullable=True) # kg
    bmi = db.Column(db.Numeric(4, 1), nullable=True)
    smoking_status = db.Column(db.String(50), nullable=True, default='No')
    alcohol_status = db.Column(db.String(50), nullable=True, default='No')
    chronic_diseases = db.Column(db.String(255), nullable=True, default='No')
    remarks = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Relationship to Patient
    patient = db.relationship('Patient', backref=db.backref('ehr_detail', uselist=False, cascade='all, delete-orphan'))

    def __repr__(self):
        return f"<EHRDetail patient_id={self.patient_id} bmi={self.bmi}>"


class Allergy(db.Model):
    __tablename__ = 'allergies'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    allergen = db.Column(db.String(100), nullable=False)
    reaction = db.Column(db.String(255), nullable=False)
    added_on = db.Column(db.Date, nullable=False)

    # Relationship to Patient
    patient = db.relationship('Patient', backref=db.backref('allergies', cascade='all, delete-orphan'))

    def __repr__(self):
        return f"<Allergy patient_id={self.patient_id} allergen={self.allergen}>"


class PatientMedication(db.Model):
    __tablename__ = 'patient_medications'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    medicine = db.Column(db.String(150), nullable=False)
    dosage = db.Column(db.String(100), nullable=False)
    frequency = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)

    # Relationship to Patient
    patient = db.relationship('Patient', backref=db.backref('current_medications', cascade='all, delete-orphan'))

    def __repr__(self):
        return f"<PatientMedication patient_id={self.patient_id} medicine={self.medicine}>"
