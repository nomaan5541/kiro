"""
School Management System - Main Application Entry Point
"""
from flask import Flask
from config import Config
from extensions import db, migrate, jwt, bcrypt
from blueprints.auth import auth_bp
from blueprints.super_admin import super_admin_bp
from blueprints.school_admin import school_admin_bp
from blueprints.teacher import teacher_bp
from blueprints.student import student_bp
from blueprints.api import api_bp
from blueprints.files import files_bp


def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(super_admin_bp, url_prefix='/super-admin')
    app.register_blueprint(school_admin_bp, url_prefix='/school')
    app.register_blueprint(teacher_bp, url_prefix='/teacher')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(files_bp, url_prefix='/files')
    
    # Import and register fee API blueprint
    from blueprints.fee_api import fee_api_bp
    app.register_blueprint(fee_api_bp)
    
    # Import and register notification API blueprint
    from blueprints.notification_api import notification_api_bp
    app.register_blueprint(notification_api_bp)
    
    # Register before_request handler
    from utils.auth import before_request
    app.before_request(before_request)
    
    # Register template filters
    from utils.file_helpers import register_file_filters
    register_file_filters(app)
    
    # Root route
    @app.route('/')
    def index():
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)