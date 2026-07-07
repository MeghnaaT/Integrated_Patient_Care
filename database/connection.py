# =============================================================================
# database/connection.py — Shared SQLAlchemy instance
# =============================================================================
# This module is imported by the app factory and all model files.
# It defines a single SQLAlchemy object that is lazily bound to the Flask app
# via ``db.init_app(app)`` inside ``create_app``.
# =============================================================================

from flask_sqlalchemy import SQLAlchemy

# The db object is created here, **without** an app context.
# All models import this instance, ensuring they all share the same
# session/metadata once the Flask app is instantiated.

db = SQLAlchemy()
