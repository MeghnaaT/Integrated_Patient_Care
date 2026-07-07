# =============================================================================
# forms/forgot_password_form.py — Forgot Password WTForm
# =============================================================================
# Simple form that asks for the user's email address. Validation checks that the
# field contains a syntactically valid email. We do NOT reveal whether the email
# exists in the system – the route handles that securely.
# =============================================================================

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length


class ForgotPasswordForm(FlaskForm):
    """Form displayed on /auth/forgot_password."""

    email = StringField(
        "Email Address",
        validators=[
            DataRequired(message="Email is required."),
            Email(message="Enter a valid email address."),
            Length(max=100, message="Email must be under 100 characters."),
        ],
        render_kw={"placeholder": "you@example.com", "autofocus": True},
    )

    submit = SubmitField("Send Reset Link")
