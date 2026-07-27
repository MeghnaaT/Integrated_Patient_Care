# =============================================================================
# forms/ehr_forms.py — EHR Detail, Allergy, and Active Medication WTForms
# =============================================================================

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DecimalField, SelectField, TextAreaField, DateField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange, Length

class EHRDetailForm(FlaskForm):
    """Form for adding or editing a patient's EHR vitals & lifestyle summary."""
    height = IntegerField('Height (cm)', validators=[Optional(), NumberRange(min=30, max=250)], render_kw={"placeholder": "175"})
    weight = IntegerField('Weight (kg)', validators=[Optional(), NumberRange(min=2, max=300)], render_kw={"placeholder": "72"})
    bmi = DecimalField('BMI', places=1, validators=[Optional(), NumberRange(min=5.0, max=80.0)], render_kw={"placeholder": "23.5"})
    smoking_status = SelectField('Smoking Status', choices=[('No', 'No'), ('Occasional', 'Occasional'), ('Regular', 'Regular'), ('Former', 'Former')], default='No')
    alcohol_status = SelectField('Alcohol Status', choices=[('No', 'No'), ('Occasional', 'Occasional'), ('Regular', 'Regular')], default='No')
    chronic_diseases = StringField('Chronic Diseases', validators=[Optional(), Length(max=255)], render_kw={"placeholder": "e.g. No, Hypertension, Diabetes"})
    remarks = TextAreaField('Remarks / Observations', validators=[Optional()], render_kw={"placeholder": "Patient health summary...", "rows": 3})
    submit = SubmitField('Save EHR Vitals')


class AllergyForm(FlaskForm):
    """Form for adding a new patient allergy entry."""
    allergen = StringField('Allergen', validators=[DataRequired(), Length(max=100)], render_kw={"placeholder": "e.g. Penicillin, Peanuts"})
    reaction = StringField('Reaction', validators=[DataRequired(), Length(max=255)], render_kw={"placeholder": "e.g. Rash, Anaphylaxis"})
    added_on = DateField('Added On Date', validators=[DataRequired()], format='%Y-%m-%d')
    submit = SubmitField('Add Allergy')


class PatientMedicationForm(FlaskForm):
    """Form for adding active current medications."""
    medicine = StringField('Medicine Name', validators=[DataRequired(), Length(max=150)], render_kw={"placeholder": "e.g. Paracetamol 500mg"})
    dosage = StringField('Dosage', validators=[DataRequired(), Length(max=100)], render_kw={"placeholder": "e.g. 500 mg"})
    frequency = StringField('Frequency', validators=[DataRequired(), Length(max=100)], render_kw={"placeholder": "e.g. Twice a day"})
    start_date = DateField('Start Date', validators=[DataRequired()], format='%Y-%m-%d')
    submit = SubmitField('Add Medication')
