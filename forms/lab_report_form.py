# =============================================================================
# forms/lab_report_form.py — Laboratory Test Form
# =============================================================================

from flask_wtf import FlaskForm
from wtforms import SelectField, DateField, StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional

TEST_TYPE_CHOICES = [
    ('Complete Blood Count', 'Complete Blood Count (CBC)'),
    ('Blood Sugar (Fasting)', 'Blood Sugar (Fasting)'),
    ('Lipid Profile', 'Lipid Profile'),
    ('Urine Routine', 'Urine Routine'),
    ('X-Ray Chest', 'X-Ray Chest'),
    ('MRI Brain', 'MRI Brain'),
    ('Liver Function Test', 'Liver Function Test'),
    ('Thyroid Profile', 'Thyroid Profile')
]

RESULT_CHOICES = [
    ('Normal', 'Normal'),
    ('Borderline', 'Borderline'),
    ('High', 'High'),
    ('Abnormal', 'Abnormal'),
    ('Pending', 'Pending')
]

class LabReportForm(FlaskForm):
    """Form for doctors/lab staff to record lab test requests and results."""
    patient_id = SelectField('Patient Name *', coerce=int, validators=[DataRequired()])
    doctor_id = SelectField('Doctor Name *', coerce=int, validators=[DataRequired()])
    test_name = SelectField('Laboratory Test Type *', choices=TEST_TYPE_CHOICES, validators=[DataRequired()])
    test_date = DateField('Test Date *', validators=[DataRequired()], format='%Y-%m-%d')
    result = SelectField('Laboratory Test Result *', choices=RESULT_CHOICES, default='Normal', validators=[DataRequired()])
    remarks = TextAreaField('Remarks / Observations', validators=[Optional()], render_kw={"placeholder": "Enter detailed test findings or observations...", "rows": 3})
    submit = SubmitField('Save Laboratory Report')
