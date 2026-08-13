# =============================================================================
# models/pharmacy.py — Pharmacy & Medicine Models
# =============================================================================

from database.connection import db

class Medicine(db.Model):
    __tablename__ = 'medicines'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    medicine_code = db.Column(db.String(50), nullable=False, unique=True)
    medicine_name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), nullable=False) # Tablet, Capsule, Syrup, etc.
    manufacturer = db.Column(db.String(100), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum('Available', 'Low Stock', 'Expired'), nullable=False, default='Available')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f"<Medicine code={self.medicine_code} name={self.medicine_name} stock={self.stock}>"


class MedicineDispensation(db.Model):
    __tablename__ = 'medicine_dispensations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prescription_id = db.Column(db.Integer, nullable=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    dispensed_by = db.Column(db.Integer, nullable=True)
    dispensed_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationships
    patient = db.relationship('Patient', backref=db.backref('dispensations', cascade='all, delete-orphan'))
    medicine = db.relationship('Medicine', backref='dispensations')

    def __repr__(self):
        return f"<MedicineDispensation patient_id={self.patient_id} medicine_id={self.medicine_id} qty={self.quantity}>"
