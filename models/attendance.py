"""
Attendance model for tracking student attendance
"""
from extensions import db
from datetime import datetime, date
from enum import Enum


class AttendanceStatus(Enum):
    PRESENT = 'present'
    ABSENT = 'absent'
    LEAVE = 'leave'
    LATE = 'late'


class Attendance(db.Model):
    """Attendance model for tracking daily student attendance"""
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    
    # Attendance information
    date = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.Enum(AttendanceStatus), nullable=False)
    remarks = db.Column(db.Text, nullable=True)
    
    # Tracking information
    marked_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    marked_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    school = db.relationship('School', backref='attendance_records', lazy=True)
    student = db.relationship('Student', backref='attendance_records', lazy=True)
    class_info = db.relationship('Class', backref='attendance_records', lazy=True)
    marked_by_user = db.relationship('User', backref='marked_attendance', lazy=True)
    
    # Unique constraint - one attendance record per student per date
    __table_args__ = (
        db.UniqueConstraint('student_id', 'date', name='unique_student_date_attendance'),
    )
    
    def __repr__(self):
        return f'<Attendance {self.student.name if self.student else "Unknown"} - {self.date} - {self.status.value}>'
    
    def to_dict(self):
        """Convert attendance to dictionary"""
        return {
            'id': self.id,
            'school_id': self.school_id,
            'student_id': self.student_id,
            'class_id': self.class_id,
            'date': self.date.isoformat() if self.date else None,
            'status': self.status.value,
            'remarks': self.remarks,
            'marked_by': self.marked_by,
            'marked_at': self.marked_at.isoformat() if self.marked_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AttendanceSummary(db.Model):
    """Attendance summary model for storing calculated attendance statistics"""
    __tablename__ = 'attendance_summary'
    
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    
    # Summary period
    month = db.Column(db.Integer, nullable=False)  # 1-12
    year = db.Column(db.Integer, nullable=False)
    
    # Attendance statistics
    total_days = db.Column(db.Integer, default=0)
    present_days = db.Column(db.Integer, default=0)
    absent_days = db.Column(db.Integer, default=0)
    leave_days = db.Column(db.Integer, default=0)
    late_days = db.Column(db.Integer, default=0)
    
    # Calculated percentage
    attendance_percentage = db.Column(db.Float, default=0.0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    school = db.relationship('School', backref='attendance_summaries', lazy=True)
    student = db.relationship('Student', backref='attendance_summaries', lazy=True)
    class_info = db.relationship('Class', backref='attendance_summaries', lazy=True)
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('student_id', 'month', 'year', name='unique_student_month_year'),
    )
    
    def __repr__(self):
        return f'<AttendanceSummary {self.student.name if self.student else "Unknown"} - {self.month}/{self.year}>'
    
    def calculate_percentage(self):
        """Calculate attendance percentage"""
        if self.total_days > 0:
            self.attendance_percentage = (self.present_days / self.total_days) * 100
        else:
            self.attendance_percentage = 0.0
        return self.attendance_percentage
    
    def to_dict(self):
        """Convert attendance summary to dictionary"""
        return {
            'id': self.id,
            'school_id': self.school_id,
            'student_id': self.student_id,
            'class_id': self.class_id,
            'month': self.month,
            'year': self.year,
            'total_days': self.total_days,
            'present_days': self.present_days,
            'absent_days': self.absent_days,
            'leave_days': self.leave_days,
            'late_days': self.late_days,
            'attendance_percentage': self.attendance_percentage,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }