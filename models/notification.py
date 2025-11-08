"""
Notification models for managing message templates and delivery tracking
"""
from extensions import db
from datetime import datetime
from enum import Enum


class NotificationType(Enum):
    ATTENDANCE_ALERT = 'attendance_alert'
    FEE_REMINDER = 'fee_reminder'
    FEE_CONFIRMATION = 'fee_confirmation'
    HOLIDAY_ANNOUNCEMENT = 'holiday_announcement'
    EXAM_NOTIFICATION = 'exam_notification'
    GENERAL_ANNOUNCEMENT = 'general_announcement'
    ASSIGNMENT_NOTIFICATION = 'assignment_notification'


class NotificationChannel(Enum):
    SMS = 'sms'
    WHATSAPP = 'whatsapp'
    EMAIL = 'email'
    IN_APP = 'in_app'


class DeliveryStatus(Enum):
    PENDING = 'pending'
    SENT = 'sent'
    DELIVERED = 'delivered'
    FAILED = 'failed'
    READ = 'read'


class NotificationTemplate(db.Model):
    """Template model for notification messages"""
    __tablename__ = 'notification_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    
    # Template information
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.Enum(NotificationType), nullable=False)
    channel = db.Column(db.Enum(NotificationChannel), nullable=False)
    
    # Template content
    subject = db.Column(db.String(200), nullable=True)  # For email notifications
    message_template = db.Column(db.Text, nullable=False)
    
    # Template settings
    is_active = db.Column(db.Boolean, default=True)
    is_default = db.Column(db.Boolean, default=False)
    
    # Available variables (JSON string)
    available_variables = db.Column(db.Text, nullable=True)  # JSON string of available variables
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    school = db.relationship('School', backref='notification_templates', lazy=True)
    
    def __repr__(self):
        return f'<NotificationTemplate {self.name} ({self.type.value})>'
    
    def render_message(self, variables):
        """Render message template with provided variables"""
        message = self.message_template
        for key, value in variables.items():
            placeholder = f'{{{{{key}}}}}'
            message = message.replace(placeholder, str(value))
        return message
    
    def to_dict(self):
        """Convert template to dictionary"""
        return {
            'id': self.id,
            'school_id': self.school_id,
            'name': self.name,
            'type': self.type.value,
            'channel': self.channel.value,
            'subject': self.subject,
            'message_template': self.message_template,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'available_variables': self.available_variables,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class NotificationLog(db.Model):
    """Log model for tracking sent notifications"""
    __tablename__ = 'notification_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('notification_templates.id'), nullable=True)
    
    # Recipient information
    recipient_type = db.Column(db.String(20), nullable=False)  # 'student', 'parent', 'teacher'
    recipient_id = db.Column(db.Integer, nullable=True)  # ID of the recipient
    recipient_phone = db.Column(db.String(15), nullable=True)
    recipient_email = db.Column(db.String(120), nullable=True)
    recipient_name = db.Column(db.String(100), nullable=True)
    
    # Message details
    type = db.Column(db.Enum(NotificationType), nullable=False)
    channel = db.Column(db.Enum(NotificationChannel), nullable=False)
    subject = db.Column(db.String(200), nullable=True)
    message = db.Column(db.Text, nullable=False)
    
    # Delivery tracking
    status = db.Column(db.Enum(DeliveryStatus), default=DeliveryStatus.PENDING)
    sent_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    read_at = db.Column(db.DateTime, nullable=True)
    
    # Error tracking
    error_message = db.Column(db.Text, nullable=True)
    retry_count = db.Column(db.Integer, default=0)
    
    # External service tracking
    external_id = db.Column(db.String(100), nullable=True)  # ID from SMS/WhatsApp service
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    school = db.relationship('School', backref='notification_logs', lazy=True)
    template = db.relationship('NotificationTemplate', backref='notification_logs', lazy=True)
    
    def __repr__(self):
        return f'<NotificationLog {self.type.value} to {self.recipient_name} ({self.status.value})>'
    
    def mark_sent(self, external_id=None):
        """Mark notification as sent"""
        self.status = DeliveryStatus.SENT
        self.sent_at = datetime.utcnow()
        if external_id:
            self.external_id = external_id
    
    def mark_delivered(self):
        """Mark notification as delivered"""
        self.status = DeliveryStatus.DELIVERED
        self.delivered_at = datetime.utcnow()
    
    def mark_failed(self, error_message):
        """Mark notification as failed"""
        self.status = DeliveryStatus.FAILED
        self.error_message = error_message
    
    def to_dict(self):
        """Convert log to dictionary"""
        return {
            'id': self.id,
            'school_id': self.school_id,
            'template_id': self.template_id,
            'recipient_type': self.recipient_type,
            'recipient_id': self.recipient_id,
            'recipient_phone': self.recipient_phone,
            'recipient_email': self.recipient_email,
            'recipient_name': self.recipient_name,
            'type': self.type.value,
            'channel': self.channel.value,
            'subject': self.subject,
            'message': self.message,
            'status': self.status.value,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'external_id': self.external_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }