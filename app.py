# =============================================================================
# INTEGRATED PATIENT CARE MANAGEMENT SYSTEM
# Flask Application Factory
# =============================================================================
#
# Uses the Application Factory Pattern so the app can be instantiated with
# different config objects (development vs production vs testing).
#
# Extensions (db, login_manager, csrf) are created here and bound to the app
# instance inside create_app(), not at module level, so they are safe for
# unit testing and multiple app instances.
# =============================================================================

from flask import Flask, render_template
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

from database.connection import db
from config import config

# ---------------------------------------------------------------------------
# Extension instances — not yet bound to any Flask app
# ---------------------------------------------------------------------------
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_name: str = 'default') -> Flask:
    """
    Application factory function.

    Args:
        config_name: Key in config dict ('development' | 'production' | 'default')

    Returns:
        Fully configured Flask application instance.
    """
    app = Flask(__name__, template_folder='templates', static_folder='static')

    # -------------------------------------------------------------------------
    # Load configuration
    # -------------------------------------------------------------------------
    app.config.from_object(config[config_name])

    # -------------------------------------------------------------------------
    # Initialise extensions with the app instance
    # -------------------------------------------------------------------------
    db.init_app(app)
    csrf.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = app.config['LOGIN_MESSAGE']
    login_manager.login_message_category = app.config['LOGIN_MESSAGE_CATEGORY']

    # -------------------------------------------------------------------------
    # Flask-Login: user loader callback
    # -------------------------------------------------------------------------
    from models.user import User

    @login_manager.user_loader
    def load_user(user_id: str):
        """Reload the user object from the session's user_id."""
        return db.session.get(User, int(user_id))

    # -------------------------------------------------------------------------
    # Register Blueprints
    # -------------------------------------------------------------------------
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.admin import admin_bp
    from routes.doctor import doctor_bp
    from routes.nurse import nurse_bp
    from routes.patient import patient_bp

    app.register_blueprint(dashboard_bp)                      # / and /dashboard
    app.register_blueprint(auth_bp,    url_prefix='/auth')    # /auth/login  /auth/logout
    app.register_blueprint(admin_bp,   url_prefix='/admin')   # /admin/*
    app.register_blueprint(doctor_bp,  url_prefix='/doctor')  # /doctor/*
    app.register_blueprint(nurse_bp,   url_prefix='/nurse')   # /nurse/*
    app.register_blueprint(patient_bp, url_prefix='/patient') # /patient/*

    # -------------------------------------------------------------------------
    # HTTP Error Handlers
    # -------------------------------------------------------------------------
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()       # Roll back any partial transaction
        return render_template('errors/500.html'), 500

    return app
