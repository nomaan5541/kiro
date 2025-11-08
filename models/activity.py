"""
Data models for activity logging and system metrics.

This module defines the `ActivityLog` model, which is used to create an audit
trail of all significant actions performed within the system. It also defines
the `SystemMetrics` model for tracking performance and usage statistics.
"""
from extensions import db
from datetime import datetime
from enum import Enum


class ActivityType(Enum):
    """Enumeration for the different types of activities that can be logged."""
    # User activities
    USER_LOGIN = 'user_login'
    USER_LOGOUT = 'user_logout'
    USER_CREATED = 'user_created'
    USER_UPDATED = 'user_updated'
    USER_DELETED = 'user_deleted'
    
    # School activities
    SCHOOL_REGISTERED = 'school_registered'
    SCHOOL_UPDATED = 'school_updated'
    SCHOOL_SUSPENDED = 'school_suspended'
    SCHOOL_ACTIVATED = 'school_activated'
    SUBSCRIPTION_RENEWED = 'subscription_renewed'
    
    # Student activities
    STUDENT_ENROLLED = 'student_enrolled'
    STUDENT_UPDATED = 'student_updated'
    STUDENT_TRANSFERRED = 'student_transferred'
    STUDENT_GRADUATED = 'student_graduated'
    
    # Class activities
    CLASS_CREATED = 'class_created'
    CLASS_UPDATED = 'class_updated'
    CLASS_DELETED = 'class_deleted'
    
    # Attendance activities
    ATTENDANCE_MARKED = 'attendance_marked'
    ATTENDANCE_UPDATED = 'attendance_updated'
    ATTENDANCE_BULK_MARKED = 'attendance_bulk_marked'
    
    # Payment activities
    PAYMENT_RECEIVED = 'payment_received'
    PAYMENT_UPDATED = 'payment_updated'
    PAYMENT_REFUNDED = 'payment_refunded'
    FEE_STRUCTURE_CREATED = 'fee_structure_created'
    FEE_STRUCTURE_UPDATED = 'fee_structure_updated'
    
    # System activities
    DATA_EXPORTED = 'data_exported'
    DATA_IMPORTED = 'data_imported'
    BACKUP_CREATED = 'backup_created'
    SYSTEM_ERROR = 'system_error'


