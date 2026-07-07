from database.connection import db

class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationships
    # One Department can have Many Doctors or Nurses
    doctors = db.relationship('Doctor', back_populates='department', cascade='all, delete-orphan')
    nurses = db.relationship('Nurse', back_populates='department', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Department {self.name}>"
