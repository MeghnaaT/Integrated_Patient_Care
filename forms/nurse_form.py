# =============================================================================
# forms/nurse_form.py — Nurse Add/Edit Form
# =============================================================================
# Uses Flask‑WTF and WTForms. Includes validation for required fields, length,
# email formats, contact phone numbers, and selection drop-downs.
# =============================================================================

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp, Email


class NurseForm(FlaskForm):
    """Form for adding or editing a nurse profile."""

    first_name = StringField(
        "First Name",
        validators=[DataRequired(), Length(max=50)],
        render_kw={"placeholder": "Sarah", "autofocus": True},
    )
    last_name = StringField(
        "Last Name",
        validators=[DataRequired(), Length(max=50)],
        render_kw={"placeholder": "Connor"},
    )
    department_id = SelectField(
        "Department",
        coerce=int,
        validators=[DataRequired()],
    )
    shift = SelectField(
        "Shift",
        choices=[("Morning", "Morning"), ("Evening", "Evening"), ("Night", "Night")],
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
    email = StringField(
        "Email Address",
        validators=[DataRequired(), Email(), Length(max=100)],
        render_kw={"placeholder": "sarah.connor@ipcms.com"},
    )
    submit = SubmitField("Save")
