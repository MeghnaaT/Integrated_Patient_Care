from database.connection import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Relationships
    role = db.relationship('Role', back_populates='users')
    
    # One-to-One: A user might have a related Patient, Doctor, or Nurse record
    patient = db.relationship('Patient', back_populates='user', uselist=False, cascade='all, delete-orphan')
    doctor = db.relationship('Doctor', back_populates='user', uselist=False, cascade='all, delete-orphan')
    nurse = db.relationship('Nurse', back_populates='user', uselist=False, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<User {self.username} ({self.email})>"
