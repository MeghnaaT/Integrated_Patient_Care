# =============================================================================
# forms/feedback_form.py — Patient Feedback & Rating Form
# =============================================================================

from flask_wtf import FlaskForm
from wtforms import SelectField, TextAreaField, HiddenField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional

class FeedbackForm(FlaskForm):
    """Form for patients to rate services and submit feedback."""
    service_type = SelectField(
        'Rating Category',
        choices=[
            ('Doctor Performance', 'Doctor Performance'),
            ('Hospital Service', 'Hospital Service'),
            ('Laboratory Service', 'Laboratory Service'),
            ('Pharmacy Service', 'Pharmacy Service')
        ],
        validators=[DataRequired()]
    )
    doctor_id = SelectField('Consulting Doctor', coerce=int, validators=[Optional()])
    department_id = SelectField('Department', coerce=int, validators=[Optional()])
    consultation_id = HiddenField('Consultation ID', validators=[Optional()])
    rating = SelectField(
        'Star Rating (1-5)',
        coerce=int,
        choices=[(5, '5 Stars - Excellent'), (4, '4 Stars - Good'), (3, '3 Stars - Average'), (2, '2 Stars - Poor'), (1, '1 Star - Very Poor')],
        validators=[DataRequired()]
    )
    comment = TextAreaField('Feedback & Comments', validators=[Optional()])
    submit = SubmitField('Submit Feedback')
