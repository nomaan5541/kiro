"""Data models for managing school holidays.

This module defines the `Holiday` model for creating and managing school
holidays and announcements.
"""
from extensions import db
from datetime import datetime
from enum import Enum


class HolidayStatus(Enum):
    """Enumeration for the status of a holiday."""
    UPCOMING = 'upcoming'
    ACTIVE = 'active'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'


class Holiday(db.Model):
    """Represents a school holiday or announcement.

    Attributes:
        id (int): Primary key.
        school_id (int): Foreign key for the school.
        created_by (int): Foreign key for the user who created the holiday.
        title (str): The title of the holiday.
        description (str): A description of the holiday.
        start_date (date): The start date of the holiday.
        end_date (date): The end date of the holiday (for multi-day holidays).
        status (HolidayStatus): The status of the holiday.
    """
    __tablename__ = 'holidays'
    
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Holiday information
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)  # For multi-day holidays
    
    # Notification settings
    notify_teachers = db.Column(db.Boolean, default=True)
    notify_students = db.Column(db.Boolean, default=True)
    notify_parents = db.Column(db.Boolean, default=True)
    
    # Status and tracking
    status = db.Column(db.Enum(HolidayStatus), default=HolidayStatus.UPCOMING)
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_pattern = db.Column(db.String(50), nullable=True)  # 'yearly', 'monthly', etc.
    
    # Notification tracking
    notifications_sent = db.Column(db.Boolean, default=False)
    notification_sent_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    school = db.relationship('School', backref='holidays', lazy=True)
    creator = db.relationship('User', backref='created_holidays', lazy=True)
    
    def __repr__(self):
        return f'<Holiday {self.title} on {self.start_date}>'
    
    def get_duration_days(self):
        """Calculates the duration of the holiday in days."""
        if self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 1
    
    def is_multi_day(self):
        """Checks if the holiday spans multiple days."""
        return self.end_date is not None and self.end_date != self.start_date
    
    def get_status_display(self):
        """Returns a human-readable status for the holiday."""
        today = datetime.now().date()
        
        if self.start_date > today:
            return 'Upcoming'
        elif self.end_date and self.end_date < today:
            return 'Completed'
        elif self.start_date <= today <= (self.end_date or self.start_date):
            return 'Active'
        else:
            return self.status.value.title()
    
    def to_dict(self):
        """Serializes the Holiday object to a dictionary.

        Returns:
            dict: A dictionary representation of the holiday.
        """
        return {
            'id': self.id,
            'school_id': self.school_id,
            'created_by': self.created_by,
            'title': self.title,
            'description': self.description,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'notify_teachers': self.notify_teachers,
            'notify_students': self.notify_students,
            'notify_parents': self.notify_parents,
            'status': self.status.value,
            'is_recurring': self.is_recurring,
            'recurrence_pattern': self.recurrence_pattern,
            'notifications_sent': self.notifications_sent,
            'notification_sent_at': self.notification_sent_at.isoformat() if self.notification_sent_at else None,
            'duration_days': self.get_duration_days(),
            'is_multi_day': self.is_multi_day(),
            'status_display': self.get_status_display(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }