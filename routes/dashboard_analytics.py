# =============================================================================
# routes/dashboard_analytics.py — Executive Dashboard Analytics & Security
# =============================================================================

from flask import Blueprint, render_template, jsonify, flash
from flask_login import login_required, current_user
from utils.decorators import role_required
from services.analytics_service import get_executive_analytics_summary

dashboard_analytics_bp = Blueprint('dashboard_analytics', __name__)

@dashboard_analytics_bp.route('/dashboard-overview', methods=['GET'])
@login_required
@role_required('Admin')
def executive_overview():
    """Executive Administrator Analytics Dashboard matching Milestone 4 Day 1 (Slide 4 & 7 mockups)."""
    try:
        analytics = get_executive_analytics_summary()
    except Exception as e:
        flash(f"Error fetching real-time database analytics: {e}", "warning")
        analytics = {}

    return render_template(
        'dashboards/analytics.html',
        analytics=analytics,
        title='Analytics Dashboard'
    )


@dashboard_analytics_bp.route('/dashboard-overview/data', methods=['GET'])
@login_required
@role_required('Admin')
def executive_overview_data():
    """JSON API endpoint for real-time live refresh of charts and metric cards."""
    try:
        analytics = get_executive_analytics_summary()
        return jsonify({"status": "success", "analytics": analytics}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
