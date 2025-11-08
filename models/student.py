"""Data model for students.

This module defines the `Student` model, which stores all the information
related to a student in a school.
"""
from extensions import db
from datetime import datetime
from enum import Enum


class StudentStatus(Enum):
    """Enumeration for the status of a student."""
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    GRADUATED = 'graduated'
    TRANSFERRED = 'transferred'


class Student(db.Model):
    """Represents a student in a school.

    Attributes:
        id (int): Primary key.
        school_id (int): Foreign key for the school.
        class_id (int): Foreign key for the class.
        roll_number (str): The student's roll number in their class.
        admission_no (str): The unique admission number of the student.
        name (str): The full name of the student.
        father_name (str): The father's name.
        mother_name (str): The mother's name.
        gender (str): The gender of the student.
        date_of_birth (date): The student's date of birth.
        phone (str): The contact phone number.
        email (str): The contact email address.
        address (str): The student's address.
        status (StudentStatus): The current status of the student.
        // ... and other attributes
    """
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=True)
    
    # Student identification
    roll_number = db.Column(db.String(20), nullable=False)
    admission_no = db.Column(db.String(50), nullable=False)
    admission_date = db.Column(db.Date, nullable=False)
    
    # Personal information
    name = db.Column(db.String(100), nullable=False)
    father_name = db.Column(db.String(100), nullable=False)
    mother_name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.Enum('male', 'female', 'other', name='gender'), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    
    # Contact information
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    pincode = db.Column(db.String(10), nullable=True)
    
    # Additional information
    blood_group = db.Column(db.String(5), nullable=True)
    pen_no = db.Column(db.String(50), nullable=True)  # Permanent Education Number
    bio = db.Column(db.Text, nullable=True)
    photo_url = db.Column(db.String(255), nullable=True)
    
    # Status and tracking
    status = db.Column(db.Enum(StudentStatus), default=StudentStatus.ACTIVE)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    school = db.relationship('School', backref='students', lazy=True)
    class_info = db.relationship('Class', backref='students', lazy=True)
    
    # Unique constraints
    __table_args__ = (
        db.UniqueConstraint('school_id', 'roll_number', name='unique_school_roll'),
        db.UniqueConstraint('school_id', 'admission_no', name='unique_school_admission'),
    )
    
    def __repr__(self):
        return f'<Student {self.name} ({self.admission_no})>'
    
    def get_full_name(self):
        """Returns the student's full name."""
        return self.name
    
    def get_age(self):
        """Calculates and returns the student's current age."""
        if self.date_of_birth:
            today = datetime.now().date()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None
    
    def to_dict(self):
        """Serializes the Student object to a dictionary.

        Returns:
            dict: A dictionary representation of the student.
        """
        return {
            'id': self.id,
            'school_id': self.school_id,
            'class_id': self.class_id,
            'roll_number': self.roll_number,
            'admission_no': self.admission_no,
            'admission_date': self.admission_date.isoformat() if self.admission_date else None,
            'name': self.name,
            'father_name': self.father_name,
            'mother_name': self.mother_name,
            'gender': self.gender,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'pincode': self.pincode,
            'blood_group': self.blood_group,
            'pen_no': self.pen_no,
            'bio': self.bio,
            'photo_url': self.photo_url,
            'status': self.status.value,
            'age': self.get_age(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }