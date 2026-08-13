# =============================================================================
# models/billing.py — Billing & Invoice Models
# =============================================================================

from database.connection import db

class Bill(db.Model):
    __tablename__ = 'bills'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bill_number = db.Column(db.String(50), nullable=False, unique=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    consultation_id = db.Column(db.Integer, nullable=True)
    total_consultation_fee = db.Column(db.Numeric(10, 2), default=0.00)
    total_lab_fee = db.Column(db.Numeric(10, 2), default=0.00)
    total_pharmacy_fee = db.Column(db.Numeric(10, 2), default=0.00)
    other_charges = db.Column(db.Numeric(10, 2), default=0.00)
    sub_total = db.Column(db.Numeric(10, 2), nullable=False)
    discount = db.Column(db.Numeric(10, 2), default=0.00)
    tax_amount = db.Column(db.Numeric(10, 2), default=0.00)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.Enum('UPI', 'Card', 'Cash', 'Insurance'), nullable=False, default='UPI')
    transaction_id = db.Column(db.String(100), nullable=True)
    payment_status = db.Column(db.Enum('Paid', 'Unpaid', 'Pending'), nullable=False, default='Paid')
    bill_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationships
    patient = db.relationship('Patient', backref=db.backref('bills', cascade='all, delete-orphan'))
    items = db.relationship('BillItem', backref='bill', cascade='all, delete-orphan', lazy=True)

    def __repr__(self):
        return f"<Bill number={self.bill_number} amount={self.total_amount} status={self.payment_status}>"


class BillItem(db.Model):
    __tablename__ = 'bill_items'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bill_id = db.Column(db.Integer, db.ForeignKey('bills.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    service_type = db.Column(db.Enum('Consultation', 'Laboratory', 'Pharmacy', 'Other'), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    reference_id = db.Column(db.String(50), nullable=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)

    def __repr__(self):
        return f"<BillItem service={self.service_type} amount={self.amount}>"
