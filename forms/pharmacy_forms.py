# =============================================================================
# forms/pharmacy_forms.py — Pharmacy WTForms
# =============================================================================

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, DecimalField, DateField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional

class MedicineForm(FlaskForm):
    """Form to add or edit a medicine in pharmacy inventory."""
    medicine_code = StringField('Medicine Code', validators=[DataRequired()], render_kw={"placeholder": "e.g., MED106"})
    medicine_name = StringField('Medicine Name', validators=[DataRequired()], render_kw={"placeholder": "e.g., Paracetamol 500 mg"})
    category = SelectField('Category', choices=[
        ('Tablet', 'Tablet'),
        ('Capsule', 'Capsule'),
        ('Syrup', 'Syrup'),
        ('Injection', 'Injection'),
        ('Ointment', 'Ointment'),
        ('Drops', 'Drops')
    ], validators=[DataRequired()])
    manufacturer = StringField('Manufacturer', validators=[DataRequired()], render_kw={"placeholder": "e.g., ABC Pharma Ltd."})
    stock = IntegerField('Initial Stock', validators=[DataRequired(), NumberRange(min=0)], default=100)
    unit_price = DecimalField('Unit Price (₹)', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    expiry_date = DateField('Expiry Date', validators=[DataRequired()], format='%Y-%m-%d')
    submit = SubmitField('Save Medicine')


class StockUpdateForm(FlaskForm):
    """Form for quick stock level updates."""
    stock = IntegerField('New Stock Quantity', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Update Stock')


class DispenseMedicineForm(FlaskForm):
    """Form to dispense medicines according to digital prescriptions."""
    prescription_code = StringField('Prescription ID', validators=[Optional()], render_kw={"placeholder": "e.g., PRS1005"})
    patient_id = IntegerField('Patient ID', validators=[DataRequired()])
    medicine_id = SelectField('Select Medicine', coerce=int, validators=[DataRequired()])
    quantity = IntegerField('Quantity to Dispense', validators=[DataRequired(), NumberRange(min=1)], default=1)
    submit = SubmitField('Dispense Medicine')
