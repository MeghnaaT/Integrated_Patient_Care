# =============================================================================
# models/password_reset_token.py — Password Reset Token Model
# =============================================================================
# Stores a one‑time token for a user to reset their password. The token is a
# short random string (URL‑safe) with an expiration timestamp.
# =============================================================================

import secrets
from datetime import datetime, timedelta

from database.connection import db

class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)

    # Relationship back to User (optional convenience)
    user = db.relationship('User', backref=db.backref('reset_tokens', lazy='dynamic'))

    @staticmethod
    def generate_for_user(user, expires_in_minutes: int = 30):
        """Create a new token for *user* that expires after *expires_in_minutes*.
        Returns the newly created PasswordResetToken instance (already added to the
        session but not committed)."""
        raw_token = secrets.token_urlsafe(32)
        token_obj = PasswordResetToken(
            user_id=user.id,
            token=raw_token,
            expires_at=datetime.utcnow() + timedelta(minutes=expires_in_minutes),
        )
        db.session.add(token_obj)
        return token_obj

    def is_valid(self):
        """Return True if the token has not expired and has not been used."""
        return not self.used and datetime.utcnow() < self.expires_at

    def __repr__(self):
        return f"<PasswordResetToken user_id={self.user_id} token={self.token[:8]}...>"
