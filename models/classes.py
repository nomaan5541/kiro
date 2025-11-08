"""Data models for classes and subjects.

This module defines the `Class` model for representing a class in the school
and the `Subject` model for representing a subject taught in a class.
"""
from extensions import db
from datetime import datetime


class Class(db.Model):
    """Represents a class in the school.

    Attributes:
        id (int): Primary key.
        school_id (int): Foreign key for the school.
        class_name (str): The name of the class (e.g., "Class 10").
        section (str): The section of the class (e.g., "A").
        capacity (int): The capacity of the class.
        academic_year (str): The academic year.
    """
    __tablename__ = 'classes'
    
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    
    # Class information
    class_name = db.Column(db.String(50), nullable=False)  # e.g., "Nursery", "Class 1", "Class 10"
    section = db.Column(db.String(10), nullable=True)  # e.g., "A", "B", "C"
    capacity = db.Column(db.Integer, default=60)
    
    # Academic year
    academic_year = db.Column(db.String(20), nullable=True)  # e.g., "2024-25"
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    school = db.relationship('School', backref='classes', lazy=True)
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('school_id', 'class_name', 'section', name='unique_school_class_section'),
    )
    
    def __repr__(self):
        return f'<Class {self.class_name}{" " + self.section if self.section else ""}>'
    
    def get_display_name(self):
        """Returns the full display name of the class (e.g., "Class 10 A")."""
        if self.section:
            return f"{self.class_name} {self.section}"
        return self.class_name
    
    def get_student_count(self):
        """Returns the number of students in the class."""
        return len(self.students)
    
    def to_dict(self):
        """Serializes the Class object to a dictionary.

        Returns:
            dict: A dictionary representation of the class.
        """
        return {
            'id': self.id,
            'school_id': self.school_id,
            'class_name': self.class_name,
            'section': self.section,
            'capacity': self.capacity,
            'academic_year': self.academic_year,
            'display_name': self.get_display_name(),
            'student_count': self.get_student_count(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Subject(db.Model):
    """Represents a subject taught in a class.

    Attributes:
        id (int): Primary key.
        school_id (int): Foreign key for the school.
        class_id (int): Foreign key for the class.
        name (str): The name of the subject (e.g., "Mathematics").
        code (str): The subject code (e.g., "MATH").
        description (str): A description of the subject.
    """
    __tablename__ = 'subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    
    # Subject information
    name = db.Column(db.String(100), nullable=False)  # e.g., "Mathematics", "English"
    code = db.Column(db.String(20), nullable=True)  # e.g., "MATH", "ENG"
    description = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    school = db.relationship('School', backref='subjects', lazy=True)
    class_info = db.relationship('Class', backref='subjects', lazy=True)
    
    def __repr__(self):
        return f'<Subject {self.name}>'
    
    def to_dict(self):
        """Serializes the Subject object to a dictionary.

        Returns:
            dict: A dictionary representation of the subject.
        """
        return {
            'id': self.id,
            'school_id': self.school_id,
            'class_id': self.class_id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }