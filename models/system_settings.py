"""Data models for system settings and backups.

This module defines the `SystemSettings` model for managing school-specific
configurations and the `SchoolBackup` model for tracking data backups.
"""
from extensions import db
from datetime import datetime
from enum import Enum


class SettingType(Enum):
    """Enumeration for the data type of a setting."""
    STRING = 'string'
    INTEGER = 'integer'
    FLOAT = 'float'
    BOOLEAN = 'boolean'
    JSON = 'json'
    DATE = 'date'


class SystemSettings(db.Model):
    """Represents a single configuration setting for a school.

    This model provides a key-value store for school-specific settings,
    allowing for flexible configuration of the application.

    Attributes:
        id (int): Primary key.
        school_id (int): Foreign key for the school.
        key (str): The unique key for the setting.
        value (str): The value of the setting.
        setting_type (SettingType): The data type of the setting.
        category (str): The category of the setting.
        display_name (str): A human-readable name for the setting.
        description (str): A description of the setting.
    """
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    
    # Setting information
    key = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Text, nullable=True)
    setting_type = db.Column(db.Enum(SettingType), default=SettingType.STRING)
    
    # Setting metadata
    category = db.Column(db.String(50), nullable=False)  # 'general', 'academic', 'notification', 'payment', etc.
    display_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Validation and constraints
    is_required = db.Column(db.Boolean, default=False)
    default_value = db.Column(db.Text, nullable=True)
    validation_rules = db.Column(db.Text, nullable=True)  # JSON string for validation rules
    
    # Access control
    is_public = db.Column(db.Boolean, default=False)  # Can be accessed by non-admin users
    is_editable = db.Column(db.Boolean, default=True)  # Can be modified
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    school = db.relationship('School', backref='system_settings', lazy=True)
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('school_id', 'key', name='unique_school_setting_key'),
    )
    
    def __repr__(self):
        return f'<SystemSettings {self.key}={self.value}>'
    
    def get_typed_value(self):
        """Returns the setting's value converted to its proper data type.

        Returns:
            The typed value of the setting.
        """
        if self.value is None:
            return None
        
        try:
            if self.setting_type == SettingType.INTEGER:
                return int(self.value)
            elif self.setting_type == SettingType.FLOAT:
                return float(self.value)
            elif self.setting_type == SettingType.BOOLEAN:
                return self.value.lower() in ('true', '1', 'yes', 'on')
            elif self.setting_type == SettingType.JSON:
                import json
                return json.loads(self.value)
            elif self.setting_type == SettingType.DATE:
                from datetime import datetime
                return datetime.fromisoformat(self.value).date()
            else:
                return self.value
        except (ValueError, TypeError):
            return self.default_value
    
    def set_typed_value(self, value):
        """Sets the setting's value, converting it to a string.

        Args:
            value: The new value for the setting.
        """
        if value is None:
            self.value = None
            return
        
        if self.setting_type == SettingType.JSON:
            import json
            self.value = json.dumps(value)
        elif self.setting_type == SettingType.DATE:
            if hasattr(value, 'isoformat'):
                self.value = value.isoformat()
            else:
                self.value = str(value)
        else:
            self.value = str(value)
    
    def to_dict(self):
        """Serializes the SystemSettings object to a dictionary.

        Returns:
            dict: A dictionary representation of the setting.
        """
        return {
            'id': self.id,
            'school_id': self.school_id,
            'key': self.key,
            'value': self.value,
            'typed_value': self.get_typed_value(),
            'setting_type': self.setting_type.value,
            'category': self.category,
            'display_name': self.display_name,
            'description': self.description,
            'is_required': self.is_required,
            'default_value': self.default_value,
            'validation_rules': self.validation_rules,
            'is_public': self.is_public,
            'is_editable': self.is_editable,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SchoolBackup(db.Model):
    """Represents a backup of a school's data.

    Attributes:
        id (int): Primary key.
        school_id (int): Foreign key for the school.
        created_by (int): Foreign key for the user who created the backup.
        backup_name (str): The name of the backup.
        backup_type (str): The type of backup ('manual', 'automatic').
        file_path (str): The path to the backup file.
        file_size (int): The size of the backup file in bytes.
        status (str): The status of the backup.
    """
    __tablename__ = 'school_backups'
    
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Backup information
    backup_name = db.Column(db.String(200), nullable=False)
    backup_type = db.Column(db.String(20), nullable=False)  # 'manual', 'automatic', 'scheduled'
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.BigInteger, nullable=True)  # Size in bytes
    
    # Backup content
    includes_students = db.Column(db.Boolean, default=True)
    includes_teachers = db.Column(db.Boolean, default=True)
    includes_classes = db.Column(db.Boolean, default=True)
    includes_fees = db.Column(db.Boolean, default=True)
    includes_attendance = db.Column(db.Boolean, default=True)
    includes_assignments = db.Column(db.Boolean, default=True)
    includes_settings = db.Column(db.Boolean, default=True)
    
    # Status and metadata
    status = db.Column(db.String(20), default='completed')  # 'in_progress', 'completed', 'failed'
    compression_type = db.Column(db.String(10), default='zip')
    checksum = db.Column(db.String(64), nullable=True)  # MD5 or SHA256 checksum
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    school = db.relationship('School', backref='backups', lazy=True)
    creator = db.relationship('User', backref='created_backups', lazy=True)
    
    def __repr__(self):
        return f'<SchoolBackup {self.backup_name} ({self.status})>'
    
    def get_file_size_mb(self):
        """Returns the file size in megabytes."""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0
    
    def to_dict(self):
        """Serializes the SchoolBackup object to a dictionary.

        Returns:
            dict: A dictionary representation of the backup.
        """
        return {
            'id': self.id,
            'school_id': self.school_id,
            'created_by': self.created_by,
            'backup_name': self.backup_name,
            'backup_type': self.backup_type,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_size_mb': self.get_file_size_mb(),
            'includes_students': self.includes_students,
            'includes_teachers': self.includes_teachers,
            'includes_classes': self.includes_classes,
            'includes_fees': self.includes_fees,
            'includes_attendance': self.includes_attendance,
            'includes_assignments': self.includes_assignments,
            'includes_settings': self.includes_settings,
            'status': self.status,
            'compression_type': self.compression_type,
            'checksum': self.checksum,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }