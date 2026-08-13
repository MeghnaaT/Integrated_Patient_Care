# =============================================================================
# routes/system_integration.py — System Integration & Performance Blueprint
# =============================================================================

from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from utils.decorators import role_required
from services.workflow_integration_service import execute_complete_patient_workflow

system_integration_bp = Blueprint('system_integration', __name__)

@system_integration_bp.route('/system-integration', methods=['GET'])
@login_required
@role_required('Admin', 'Doctor', 'Nurse', 'Pharmacist')
def integration_testing():
    """System Integration & Performance Testing Dashboard matching Slide 36 mockup."""
    return render_template(
        'dashboards/system_integration.html',
        title='System Integration & Performance Testing'
    )


@system_integration_bp.route('/system-integration/run-workflow', methods=['POST', 'GET'])
@login_required
@role_required('Admin', 'Doctor', 'Nurse', 'Pharmacist')
def run_integration_workflow():
    """Executes the complete 12-step end-to-end patient workflow and returns JSON test results."""
    try:
        results = execute_complete_patient_workflow()
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@system_integration_bp.route('/milestone3-summary', methods=['GET'])
@login_required
@role_required('Admin', 'Doctor', 'Nurse', 'Pharmacist')
def milestone3_summary():
    """Milestone 3 System Integrated Dashboard matching Slide 37 mockup."""
    return render_template(
        'dashboards/milestone3_dashboard.html',
        title='Milestone 3 - System Integrated Dashboard'
    )
