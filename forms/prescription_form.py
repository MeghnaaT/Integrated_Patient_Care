# =============================================================================
# forms/prescription_form.py — Prescription WTForm
# =============================================================================

from flask_wtf import FlaskForm
from wtforms import SelectField, DateField, StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional

class PrescriptionForm(FlaskForm):
    """Form for doctors to prescribe digital medicines."""
    patient_id = SelectField('Patient Name *', coerce=int, validators=[DataRequired()])
    doctor_id = SelectField('Doctor Name *', coerce=int, validators=[DataRequired()])
    prescription_date = DateField('Prescription Date *', validators=[DataRequired()], format='%Y-%m-%d')
    special_instructions = TextAreaField('Special Instructions', validators=[Optional()], render_kw={"placeholder": "e.g., Take after food. Drink plenty of fluids.", "rows": 2})

    # Medicine Line Item 1
    medicine_name_1 = StringField('Medicine Name 1 *', validators=[DataRequired()], render_kw={"placeholder": "e.g. Paracetamol 500 mg"})
    dosage_1 = StringField('Dosage 1 *', validators=[DataRequired()], render_kw={"placeholder": "e.g. 500 mg"})
    frequency_1 = StringField('Frequency 1 *', validators=[DataRequired()], render_kw={"placeholder": "e.g. Twice a Day"})
    duration_1 = StringField('Duration 1 *', validators=[DataRequired()], render_kw={"placeholder": "e.g. 5 Days"})

    # Medicine Line Item 2 (Optional)
    medicine_name_2 = StringField('Medicine Name 2', validators=[Optional()], render_kw={"placeholder": "e.g. Cetirizine 10 mg"})
    dosage_2 = StringField('Dosage 2', validators=[Optional()], render_kw={"placeholder": "e.g. 10 mg"})
    frequency_2 = StringField('Frequency 2', validators=[Optional()], render_kw={"placeholder": "e.g. Once a Day"})
    duration_2 = StringField('Duration 2', validators=[Optional()], render_kw={"placeholder": "e.g. 3 Days"})

    submit = SubmitField('Save & Generate Prescription')
