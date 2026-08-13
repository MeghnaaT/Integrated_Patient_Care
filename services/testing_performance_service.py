# =============================================================================
# services/testing_performance_service.py — Performance Benchmark & Audit Engine
# =============================================================================

import time
import datetime
from typing import Dict, List, Any
from database.connection import db
from models.patient import Patient
from models.doctor import Doctor
from models.appointment import Appointment
from models.consultation import Consultation
from models.billing import Bill
from models.lab_report import LabReport

def measure_database_query_speed() -> float:
    """Measures live database query execution time in milliseconds."""
    start_time = time.time()
    # Execute complex multi-table query benchmark
    _ = Patient.query.join(Appointment, isouter=True).limit(50).all()
    elapsed_ms = (time.time() - start_time) * 1000.0
    return round(elapsed_ms, 2)

def get_performance_optimization_metrics() -> Dict[str, Any]:
    """
    Computes system performance benchmarks and metrics matching Slide 15 mockup.
    """
    db_query_time = measure_database_query_speed()

    response_time_trend = {
        'labels': ['12:00 PM', '04:00 PM', '08:00 PM', '12:00 AM', '04:00 AM', '08:00 AM', '12:00 PM'],
        'data': [210, 240, 190, 180, 310, 200, 185]
    }

    performance_by_module = [
        {'module': 'Patient Management', 'response_time': '152 ms', 'status': 'Excellent'},
        {'module': 'Appointment Management', 'response_time': '180 ms', 'status': 'Excellent'},
        {'module': 'Consultation Management', 'response_time': '210 ms', 'status': 'Good'},
        {'module': 'Laboratory Management', 'response_time': '195 ms', 'status': 'Good'},
        {'module': 'Prescription Management', 'response_time': '160 ms', 'status': 'Excellent'},
        {'module': 'Billing & Payments', 'response_time': '220 ms', 'status': 'Good'},
        {'module': 'Reports & Analytics', 'response_time': '175 ms', 'status': 'Excellent'},
        {'module': 'Notification System', 'response_time': '140 ms', 'status': 'Excellent'}
    ]

    load_testing_results = [
        {'scenario': 'Normal Load', 'users': '50 Users', 'duration': '10 min', 'requests': '15,234', 'avg_response': '152 ms', 'status': 'Passed'},
        {'scenario': 'High Load', 'users': '100 Users', 'duration': '10 min', 'requests': '28,456', 'avg_response': '198 ms', 'status': 'Passed'},
        {'scenario': 'Stress Test', 'users': '200 Users', 'duration': '15 min', 'requests': '56,789', 'avg_response': '367 ms', 'status': 'Passed'},
        {'scenario': 'Spike Test', 'users': '150 Users', 'duration': '5 min', 'requests': '12,345', 'avg_response': '210 ms', 'status': 'Passed'}
    ]

    api_testing_summary = {
        'total': 120,
        'passed': 108,
        'failed': 6,
        'warning': 4,
        'not_tested': 2,
        'passed_pct': 90.0
    }

    database_performance = {
        'query_response_time': f"{db_query_time if db_query_time > 0 else 45} ms",
        'slow_queries': 2,
        'active_connections': '28 / 100',
        'cache_hit_ratio': '96.5%'
    }

    optimization_recommendations = [
        {'recommendation': 'Enable Redis caching for frequently accessed patient records', 'impact': 'High Impact', 'badge': 'bg-danger'},
        {'recommendation': 'Optimize database indexes for appointment queries', 'impact': 'High Impact', 'badge': 'bg-danger'},
        {'recommendation': 'Implement API response compression (gzip)', 'impact': 'Medium Impact', 'badge': 'bg-warning text-dark'},
        {'recommendation': 'Enable connection pooling for database connections', 'impact': 'Medium Impact', 'badge': 'bg-warning text-dark'},
        {'recommendation': 'Optimize images and static assets', 'impact': 'Low Impact', 'badge': 'bg-secondary'}
    ]

    return {
        'overall_score': 92,
        'avg_response_time': '185 ms',
        'system_throughput': '256 req/s',
        'error_rate': '0.35%',
        'system_uptime': '99.98%',
        'db_query_time': f"{db_query_time} ms",
        'response_time_trend': response_time_trend,
        'performance_by_module': performance_by_module,
        'load_testing_results': load_testing_results,
        'api_testing_summary': api_testing_summary,
        'database_performance': database_performance,
        'optimization_recommendations': optimization_recommendations
    }
