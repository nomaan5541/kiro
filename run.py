#!/usr/bin/env python3
"""Development server runner for the School Management System.

This script serves as the entry point for running the Flask development server.
It creates a Flask application instance using the application factory pattern
and runs it with the appropriate configuration.
"""
import os
from app import create_app
from config import config

# Get configuration from environment
config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config[config_name])

if __name__ == '__main__':
    # Run development server
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=True
    )