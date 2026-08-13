# =============================================================================
# routes/api_dashboard.py — REST API Management Dashboard
# =============================================================================

from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from utils.decorators import role_required

api_dashboard_bp = Blueprint('api_dashboard', __name__)

@api_dashboard_bp.route('/api-management', methods=['GET'])
@login_required
@role_required('Admin', 'Doctor', 'Nurse', 'Pharmacist')
def dashboard():
    """REST API Management Dashboard matching Slide 21 mockup."""
    api_endpoints = [
        {"id": 1, "name": "Patient API", "endpoint": "/api/v1/patients", "methods": ["GET", "POST"], "status": "Active", "avg_time": "142 ms", "p95": "210 ms"},
        {"id": 2, "name": "Doctor API", "endpoint": "/api/v1/doctors", "methods": ["GET", "POST", "PUT"], "status": "Active", "avg_time": "128 ms", "p95": "192 ms"},
        {"id": 3, "name": "Consultation API", "endpoint": "/api/v1/consultations", "methods": ["GET", "POST", "PUT", "DELETE"], "status": "Active", "avg_time": "168 ms", "p95": "245 ms"},
        {"id": 4, "name": "Prescription API", "endpoint": "/api/v1/prescriptions", "methods": ["GET", "POST", "PUT", "DELETE"], "status": "Active", "avg_time": "153 ms", "p95": "230 ms"},
        {"id": 5, "name": "Laboratory API", "endpoint": "/api/v1/laboratory", "methods": ["GET", "POST", "PUT", "DELETE"], "status": "Active", "avg_time": "171 ms", "p95": "255 ms"},
        {"id": 6, "name": "Pharmacy API", "endpoint": "/api/v1/pharmacy", "methods": ["GET", "POST", "PUT", "DELETE"], "status": "Active", "avg_time": "149 ms", "p95": "220 ms"},
        {"id": 7, "name": "Billing API", "endpoint": "/api/v1/billing", "methods": ["GET", "POST", "PUT", "DELETE"], "status": "Active", "avg_time": "137 ms", "p95": "205 ms"},
        {"id": 8, "name": "Notification API", "endpoint": "/api/v1/notifications", "methods": ["GET", "POST"], "status": "Active", "avg_time": "110 ms", "p95": "165 ms"}
    ]

    metrics = {
        "total_apis": 18,
        "active_apis": "100%",
        "avg_response_time": "185 ms",
        "success_rate": "99%",
        "p95_response_time": "278 ms"
    }

    return render_template(
        'api/dashboard.html',
        endpoints=api_endpoints,
        metrics=metrics,
        title='REST API Management'
    )
