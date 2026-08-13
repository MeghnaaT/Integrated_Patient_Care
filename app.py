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
    from routes.appointment import appointment_bp
    from routes.reports import reports_bp
    from routes.ehr import ehr_bp
    from routes.consultation import consultation_bp
    from routes.prescription import prescription_bp
    from routes.lab import laboratory_bp
    from routes.medical_history import medical_history_bp

    from routes.pharmacy import pharmacy_bp
    from routes.billing import billing_bp
    from routes.api import api_bp
    from routes.api_dashboard import api_dashboard_bp
    from routes.notification import notification_bp
    from routes.dashboard_analytics import dashboard_analytics_bp
    from routes.system_integration import system_integration_bp
    from routes.testing_performance import testing_performance_bp
    from routes.feedback import feedback_bp

    app.register_blueprint(dashboard_bp)                                 # / and /dashboard
    app.register_blueprint(auth_bp,            url_prefix='/auth')            # /auth/*
    app.register_blueprint(admin_bp,           url_prefix='/admin')           # /admin/*
    app.register_blueprint(doctor_bp,          url_prefix='/doctor')          # /doctor/*
    app.register_blueprint(nurse_bp,           url_prefix='/nurse')           # /nurse/*
    app.register_blueprint(patient_bp,         url_prefix='/patient')         # /patient/*
    app.register_blueprint(appointment_bp,     url_prefix='/appointment')     # /appointment/*
    app.register_blueprint(reports_bp,         url_prefix='/reports')         # /reports/*
    app.register_blueprint(ehr_bp,             url_prefix='/ehr')             # /ehr/*
    app.register_blueprint(consultation_bp,    url_prefix='/consultations')   # /consultations/*
    app.register_blueprint(prescription_bp,    url_prefix='/prescriptions')   # /prescriptions/*
    app.register_blueprint(laboratory_bp,      url_prefix='/laboratory')      # /laboratory/*
    app.register_blueprint(medical_history_bp, url_prefix='/medical-history') # /medical-history/*
    app.register_blueprint(pharmacy_bp,        url_prefix='/pharmacy')        # /pharmacy/*
    app.register_blueprint(billing_bp,         url_prefix='/billing')         # /billing/*
    app.register_blueprint(api_bp,             url_prefix='/api/v1')         # /api/v1/*
    app.register_blueprint(api_dashboard_bp)                                  # /api-management
    app.register_blueprint(notification_bp,    url_prefix='/notifications')   # /notifications/*
    app.register_blueprint(dashboard_analytics_bp)                             # /dashboard-overview
    app.register_blueprint(system_integration_bp)                            # /system-integration & /milestone3-summary
    app.register_blueprint(testing_performance_bp)                            # /testing-performance
    app.register_blueprint(feedback_bp,               url_prefix='/feedback')        # /feedback/*


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
