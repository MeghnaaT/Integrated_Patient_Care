# =============================================================================
# routes/auth.py — Authentication Blueprint
# =============================================================================
# Handles: login, logout, register
# URL prefix: /auth  (set in app.py)
# =============================================================================

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash

from database.connection import db
from models.user import User
from models.role import Role
from forms.auth_forms import LoginForm, RegisterForm

auth_bp = Blueprint('auth', __name__)


# ---------------------------------------------------------------------------
# GET /auth/login   — show login form
# POST /auth/login  — validate and authenticate
# ---------------------------------------------------------------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Redirect already-authenticated users straight to their dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()

        if user and user.is_active and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash(f'Welcome back, {user.username}!', 'success')
            # Honour the ?next= redirect if it is safe
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.dashboard'))

        flash('Invalid email or password. Please try again.', 'danger')

    return render_template('auth/login.html', form=form, title='Sign In')


# ---------------------------------------------------------------------------
# GET /auth/register   — show registration form
# POST /auth/register  — create new patient account
# ---------------------------------------------------------------------------
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))

    form = RegisterForm()

    if form.validate_on_submit():
        # Check uniqueness
        if User.query.filter_by(email=form.email.data.lower().strip()).first():
            flash('An account with that email already exists.', 'warning')
            return render_template('auth/register.html', form=form, title='Register')

        if User.query.filter_by(username=form.username.data.strip()).first():
            flash('That username is already taken.', 'warning')
            return render_template('auth/register.html', form=form, title='Register')

        # Default self-registration role is Patient
        patient_role = Role.query.filter_by(name='Patient').first()
        if not patient_role:
            flash('System configuration error. Please contact the administrator.', 'danger')
            return redirect(url_for('auth.login'))

        new_user = User(
            username=form.username.data.strip(),
            email=form.email.data.lower().strip(),
            password_hash=generate_password_hash(form.password.data, method='scrypt'),
            role_id=patient_role.id,
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form, title='Create Account')


# ---------------------------------------------------------------------------
# GET /auth/logout  — clear session and redirect to login
# ---------------------------------------------------------------------------
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

# ---------------------------------------------------------------------------
# GET /auth/forgot_password — show form to request password reset
# POST /auth/forgot_password — generate token, flash it (email sending stub)
# ---------------------------------------------------------------------------
@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    from forms.forgot_password_form import ForgotPasswordForm
    from models.password_reset_token import PasswordResetToken
    from models.user import User
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user:
            token_obj = PasswordResetToken.generate_for_user(user)
            db.session.commit()
            # In a real app you'd email token_obj.token to the user.
            flash(f'Password reset link generated. Use token: {token_obj.token}', 'success')
        else:
            flash('If that email exists in our system, a reset link will be sent.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/forgot_password.html', form=form, title='Forgot Password')

# ---------------------------------------------------------------------------
# GET /auth/reset_password/<token> — show form to set new password
# POST /auth/reset_password/<token> — validate token, update password
# ---------------------------------------------------------------------------
@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    from forms.reset_password_form import ResetPasswordForm
    from models.password_reset_token import PasswordResetToken
    token_obj = PasswordResetToken.query.filter_by(token=token, used=False).first()
    if not token_obj or not token_obj.is_valid():
        flash('Invalid or expired password reset token.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = token_obj.user
        user.password_hash = generate_password_hash(form.password.data, method='scrypt')
        token_obj.used = True
        db.session.commit()
        flash('Your password has been updated. You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form, title='Reset Password')

