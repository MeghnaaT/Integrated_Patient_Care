# =============================================================================
# routes/testing_performance.py — Testing & Performance Optimization Blueprint
# =============================================================================

from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from utils.decorators import role_required
from services.testing_performance_service import get_performance_optimization_metrics, measure_database_query_speed

testing_performance_bp = Blueprint('testing_performance', __name__)

@testing_performance_bp.route('/testing-performance', methods=['GET'])
@login_required
@role_required('Admin')
def testing_dashboard():
    """Testing & Performance Optimization Dashboard matching Slide 15 mockup."""
    metrics = get_performance_optimization_metrics()
    return render_template(
        'dashboards/testing_optimization.html',
        metrics=metrics,
        title='Testing & Performance Optimization'
    )


@testing_performance_bp.route('/testing-performance/run-test', methods=['POST', 'GET'])
@login_required
@role_required('Admin')
def run_performance_test():
    """Executes live query performance benchmark and returns timing metrics in JSON."""
    try:
        db_speed = measure_database_query_speed()
        metrics = get_performance_optimization_metrics()
        metrics['db_query_time'] = f"{db_speed} ms"
        return jsonify({"status": "success", "metrics": metrics}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
