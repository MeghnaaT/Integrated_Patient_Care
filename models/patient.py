from database.connection import db

class Patient(db.Model):
    __tablename__ = 'patients'

    # Sharing primary key with users table for direct 1-to-1 linkage
    id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.Enum('Male', 'Female', 'Other'), nullable=False)
    blood_group = db.Column(db.String(10), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    medical_history = db.Column(db.Text, nullable=True, default='No known allergies')
    registered_on = db.Column(db.Date, nullable=False)
    last_updated = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Database Check Constraint
    __table_args__ = (
        db.CheckConstraint('age >= 0 AND age <= 150', name='chk_patients_age'),
    )

    # Relationships
    # 1:1 relation with User
    user = db.relationship('User', back_populates='patient')
    
    # 1:N relations: A patient can have multiple appointments and medical history logs
    appointments = db.relationship('Appointment', back_populates='patient', cascade='all, delete-orphan')
    medical_records = db.relationship('MedicalRecord', back_populates='patient', cascade='all, delete-orphan')

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<Patient {self.full_name}>"
