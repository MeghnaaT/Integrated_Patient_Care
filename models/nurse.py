from database.connection import db

class Nurse(db.Model):
    __tablename__ = 'nurses'

    # Sharing primary key with users table for direct 1-to-1 linkage
    id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    shift = db.Column(db.Enum('Morning', 'Evening', 'Night'), nullable=False, default='Morning')

    # Relationships
    # 1:1 relation with User
    user = db.relationship('User', back_populates='nurse')
    
    # N:1 relation: Multiple nurses belong to one department
    department = db.relationship('Department', back_populates='nurses')

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<Nurse {self.full_name}>"
