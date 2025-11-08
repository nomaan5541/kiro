"""Data model for schools.

This module defines the `School` model, which stores information about each
school registered in the system, including subscription details.
"""
from extensions import db
from datetime import datetime
from enum import Enum


class SchoolStatus(Enum):
    """Enumeration for the status of a school's subscription."""
    ACTIVE = 'active'
    SUSPENDED = 'suspended'
    EXPIRED = 'expired'
    INACTIVE = 'inactive'


class School(db.Model):
    """Represents a school registered in the system.

    Attributes:
        id (int): Primary key.
        name (str): The name of the school.
        email (str): The contact email for the school.
        phone (str): The contact phone number for the school.
        address (str): The physical address of the school.
        subscription_start (datetime): The start date of the subscription.
        subscription_end (datetime): The end date of the subscription.
        status (SchoolStatus): The current status of the school.
        setup_completed (bool): Whether the initial setup wizard is completed.
    """
    __tablename__ = 'schools'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(15), nullable=False)
    address = db.Column(db.Text, nullable=True)
    
    # Subscription management
    subscription_start = db.Column(db.DateTime, nullable=False)
    subscription_end = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.Enum(SchoolStatus), default=SchoolStatus.ACTIVE)
    
    # Setup tracking
    setup_completed = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<School {self.name}>'
    
    def days_remaining(self):
        """Calculates the number of days remaining in the subscription."""
        if self.subscription_end:
            delta = self.subscription_end - datetime.utcnow()
            return max(0, delta.days)
        return 0
    
    def is_subscription_active(self):
        """Checks if the school's subscription is currently active."""
        return (self.status == SchoolStatus.ACTIVE and 
                self.subscription_end > datetime.utcnow())
    
    def subscription_status_color(self):
        """Returns a color code based on the subscription status."""
        days_left = self.days_remaining()
        if days_left <= 3:
            return 'red'
        elif days_left <= 10:
            return 'orange'
        else:
            return 'green'
    
    def to_dict(self):
        """Serializes the School object to a dictionary.

        Returns:
            dict: A dictionary representation of the school.
        """
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'subscription_start': self.subscription_start.isoformat() if self.subscription_start else None,
            'subscription_end': self.subscription_end.isoformat() if self.subscription_end else None,
            'status': self.status.value,
            'setup_completed': self.setup_completed,
            'days_remaining': self.days_remaining(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }