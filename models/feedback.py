# =============================================================================
# models/feedback.py — Patient Feedback & Satisfaction Model
# =============================================================================

import datetime
from database.connection import db

class Feedback(db.Model):
    __tablename__ = 'feedbacks'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    feedback_code = db.Column(db.String(50), nullable=False, unique=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    consultation_id = db.Column(db.Integer, db.ForeignKey('consultations.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    
    service_type = db.Column(
        db.Enum('Doctor Performance', 'Hospital Service', 'Laboratory Service', 'Pharmacy Service'),
        nullable=False,
        default='Doctor Performance'
    )
    rating = db.Column(db.Integer, nullable=False)  # 1 to 5 stars
    comment = db.Column(db.Text, nullable=True)
    status = db.Column(db.Enum('Published', 'Pending', 'Reviewed'), nullable=False, default='Published')
    created_date = db.Column(db.Date, default=datetime.date.today, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationships
    patient = db.relationship('Patient', backref=db.backref('feedbacks', cascade='all, delete-orphan'))
    doctor = db.relationship('Doctor', backref=db.backref('feedbacks', lazy=True))
    department = db.relationship('Department', backref=db.backref('feedbacks', lazy=True))
    consultation = db.relationship('Consultation', backref=db.backref('feedbacks', lazy=True))

    def __repr__(self):
        return f"<Feedback code={self.feedback_code} rating={self.rating} service={self.service_type}>"
