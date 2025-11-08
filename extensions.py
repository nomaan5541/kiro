"""Flask extensions initialization.

This file initializes the Flask extensions used by the application.
By centralizing extension initialization here, we avoid circular dependencies
and keep the main application file cleaner.

Attributes:
    db (SQLAlchemy): The Flask-SQLAlchemy extension instance.
    migrate (Migrate): The Flask-Migrate extension instance for database migrations.
    jwt (JWTManager): The Flask-JWT-Extended extension instance for JWT management.
    bcrypt (Bcrypt): The Flask-Bcrypt extension instance for password hashing.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
bcrypt = Bcrypt()