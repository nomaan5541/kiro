"""Data model for users.

This module defines the `User` model, which is used for authentication and
role-based access control for all users in the system.
"""
from extensions import db
from datetime import datetime
from enum import Enum


class UserRole(Enum):
    """Enumeration for the different user roles in the system."""
    SUPER_ADMIN = 'super_admin'
    SCHOOL_ADMIN = 'school_admin'
    TEACHER = 'teacher'
    STUDENT = 'student'
    PARENT = 'parent'


class User(db.Model):
    """Represents a user of the system.

    This model is used for authentication and authorization. Each user has a
    specific role that determines their permissions.

    Attributes:
        id (int): Primary key.
        name (str): The full name of the user.
        email (str): The user's email address (used for login).
        password_hash (str): The hashed password.
        role (UserRole): The user's role.
        school_id (int): Foreign key for the school the user belongs to.
        is_active (bool): Whether the user's account is active.
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    school = db.relationship('School', backref='users', lazy=True)
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def to_dict(self):
        """Serializes the User object to a dictionary.

        Returns:
            dict: A dictionary representation of the user.
        """
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role.value,
            'school_id': self.school_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }