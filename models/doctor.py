from database.connection import db

class Doctor(db.Model):
    __tablename__ = 'doctors'

    # Sharing primary key with users table for direct 1-to-1 linkage
    id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    qualification = db.Column(db.String(100), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    email_address = db.Column(db.String(100), nullable=False)
    available_time = db.Column(db.String(100), nullable=False)

    # Relationships
    # 1:1 relation with User
    user = db.relationship('User', back_populates='doctor')
    
    # N:1 relation: Multiple doctors belong to one department
    department = db.relationship('Department', back_populates='doctors')
    
    # 1:N relations: A doctor receives multiple appointments and logs multiple EHR consultations
    appointments = db.relationship('Appointment', back_populates='doctor', cascade='all, delete-orphan')
    medical_records = db.relationship('MedicalRecord', back_populates='doctor', cascade='all, delete-orphan')

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<Doctor {self.full_name} ({self.specialization})>"
