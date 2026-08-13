# =============================================================================
# routes/notification.py — Notification Blueprint
# =============================================================================
# URL Prefix: /notifications
# =============================================================================

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from utils.decorators import role_required
from services.notification_service import (
    get_notification_metrics, list_notifications, mark_notification_as_read, mark_all_notifications_as_read, send_notification
)

notification_bp = Blueprint('notification', __name__)

@notification_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    """Notification Dashboard matching Slide 26 mockup."""
    metrics = get_notification_metrics()
    notifications = list_notifications(current_user.id if current_user.role and current_user.role.name == 'Patient' else None)
    
    selected_notif = notifications[0] if notifications else None

    return render_template(
        'notifications/dashboard.html',
        metrics=metrics,
        notifications=notifications,
        selected_notification=selected_notif,
        title='Notification Management'
    )


@notification_bp.route('/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_read(notification_id):
    """Mark single notification as read."""
    if mark_notification_as_read(notification_id):
        flash("Notification marked as read.", "success")
    return redirect(url_for('notification.dashboard'))


@notification_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all notifications as read."""
    count = mark_all_notifications_as_read(current_user.id if current_user.role and current_user.role.name == 'Patient' else None)
    flash(f"Marked {count} notifications as read.", "success")
    return redirect(url_for('notification.dashboard'))


@notification_bp.route('/send-test', methods=['POST'])
@login_required
def send_test_notification():
    """Triggers test notification."""
    send_notification(
        patient_id=4,
        notification_type='General Info',
        message='Test notification sent successfully from Notification Manager!',
        delivery_method='In-App'
    )
    flash("Test notification sent successfully!", "success")
    return redirect(url_for('notification.dashboard'))
