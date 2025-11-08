"""Data models for teachers and their assignments.

This module defines the models for `Teacher`, `TeacherClassAssignment`, and
`TeacherSubjectAssignment`, which are used to manage teacher information and
their responsibilities within the school.
"""
from extensions import db
from datetime import datetime
from enum import Enum


class TeacherStatus(Enum):
    """Enumeration for the employment status of a teacher."""
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    ON_LEAVE = 'on_leave'
    TERMINATED = 'terminated'


class Teacher(db.Model):
    """Represents a teacher in a school.

    Attributes:
        id (int): Primary key.
        user_id (int): Foreign key for the associated user account.
        school_id (int): Foreign key for the school.
        employee_id (str): The unique employee ID for the teacher.
        designation (str): The teacher's designation.
        qualification (str): The teacher's qualifications.
        experience_years (int): The teacher's years of experience.
        phone (str): The teacher's phone number.
        status (TeacherStatus): The teacher's employment status.
        // ... and other personal and professional information
    """
    __tablename__ = 'teachers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    
    # Professional information
    employee_id = db.Column(db.String(50), nullable=False)
    designation = db.Column(db.String(100), nullable=True)  # 'Principal', 'Vice Principal', 'Teacher', etc.
    department = db.Column(db.String(100), nullable=True)
    qualification = db.Column(db.String(200), nullable=True)
    experience_years = db.Column(db.Integer, default=0)
    
    # Personal information
    phone = db.Column(db.String(15), nullable=False)
    emergency_contact = db.Column(db.String(15), nullable=True)
    address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    pincode = db.Column(db.String(10), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    date_of_joining = db.Column(db.Date, nullable=False)
    gender = db.Column(db.Enum('male', 'female', 'other', name='teacher_gender'), nullable=True)
    blood_group = db.Column(db.String(10), nullable=True)
    marital_status = db.Column(db.String(20), nullable=True)
    aadhaar_number = db.Column(db.String(20), nullable=True)
    pan_number = db.Column(db.String(20), nullable=True)
    nationality = db.Column(db.String(50), default='Indian')
    religion = db.Column(db.String(50), nullable=True)
    languages_known = db.Column(db.String(200), nullable=True)
    communication_preference = db.Column(db.String(20), default='WhatsApp')
    
    # Employment details
    salary = db.Column(db.Numeric(10, 2), nullable=True)
    status = db.Column(db.Enum(TeacherStatus), default=TeacherStatus.ACTIVE)
    
    # Additional information
    bio = db.Column(db.Text, nullable=True)
    photo_url = db.Column(db.String(255), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='teacher_profile', lazy=True)
    school = db.relationship('School', backref='teachers', lazy=True)
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('school_id', 'employee_id', name='unique_school_employee_id'),
    )
    
    def __repr__(self):
        return f'<Teacher {self.user.name if self.user else "Unknown"} ({self.employee_id})>'
    
    def get_assigned_classes(self):
        """Returns a list of classes assigned to the teacher."""
        return [assignment.class_info for assignment in self.class_assignments if assignment.is_active]
    
    def get_assigned_subjects(self):
        """Returns a list of subjects assigned to the teacher."""
        return [assignment.subject for assignment in self.subject_assignments if assignment.is_active]
    
    def to_dict(self):
        """Serializes the Teacher object to a dictionary.

        Returns:
            dict: A dictionary representation of the teacher.
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'school_id': self.school_id,
            'employee_id': self.employee_id,
            'designation': self.designation,
            'department': self.department,
            'qualification': self.qualification,
            'experience_years': self.experience_years,
            'phone': self.phone,
            'emergency_contact': self.emergency_contact,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'pincode': self.pincode,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'gender': self.gender,
            'blood_group': self.blood_group,
            'marital_status': self.marital_status,
            'aadhaar_number': self.aadhaar_number,
            'pan_number': self.pan_number,
            'nationality': self.nationality,
            'religion': self.religion,
            'languages_known': self.languages_known,
            'communication_preference': self.communication_preference,
            'date_of_joining': self.date_of_joining.isoformat() if self.date_of_joining else None,
            'salary': float(self.salary) if self.salary else None,
            'status': self.status.value,
            'bio': self.bio,
            'photo_url': self.photo_url,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class TeacherClassAssignment(db.Model):
    """Represents the assignment of a teacher to a class.

    Attributes:
        id (int): Primary key.
        teacher_id (int): Foreign key for the teacher.
        class_id (int): Foreign key for the class.
        academic_year (str): The academic year of the assignment.
        is_class_teacher (bool): Whether the teacher is the main class teacher.
        is_active (bool): Whether the assignment is currently active.
    """
    __tablename__ = 'teacher_class_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    
    # Assignment details
    academic_year = db.Column(db.String(20), nullable=False)
    is_class_teacher = db.Column(db.Boolean, default=False)  # Is this teacher the class teacher?
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    teacher = db.relationship('Teacher', backref='class_assignments', lazy=True)
    class_info = db.relationship('Class', backref='teacher_assignments', lazy=True)
    school = db.relationship('School', backref='teacher_class_assignments', lazy=True)
    
    def __repr__(self):
        return f'<TeacherClassAssignment {self.teacher.user.name if self.teacher and self.teacher.user else "Unknown"} -> {self.class_info.get_display_name() if self.class_info else "Unknown"}>'


class TeacherSubjectAssignment(db.Model):
    """Represents the assignment of a teacher to a subject within a class.

    Attributes:
        id (int): Primary key.
        teacher_id (int): Foreign key for the teacher.
        subject_id (int): Foreign key for the subject.
        class_id (int): Foreign key for the class.
        academic_year (str): The academic year of the assignment.
        is_active (bool): Whether the assignment is currently active.
    """
    __tablename__ = 'teacher_subject_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    
    # Assignment details
    academic_year = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    teacher = db.relationship('Teacher', backref='subject_assignments', lazy=True)
    subject = db.relationship('Subject', backref='teacher_assignments', lazy=True)
    class_info = db.relationship('Class', backref='subject_assignments', lazy=True)
    school = db.relationship('School', backref='teacher_subject_assignments', lazy=True)
    
    def __repr__(self):
        return f'<TeacherSubjectAssignment {self.teacher.user.name if self.teacher and self.teacher.user else "Unknown"} -> {self.subject.name if self.subject else "Unknown"}>'


# Assignment-related classes moved to models/assignment.py
