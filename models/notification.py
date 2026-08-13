# =============================================================================
# models/notification.py — Notification Model
# =============================================================================

from database.connection import db

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    notification_code = db.Column(db.String(50), nullable=False, unique=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    user_id = db.Column(db.Integer, nullable=True)
    type = db.Column(db.Enum('Appointment Reminder', 'Lab Report', 'Prescription Ready', 'Billing Reminder', 'General Info'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date_time = db.Column(db.DateTime, default=db.func.current_timestamp())
    delivery_method = db.Column(db.Enum('In-App', 'SMS', 'Email'), nullable=False, default='In-App')
    status = db.Column(db.Enum('Delivered', 'Failed', 'Read'), nullable=False, default='Delivered')
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationships
    patient = db.relationship('Patient', backref=db.backref('notifications', cascade='all, delete-orphan'))

    def __repr__(self):
        return f"<Notification code={self.notification_code} type={self.type} status={self.status}>"
