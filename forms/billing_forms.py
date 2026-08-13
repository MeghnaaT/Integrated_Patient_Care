# =============================================================================
# forms/billing_forms.py — Billing & Payment WTForms
# =============================================================================

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DecimalField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange

class PatientBillingForm(FlaskForm):
    """Form to generate a new patient bill."""
    patient_id = StringField('Patient ID / Search', validators=[DataRequired()], render_kw={"placeholder": "Enter Patient ID e.g., P1001 or 4"})
    payment_method = SelectField('Payment Method', choices=[
        ('UPI', 'UPI'),
        ('Card', 'Credit / Debit Card'),
        ('Cash', 'Cash'),
        ('Insurance', 'Health Insurance')
    ], default='UPI')
    transaction_id = StringField('Transaction ID', validators=[Optional()], render_kw={"placeholder": "e.g., UPI1234567890"})
    discount = DecimalField('Discount (₹)', validators=[Optional(), NumberRange(min=0)], default=0.00)
    tax_amount = DecimalField('Tax Amount (₹)', validators=[Optional(), NumberRange(min=0)], default=0.00)
    submit = SubmitField('Record Payment & Print Invoice')
