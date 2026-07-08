# =============================================================================
# forms/doctor_form.py — Doctor Add/Edit Form
# =============================================================================
# Uses Flask‑WTF and WTForms. Includes validation for required fields, length,
# email format, contact phone regex, and a dynamically choices-populated
# department selection.
# =============================================================================

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp, Email


class DoctorForm(FlaskForm):
    """Form for adding or editing a doctor profile."""

    first_name = StringField(
        "First Name",
        validators=[DataRequired(), Length(max=50)],
        render_kw={"placeholder": "Jane", "autofocus": True},
    )
    last_name = StringField(
        "Last Name",
        validators=[DataRequired(), Length(max=50)],
        render_kw={"placeholder": "Doe"},
    )
    specialization = StringField(
        "Specialization",
        validators=[DataRequired(), Length(max=100)],
        render_kw={"placeholder": "Cardiologist"},
    )
    qualification = StringField(
        "Qualification",
        validators=[DataRequired(), Length(max=100)],
        render_kw={"placeholder": "MD, FACC"},
    )
    department_id = SelectField(
        "Department",
        coerce=int,
        validators=[DataRequired()],
    )
    contact_number = StringField(
        "Contact Number",
        validators=[
            DataRequired(),
            Regexp(r"^\+?[0-9]{7,15}$", message="Enter a valid contact number"),
        ],
        render_kw={"placeholder": "+1234567890"},
    )
    email_address = StringField(
        "Email Address",
        validators=[DataRequired(), Email(), Length(max=100)],
        render_kw={"placeholder": "jane.doe@ipcms.com"},
    )
    available_time = StringField(
        "Available Time",
        validators=[DataRequired(), Length(max=100)],
        render_kw={"placeholder": "10:00 AM - 01:00 PM"},
    )
    submit = SubmitField("Save")
