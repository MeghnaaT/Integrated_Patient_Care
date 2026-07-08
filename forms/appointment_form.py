# =============================================================================
# forms/appointment_form.py — Appointment Book/Edit Form
# =============================================================================
# Uses Flask‑WTF and WTForms. Includes fields for patient, doctor, date, time,
# and status, along with validators.
# =============================================================================

from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.fields import DateField, TimeField
from wtforms.validators import DataRequired, Optional


class AppointmentForm(FlaskForm):
    """Form for booking or rescheduling an appointment."""

    patient_id = SelectField(
        "Patient Name",
        coerce=int,
        validators=[Optional()],
        description="Omit if booking for self",
    )
    doctor_id = SelectField(
        "Consulting Doctor",
        coerce=int,
        validators=[DataRequired()],
    )
    appointment_date = DateField(
        "Appointment Date",
        validators=[DataRequired()],
    )
    appointment_time = TimeField(
        "Appointment Time",
        validators=[DataRequired()],
    )
    status = SelectField(
        "Appointment Status",
        choices=[
            ("Pending", "Pending"),
            ("Confirmed", "Confirmed"),
            ("Completed", "Completed"),
            ("Cancelled", "Cancelled"),
        ],
        validators=[Optional()],
    )
    submit = SubmitField("Save Appointment")
