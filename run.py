# =============================================================================
# INTEGRATED PATIENT CARE MANAGEMENT SYSTEM
# Application Entry Point
# =============================================================================
#
# Run with:
#   python run.py                   (development)
#   FLASK_ENV=production python run.py  (production)
#
# Or with the Flask CLI:
#   set FLASK_APP=run.py   (Windows)
#   flask run
# =============================================================================

import os
from app import create_app

# Pick environment from .env / shell; default to development
config_name = os.environ.get('FLASK_ENV', 'development')

app = create_app(config_name)

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=app.config.get('DEBUG', True),
    )
