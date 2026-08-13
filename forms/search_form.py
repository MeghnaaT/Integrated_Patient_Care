# =============================================================================
# forms/search_form.py — Patient Search & Reports Form
# =============================================================================

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import Optional

class PatientSearchForm(FlaskForm):
    """Form for searching patient records by Patient ID or Name."""
    search_by = SelectField('Search By', choices=[('patient_id', 'Patient ID'), ('name', 'Patient Name')], default='patient_id')
    query = StringField('Search Query', validators=[Optional()], render_kw={"placeholder": "e.g., PAT1001 or Rahul Kumar"})
    submit = SubmitField('Search')


class AdvancedPatientSearchForm(FlaskForm):
    """Form for Day 1 Advanced Patient Search (Search by ID, Name, Phone, Aadhaar, Email)."""
    search_criteria = SelectField('Search Field', choices=[
        ('all', 'All Fields'),
        ('patient_id', 'Patient ID'),
        ('name', 'Patient Name'),
        ('phone', 'Phone Number'),
        ('aadhaar', 'Aadhaar Number'),
        ('email', 'Email ID')
    ], default='all')
    query = StringField('Search Query', validators=[Optional()], render_kw={"placeholder": "Enter Patient ID, Name, Phone, Aadhaar or Email..."})
    submit = SubmitField('Search Patients')
