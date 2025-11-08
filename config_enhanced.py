"""
Enhanced Configuration settings for School Management System
Includes PostgreSQL, Redis, Cloud Storage, and advanced features
"""
import os
from datetime import timedelta


class Config:
    """Base configuration class with enhanced features"""
    
    # Basic Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Enhanced Database configuration
    # PostgreSQL as primary database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        os.environ.get('POSTGRESQL_URL') or \
        f'sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "school_management.db")}'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'max_overflow': 30,
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'pool_timeout': 30,
        'echo': False,  # Set to True for query logging in development
        'echo_pool': False,
        'connect_args': {
            'connect_timeout': 10,
            'application_name': 'school_management_system'
        }
    }
    
    # Database Migration settings
    SQLALCHEMY_MIGRATE_REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'migrations')
    
    # Redis Configuration for Caching
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    CACHE_TYPE = 'redis' if os.environ.get('REDIS_URL') else 'simple'
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300
    CACHE_KEY_PREFIX = 'school_mgmt:'
    
    # Session Configuration with Redis
    SESSION_TYPE = 'redis'
    SESSION_REDIS = None  # Will be set in app factory
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'session:'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # JWT configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-string'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
    
    # Enhanced File upload configuration
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    ALLOWED_EXTENSIONS = {
        'images': {'png', 'jpg', 'jpeg', 'gif', 'webp'},
        'documents': {'pdf', 'doc', 'docx', 'txt', 'rtf'},
        'spreadsheets': {'xls', 'xlsx', 'csv'},
        'presentations': {'ppt', 'pptx'},
        'archives': {'zip', 'rar', '7z'}
    }\n    \n    # Cloud Storage Configuration\n    # AWS S3\n    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')\n    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')\n    AWS_S3_BUCKET = os.environ.get('AWS_S3_BUCKET')\n    AWS_S3_REGION = os.environ.get('AWS_S3_REGION', 'us-east-1')\n    AWS_S3_CUSTOM_DOMAIN = os.environ.get('AWS_S3_CUSTOM_DOMAIN')\n    \n    # Google Cloud Storage\n    GOOGLE_CLOUD_PROJECT = os.environ.get('GOOGLE_CLOUD_PROJECT')\n    GOOGLE_CLOUD_BUCKET = os.environ.get('GOOGLE_CLOUD_BUCKET')\n    GOOGLE_APPLICATION_CREDENTIALS = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')\n    \n    # Storage Configuration\n    DEFAULT_FILE_STORAGE = os.environ.get('DEFAULT_FILE_STORAGE', 'local')  # 'local', 'aws_s3', 'google_cloud'\n    FILE_STORAGE_SETTINGS = {\n        'local': {\n            'base_path': UPLOAD_FOLDER,\n            'url_prefix': '/uploads/'\n        },\n        'aws_s3': {\n            'bucket': AWS_S3_BUCKET,\n            'region': AWS_S3_REGION,\n            'custom_domain': AWS_S3_CUSTOM_DOMAIN\n        },\n        'google_cloud': {\n            'bucket': GOOGLE_CLOUD_BUCKET,\n            'project': GOOGLE_CLOUD_PROJECT\n        }\n    }\n    \n    # Pagination\n    POSTS_PER_PAGE = 25\n    STUDENTS_PER_PAGE = 50\n    TEACHERS_PER_PAGE = 30\n    CLASSES_PER_PAGE = 20\n    \n    # Email configuration (Enhanced)\n    MAIL_SERVER = os.environ.get('MAIL_SERVER')\n    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)\n    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']\n    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', 'on', '1']\n    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')\n    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')\n    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or MAIL_USERNAME\n    MAIL_MAX_EMAILS = int(os.environ.get('MAIL_MAX_EMAILS') or 100)\n    MAIL_SUPPRESS_SEND = os.environ.get('MAIL_SUPPRESS_SEND', 'false').lower() in ['true', 'on', '1']\n    \n    # SMS/WhatsApp API configuration (Enhanced)\n    SMS_PROVIDER = os.environ.get('SMS_PROVIDER', 'twilio')  # 'twilio', 'aws_sns', 'custom'\n    SMS_API_KEY = os.environ.get('SMS_API_KEY')\n    SMS_API_SECRET = os.environ.get('SMS_API_SECRET')\n    SMS_API_URL = os.environ.get('SMS_API_URL')\n    SMS_FROM_NUMBER = os.environ.get('SMS_FROM_NUMBER')\n    \n    WHATSAPP_API_KEY = os.environ.get('WHATSAPP_API_KEY')\n    WHATSAPP_API_URL = os.environ.get('WHATSAPP_API_URL')\n    WHATSAPP_FROM_NUMBER = os.environ.get('WHATSAPP_FROM_NUMBER')\n    \n    # Payment gateway configuration (Enhanced)\n    PAYMENT_GATEWAY = os.environ.get('PAYMENT_GATEWAY', 'razorpay')  # 'razorpay', 'stripe', 'paypal'\n    \n    # Razorpay\n    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')\n    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')\n    RAZORPAY_WEBHOOK_SECRET = os.environ.get('RAZORPAY_WEBHOOK_SECRET')\n    \n    # Stripe\n    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')\n    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')\n    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')\n    \n    # PayPal\n    PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID')\n    PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET')\n    PAYPAL_MODE = os.environ.get('PAYPAL_MODE', 'sandbox')  # 'sandbox' or 'live'\n    \n    # Backup Configuration\n    BACKUP_ENABLED = os.environ.get('BACKUP_ENABLED', 'true').lower() in ['true', 'on', '1']\n    BACKUP_SCHEDULE = os.environ.get('BACKUP_SCHEDULE', 'daily')  # 'hourly', 'daily', 'weekly'\n    BACKUP_RETENTION_DAYS = int(os.environ.get('BACKUP_RETENTION_DAYS', 30))\n    BACKUP_STORAGE_TYPE = os.environ.get('BACKUP_STORAGE_TYPE', 'local')  # 'local', 'aws_s3', 'google_cloud'\n    BACKUP_ENCRYPTION_KEY = os.environ.get('BACKUP_ENCRYPTION_KEY')\n    \n    # Monitoring and Logging\n    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')\n    LOG_FILE = os.environ.get('LOG_FILE', 'logs/school_management.log')\n    LOG_MAX_BYTES = int(os.environ.get('LOG_MAX_BYTES', 10485760))  # 10MB\n    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 5))\n    \n    # Performance Monitoring\n    SLOW_QUERY_THRESHOLD = float(os.environ.get('SLOW_QUERY_THRESHOLD', 0.5))  # seconds\n    ENABLE_QUERY_LOGGING = os.environ.get('ENABLE_QUERY_LOGGING', 'false').lower() in ['true', 'on', '1']\n    \n    # Security Settings\n    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT') or 'security-salt-change-in-production'\n    SECURITY_PASSWORD_HASH = 'bcrypt'\n    SECURITY_PASSWORD_LENGTH_MIN = 8\n    SECURITY_PASSWORD_COMPLEXITY_CHECKER = 'zxcvbn'\n    \n    # Rate Limiting\n    RATELIMIT_ENABLED = True\n    RATELIMIT_STORAGE_URL = REDIS_URL\n    RATELIMIT_DEFAULT = \"100 per hour\"\n    RATELIMIT_HEADERS_ENABLED = True\n    \n    # CORS Settings\n    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')\n    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']\n    CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization']\n    \n    # Multi-tenancy Settings\n    MULTI_TENANT_ENABLED = os.environ.get('MULTI_TENANT_ENABLED', 'true').lower() in ['true', 'on', '1']\n    TENANT_ISOLATION_LEVEL = os.environ.get('TENANT_ISOLATION_LEVEL', 'schema')  # 'database', 'schema', 'row'\n    \n    # Feature Flags\n    FEATURES = {\n        'advanced_reporting': os.environ.get('FEATURE_ADVANCED_REPORTING', 'true').lower() in ['true', 'on', '1'],\n        'mobile_app_api': os.environ.get('FEATURE_MOBILE_APP_API', 'true').lower() in ['true', 'on', '1'],\n        'ai_insights': os.environ.get('FEATURE_AI_INSIGHTS', 'false').lower() in ['true', 'on', '1'],\n        'video_conferencing': os.environ.get('FEATURE_VIDEO_CONFERENCING', 'false').lower() in ['true', 'on', '1'],\n        'blockchain_certificates': os.environ.get('FEATURE_BLOCKCHAIN_CERTIFICATES', 'false').lower() in ['true', 'on', '1']\n    }\n\n\nclass DevelopmentConfig(Config):\n    \"\"\"Development configuration with enhanced debugging\"\"\"\n    DEBUG = True\n    TESTING = False\n    \n    # Development database (PostgreSQL preferred, SQLite fallback)\n    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \\\n        'postgresql://school_dev:dev_password@localhost:5432/school_management_dev' or \\\n        'sqlite:///school_management_dev.db'\n    \n    # Enable query logging in development\n    SQLALCHEMY_ENGINE_OPTIONS = {\n        **Config.SQLALCHEMY_ENGINE_OPTIONS,\n        'echo': True,\n        'echo_pool': True\n    }\n    \n    # Development-specific settings\n    MAIL_SUPPRESS_SEND = True\n    CACHE_TYPE = 'simple'  # Use simple cache for development\n    ENABLE_QUERY_LOGGING = True\n    \n    # Relaxed security for development\n    WTF_CSRF_ENABLED = True\n    WTF_CSRF_TIME_LIMIT = None\n\n\nclass TestingConfig(Config):\n    \"\"\"Testing configuration\"\"\"\n    TESTING = True\n    DEBUG = False\n    \n    # In-memory database for testing\n    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'\n    \n    # Disable CSRF for testing\n    WTF_CSRF_ENABLED = False\n    \n    # Disable caching for testing\n    CACHE_TYPE = 'null'\n    \n    # Disable external services for testing\n    MAIL_SUPPRESS_SEND = True\n    BACKUP_ENABLED = False\n    \n    # Fast password hashing for testing\n    SECURITY_PASSWORD_HASH = 'plaintext'\n\n\nclass ProductionConfig(Config):\n    \"\"\"Production configuration with enhanced security and performance\"\"\"\n    DEBUG = False\n    TESTING = False\n    \n    # Production database (must be PostgreSQL)\n    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')\n    \n    if not SQLALCHEMY_DATABASE_URI or SQLALCHEMY_DATABASE_URI.startswith('sqlite'):\n        raise ValueError(\"Production environment requires PostgreSQL database URL\")\n    \n    # Production security settings\n    SESSION_COOKIE_SECURE = True\n    SESSION_COOKIE_HTTPONLY = True\n    SESSION_COOKIE_SAMESITE = 'Lax'\n    \n    # Enhanced security headers\n    SECURITY_HEADERS = {\n        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',\n        'X-Content-Type-Options': 'nosniff',\n        'X-Frame-Options': 'DENY',\n        'X-XSS-Protection': '1; mode=block',\n        'Content-Security-Policy': \"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'\"\n    }\n    \n    # Production performance settings\n    SQLALCHEMY_ENGINE_OPTIONS = {\n        **Config.SQLALCHEMY_ENGINE_OPTIONS,\n        'pool_size': 50,\n        'max_overflow': 100,\n        'echo': False\n    }\n    \n    # Production logging\n    LOG_LEVEL = 'WARNING'\n    ENABLE_QUERY_LOGGING = False\n    \n    # Production rate limiting\n    RATELIMIT_DEFAULT = \"50 per hour\"\n\n\nclass StagingConfig(ProductionConfig):\n    \"\"\"Staging configuration (similar to production but with debugging)\"\"\"\n    DEBUG = True\n    \n    # Staging database\n    SQLALCHEMY_DATABASE_URI = os.environ.get('STAGING_DATABASE_URL')\n    \n    # Enable some debugging in staging\n    LOG_LEVEL = 'INFO'\n    ENABLE_QUERY_LOGGING = True\n    \n    # Relaxed rate limiting for testing\n    RATELIMIT_DEFAULT = \"200 per hour\"\n\n\nconfig = {\n    'development': DevelopmentConfig,\n    'testing': TestingConfig,\n    'staging': StagingConfig,\n    'production': ProductionConfig,\n    'default': DevelopmentConfig\n}\n\n\ndef get_config(config_name=None):\n    \"\"\"Get configuration based on environment\"\"\"\n    config_name = config_name or os.environ.get('FLASK_ENV', 'development')\n    return config.get(config_name, config['default'])\n