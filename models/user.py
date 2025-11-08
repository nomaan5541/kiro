"""
User model for authentication and role management
"""
from extensions import db
from datetime import datetime
from enum import Enum


class UserRole(Enum):
    SUPER_ADMIN = 'super_admin'
    SCHOOL_ADMIN = 'school_admin'
    TEACHER = 'teacher'
    STUDENT = 'student'
    PARENT = 'parent'


class User(db.Model):
    """User model for all system users"""
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
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role.value,
            'school_id': self.school_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }