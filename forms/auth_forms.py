# =============================================================================
# forms/auth_forms.py — Authentication WTForms
# =============================================================================
# LoginForm    — email + password + remember_me
# RegisterForm — username + email + password + confirm password
#
# All forms include the hidden CSRF token automatically via Flask-WTF.
# =============================================================================

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, Regexp, ValidationError
)


class LoginForm(FlaskForm):
    """Form displayed on /auth/login."""

    email = StringField(
        'Email Address',
        validators=[
            DataRequired(message='Email is required.'),
            Email(message='Please enter a valid email address.'),
            Length(max=100, message='Email must be under 100 characters.'),
        ],
        render_kw={'placeholder': 'you@example.com', 'autofocus': True},
    )

    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required.'),
            Length(min=6, max=128, message='Password must be between 6 and 128 characters.'),
        ],
        render_kw={'placeholder': '••••••••'},
    )

    remember_me = BooleanField('Keep me signed in')

    submit = SubmitField('Sign In')


class RegisterForm(FlaskForm):
    """Form displayed on /auth/register (self-registration as Patient)."""

    username = StringField(
        'Username',
        validators=[
            DataRequired(message='Username is required.'),
            Length(min=3, max=50, message='Username must be 3–50 characters.'),
            Regexp(
                r'^[\w.-]+$',
                message='Username may only contain letters, numbers, dots, hyphens, and underscores.',
            ),
        ],
        render_kw={'placeholder': 'john_doe'},
    )

    email = StringField(
        'Email Address',
        validators=[
            DataRequired(message='Email is required.'),
            Email(message='Please enter a valid email address.'),
            Length(max=100, message='Email must be under 100 characters.'),
        ],
        render_kw={'placeholder': 'you@example.com'},
    )

    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required.'),
            Length(min=8, max=128, message='Password must be at least 8 characters.'),
        ],
        render_kw={'placeholder': 'Minimum 8 characters'},
    )

    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(message='Please confirm your password.'),
            EqualTo('password', message='Passwords must match.'),
        ],
        render_kw={'placeholder': 'Repeat password'},
    )

    submit = SubmitField('Create Account')
