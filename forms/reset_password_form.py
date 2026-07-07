# =============================================================================
# forms/reset_password_form.py — Reset Password WTForm
# =============================================================================
# Allows the user to set a new password after following a password‑reset link.
# Includes a confirmation field and a simple length validator.
# =============================================================================

from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo


class ResetPasswordForm(FlaskForm):
    """Form displayed on /auth/reset_password/<token>."""

    password = PasswordField(
        "New Password",
        validators=[
            DataRequired(message="Password is required."),
            Length(min=8, max=128, message="Password must be between 8 and 128 characters."),
        ],
        render_kw={"placeholder": "Enter new password"},
    )

    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[
            DataRequired(message="Please confirm your password."),
            EqualTo('password', message="Passwords must match."),
        ],
        render_kw={"placeholder": "Repeat new password"},
    )

    submit = SubmitField("Reset Password")
