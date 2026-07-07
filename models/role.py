from database.connection import db

class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationships
    # One Role can be assigned to Many Users
    users = db.relationship('User', back_populates='role', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Role {self.name}>"
