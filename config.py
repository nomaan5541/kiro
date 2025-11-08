"""Configuration settings for School Management System.

This file contains the configuration settings for the Flask application.
It uses a class-based approach to handle different environments such as
development, testing, and production.
"""
import os
from datetime import timedelta


class Config:
    """Base configuration class.

    Contains default configuration settings that are common across all
    environments. Specific environments can override these settings.
    """

    # Basic Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # CSRF Protection (disabled for now due to incomplete implementation)
    WTF_CSRF_ENABLED = False
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "school_management.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # JWT configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-string'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # File upload configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
    
    # Pagination
    POSTS_PER_PAGE = 25
    STUDENTS_PER_PAGE = 50
    
    # Email configuration (for notifications)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # SMS/WhatsApp API configuration
    SMS_API_KEY = os.environ.get('SMS_API_KEY')
    SMS_API_URL = os.environ.get('SMS_API_URL')
    WHATSAPP_API_KEY = os.environ.get('WHATSAPP_API_KEY')
    WHATSAPP_API_URL = os.environ.get('WHATSAPP_API_URL')
    
    # Payment gateway configuration
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')


class DevelopmentConfig(Config):
    """Development configuration.

    Enables debug mode and uses a separate database for development.
    """
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///school_management_dev.db'


class TestingConfig(Config):
    """Testing configuration.

    Enables testing mode, uses an in-memory SQLite database, and disables CSRF
    protection for easier testing.
    """
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration.

    Disables debug mode and sets security settings for a production
    environment.
    """
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # Production security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}