class ActivityLog(db.Model):
    """Represents a single entry in the activity log.

    This model is used to create an audit trail of actions performed by users
    or the system.

    Attributes:
        id (int): The primary key.
        school_id (int): The ID of the school where the activity occurred.
        user_id (int): The ID of the user who performed the activity.
        activity_type (ActivityType): The type of activity.
        description (str): A human-readable description of the activity.
        entity_type (str): The type of the entity related to the activity.
        entity_id (int): The ID of the related entity.
        extra_data (str): A JSON string for storing additional data.
        ip_address (str): The IP address from which the activity was performed.
        user_agent (str): The user agent of the client.
        created_at (datetime): The timestamp of the activity.
    """
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Activity information
    activity_type = db.Column(db.Enum(ActivityType), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    # Related entity information
    entity_type = db.Column(db.String(50), nullable=True)  # 'student', 'payment', 'class', etc.
    entity_id = db.Column(db.Integer, nullable=True)
    
    # Additional data (JSON format)
    extra_data = db.Column(db.Text, nullable=True)  # JSON string for additional data
    
    # Request information
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4 or IPv6
    user_agent = db.Column(db.Text, nullable=True)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    school = db.relationship('School', backref='activity_logs', lazy=True)
    user = db.relationship('User', backref='activity_logs', lazy=True)
    
    def __repr__(self):
        return f'<ActivityLog {self.activity_type.value} by {self.user.name if self.user else "System"}>'
    
    @classmethod
    def log_activity(cls, activity_type, description, school_id=None, user_id=None, 
                    entity_type=None, entity_id=None, extra_data=None, 
                    ip_address=None, user_agent=None):
        """Creates and saves a new activity log entry.

        Args:
            activity_type (ActivityType): The type of activity.
            description (str): A description of the activity.
            school_id (int, optional): The ID of the associated school.
            user_id (int, optional): The ID of the user performing the action.
            entity_type (str, optional): The type of the related entity.
            entity_id (int, optional): The ID of the related entity.
            extra_data (str, optional): Additional JSON data.
            ip_address (str, optional): The user's IP address.
            user_agent (str, optional): The user's user agent.

        Returns:
            ActivityLog: The newly created activity log object.
        """
        activity = cls(
            school_id=school_id,
            user_id=user_id,
            activity_type=activity_type,
            description=description,
            entity_type=entity_type,
            entity_id=entity_id,
            extra_data=extra_data,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(activity)
        return activity
    
    def to_dict(self):
        """Serializes the ActivityLog object to a dictionary.

        Returns:
            dict: A dictionary representation of the activity log.
        """
        return {
            'id': self.id,
            'school_id': self.school_id,
            'user_id': self.user_id,
            'activity_type': self.activity_type.value,
            'description': self.description,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'extra_data': self.extra_data,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SystemMetrics(db.Model):
    """Represents a single data point for system metrics.

    This model is used to track various system performance and usage
    statistics over time.

    Attributes:
        id (int): The primary key.
        metric_name (str): The name of the metric.
        metric_value (float): The value of the metric.
        metric_unit (str): The unit of the metric.
        school_id (int): The ID of the school associated with the metric.
        context (str): Additional context for the metric.
        date (date): The date of the metric.
        hour (int): The hour of the metric (for hourly data).
        created_at (datetime): The timestamp of the record.
    """
    __tablename__ = 'system_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Metric information
    metric_name = db.Column(db.String(100), nullable=False)
    metric_value = db.Column(db.Float, nullable=False)
    metric_unit = db.Column(db.String(20), nullable=True)  # 'count', 'percentage', 'seconds', etc.
    
    # Context information
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)
    context = db.Column(db.String(100), nullable=True)  # Additional context
    
    # Time period
    date = db.Column(db.Date, nullable=False)
    hour = db.Column(db.Integer, nullable=True)  # For hourly metrics
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    school = db.relationship('School', backref='metrics', lazy=True)
    
    # Index for efficient querying
    __table_args__ = (
        db.Index('idx_metrics_name_date', 'metric_name', 'date'),
        db.Index('idx_metrics_school_date', 'school_id', 'date'),
    )
    
    def __repr__(self):
        return f'<SystemMetrics {self.metric_name}: {self.metric_value} {self.metric_unit or ""}>'
    
    @classmethod
    def record_metric(cls, metric_name, metric_value, metric_unit=None, 
                     school_id=None, context=None, date=None, hour=None):
        """Creates and saves a new system metric record.

        Args:
            metric_name (str): The name of the metric.
            metric_value (float): The value of the metric.
            metric_unit (str, optional): The unit of the metric.
            school_id (int, optional): The ID of the associated school.
            context (str, optional): Additional context.
            date (date, optional): The date of the metric. Defaults to today.
            hour (int, optional): The hour of the metric.

        Returns:
            SystemMetrics: The newly created metric object.
        """
        if date is None:
            date = datetime.utcnow().date()
        
        metric = cls(
            metric_name=metric_name,
            metric_value=metric_value,
            metric_unit=metric_unit,
            school_id=school_id,
            context=context,
            date=date,
            hour=hour
        )
        db.session.add(metric)
        return metric
    
    def to_dict(self):
        """Serializes the SystemMetrics object to a dictionary.

        Returns:
            dict: A dictionary representation of the system metric.
        """
        return {
            'id': self.id,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'metric_unit': self.metric_unit,
            'school_id': self.school_id,
            'context': self.context,
            'date': self.date.isoformat() if self.date else None,
            'hour': self.hour,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }