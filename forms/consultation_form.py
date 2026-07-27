# =============================================================================
# forms/consultation_form.py — Consultation WTForm
# =============================================================================

from flask_wtf import FlaskForm
from wtforms import SelectField, DateField, TextAreaField, SubmitField
from wtforms.validators import DataRequired

class ConsultationForm(FlaskForm):
    """Form for doctors to record patient consultations (matches Slide 15 mockup)."""
    patient_id = SelectField('Patient Name *', coerce=int, validators=[DataRequired()])
    doctor_id = SelectField('Doctor Name *', coerce=int, validators=[DataRequired()])
    consultation_date = DateField('Date of Consultation *', validators=[DataRequired()], format='%Y-%m-%d')
    symptoms = TextAreaField('Symptoms *', validators=[DataRequired()], render_kw={"placeholder": "e.g., Fever, Cough, Headache and Body Pain", "rows": 3})
    diagnosis = TextAreaField('Diagnosis *', validators=[DataRequired()], render_kw={"placeholder": "e.g., Viral Fever", "rows": 3})
    treatment_notes = TextAreaField('Treatment / Prescription *', validators=[DataRequired()], render_kw={"placeholder": "e.g., Paracetamol 500 mg - Twice a day. Drink plenty of water and take rest.", "rows": 3})
    submit = SubmitField('Save Consultation')
