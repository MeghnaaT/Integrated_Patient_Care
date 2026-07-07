# =============================================================================
# forms/patient_form.py — Patient Add/Edit Form
# =============================================================================
# Uses Flask‑WTF and WTForms. Includes validation for required fields, length,
# regex for phone numbers, and a gender SelectField.
# =============================================================================

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp, NumberRange, Email, Optional


class PatientForm(FlaskForm):
    """Form for adding or editing a patient record."""

    first_name = StringField(
        "First Name",
        validators=[DataRequired(), Length(max=50)],
        render_kw={"placeholder": "John", "autofocus": True},
    )
    last_name = StringField(
        "Last Name",
        validators=[DataRequired(), Length(max=50)],
        render_kw={"placeholder": "Doe"},
    )
    age = IntegerField(
        "Age",
        validators=[DataRequired(), NumberRange(min=0, max=150)],
        render_kw={"placeholder": "30"},
    )
    gender = SelectField(
        "Gender",
        choices=[("Male", "Male"), ("Female", "Female"), ("Other", "Other")],
        validators=[DataRequired()],
    )
    blood_group = StringField(
        "Blood Group",
        validators=[Optional(), Length(max=10)],
        render_kw={"placeholder": "A+"},
    )
    phone_number = StringField(
        "Phone Number",
        validators=[
            DataRequired(),
            Regexp(r"^\+?[0-9]{7,15}$", message="Enter a valid phone number"),
        ],
        render_kw={"placeholder": "+1234567890"},
    )
    email = StringField(
        "Email",
        validators=[DataRequired(), Email(), Length(max=100)],
        render_kw={"placeholder": "john.doe@example.com"},
    )
    address = TextAreaField(
        "Address",
        validators=[DataRequired(), Length(max=250)],
        render_kw={"placeholder": "123 Main St, City, Country"},
    )
    emergency_contact_name = StringField(
        "Emergency Contact Name",
        validators=[Optional(), Length(max=100)],
    )
    emergency_contact_phone = StringField(
        "Emergency Contact Phone",
        validators=[
            Optional(),
            Regexp(r"^\+?[0-9]{7,15}$", message="Enter a valid phone number"),
        ],
    )
    submit = SubmitField("Save")
