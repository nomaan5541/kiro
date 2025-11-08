"""
Create enhanced models and update database schema
"""
from app import create_app
from extensions import db
from sqlalchemy import text

# Import all models to ensure they're registered
from models.student import Student
from models.teacher import Teacher
from models.assignment import Assignment, AssignmentStatus, AssignmentType
from models.classes import Class, Subject
from models.holiday import Holiday, HolidayStatus
from models.notification import NotificationTemplate, NotificationLog, NotificationType, NotificationChannel, DeliveryStatus
from models.system_settings import SystemSettings, SchoolBackup, SettingType


def create_enhanced_database():
    """Create enhanced database with all new models"""
    
    print("🔧 Creating enhanced database schema...")
    
    try:
        # Create all tables
        print("📊 Creating database tables...")
        db.create_all()
        
        # Add new columns to existing tables if they don't exist
        print("🔄 Adding new columns to existing tables...")
        
        # Check if columns exist before adding them
        inspector = db.inspect(db.engine)
        
        # Add columns to students table
        student_columns = [col['name'] for col in inspector.get_columns('students')]
        if 'city' not in student_columns:
            db.session.execute(text("ALTER TABLE students ADD COLUMN city VARCHAR(100)"))
        if 'state' not in student_columns:
            db.session.execute(text("ALTER TABLE students ADD COLUMN state VARCHAR(100)"))
        if 'pincode' not in student_columns:
            db.session.execute(text("ALTER TABLE students ADD COLUMN pincode VARCHAR(10)"))
        
        # Add columns to teachers table
        teacher_columns = [col['name'] for col in inspector.get_columns('teachers')]
        new_teacher_columns = [
            ('city', 'VARCHAR(100)'),
            ('state', 'VARCHAR(100)'),
            ('pincode', 'VARCHAR(10)'),
            ('gender', 'VARCHAR(10)'),
            ('blood_group', 'VARCHAR(10)'),
            ('marital_status', 'VARCHAR(20)'),
            ('aadhaar_number', 'VARCHAR(20)'),
            ('pan_number', 'VARCHAR(20)'),
            ('nationality', 'VARCHAR(50)'),
            ('religion', 'VARCHAR(50)'),
            ('languages_known', 'VARCHAR(200)'),
            ('communication_preference', 'VARCHAR(20)')
        ]
        
        for col_name, col_type in new_teacher_columns:
            if col_name not in teacher_columns:
                db.session.execute(text(f"ALTER TABLE teachers ADD COLUMN {col_name} {col_type}"))
        
        # Add columns to assignments table
        assignment_columns = [col['name'] for col in inspector.get_columns('assignments')]
        new_assignment_columns = [
            ('assignment_type', 'VARCHAR(20)'),
            ('file_type', 'VARCHAR(20)'),
            ('posted_on', 'TIMESTAMP'),
            ('status', 'VARCHAR(20)'),
            ('allow_submissions', 'BOOLEAN'),
            ('max_file_size', 'INTEGER'),
            ('total_marks', 'INTEGER'),
            ('remarks', 'TEXT')
        ]
        
        for col_name, col_type in new_assignment_columns:
            if col_name not in assignment_columns:
                if col_name == 'posted_on':
                    db.session.execute(text(f"ALTER TABLE assignments ADD COLUMN {col_name} {col_type} DEFAULT CURRENT_TIMESTAMP"))
                elif col_name == 'assignment_type':
                    db.session.execute(text(f"ALTER TABLE assignments ADD COLUMN {col_name} {col_type} DEFAULT 'homework'"))
                elif col_name == 'status':
                    db.session.execute(text(f"ALTER TABLE assignments ADD COLUMN {col_name} {col_type} DEFAULT 'active'"))
                elif col_name == 'allow_submissions':
                    db.session.execute(text(f"ALTER TABLE assignments ADD COLUMN {col_name} {col_type} DEFAULT FALSE"))
                elif col_name == 'max_file_size':
                    db.session.execute(text(f"ALTER TABLE assignments ADD COLUMN {col_name} {col_type} DEFAULT 10485760"))
                else:
                    db.session.execute(text(f"ALTER TABLE assignments ADD COLUMN {col_name} {col_type}"))
        
        # Create indexes for better performance
        print("🚀 Creating database indexes...")
        try:
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_students_school_class ON students(school_id, class_id)"))
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_teachers_school ON teachers(school_id)"))
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_assignments_class_subject ON assignments(class_id, subject_id)"))
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_holidays_school_date ON holidays(school_id, start_date)"))
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_notification_logs_school_type ON notification_logs(school_id, type)"))
            db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_system_settings_school_category ON system_settings(school_id, category)"))
        except Exception as e:
            print(f"⚠️ Some indexes may already exist: {e}")
        
        # Skip template insertion for now - will be done later
        print("📝 Skipping template insertion for now...")
        
        # Skip settings insertion for now - will be done later  
        print("⚙️ Skipping settings insertion for now...")
        
        db.session.commit()
        print("✅ Enhanced database schema created successfully!")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creating enhanced database: {str(e)}")
        raise


def insert_default_templates():
    """Insert default notification templates"""
    
    # Default templates for all schools
    default_templates = [
        {
            'name': 'Attendance Alert SMS',
            'type': NotificationType.ATTENDANCE_ALERT,
            'channel': NotificationChannel.SMS,
            'message_template': 'Dear Parent, Your child {{student_name}} (Class {{class_name}}) was marked ABSENT on {{date}}. Please ensure regular attendance. - {{school_name}}'
        },
        {
            'name': 'Attendance Alert WhatsApp',
            'type': NotificationType.ATTENDANCE_ALERT,
            'channel': NotificationChannel.WHATSAPP,
            'message_template': '👋 Dear Parent, This is to inform you that your child {{student_name}} (Class: {{class_name}}) was absent on {{date}}. Please contact the class teacher if needed. 📘 Regards, {{school_name}}'
        },
        {
            'name': 'Fee Payment Confirmation',
            'type': NotificationType.FEE_CONFIRMATION,
            'channel': NotificationChannel.SMS,
            'message_template': 'Fee payment of ₹{{amount}} received for {{student_name}} on {{date}}. Receipt: {{receipt_no}}. Thank you! - {{school_name}}'
        },
        {
            'name': 'Holiday Announcement',
            'type': NotificationType.HOLIDAY_ANNOUNCEMENT,
            'channel': NotificationChannel.WHATSAPP,
            'message_template': '🎉 Holiday Announcement: {{holiday_title}} on {{date}}. {{description}} Have a great day! - {{school_name}}'
        },
        {
            'name': 'Assignment Notification',
            'type': NotificationType.ASSIGNMENT_NOTIFICATION,
            'channel': NotificationChannel.WHATSAPP,
            'message_template': '📚 New Assignment: {{assignment_title}} has been posted for {{class_name}} - {{subject_name}}. Due date: {{due_date}}. Please check the student portal. - {{school_name}}'
        }
    ]
    
    # Get all schools to create templates for each (using raw SQL to avoid enum issues)
    schools = db.session.execute(db.text("SELECT id FROM schools")).fetchall()
    
    for school in schools:
        school_id = school[0]
        for template_data in default_templates:
            # Check if template already exists
            existing = NotificationTemplate.query.filter_by(
                school_id=school_id,
                name=template_data['name']
            ).first()
            
            if not existing:
                template = NotificationTemplate(
                    school_id=school_id,
                    name=template_data['name'],
                    type=template_data['type'],
                    channel=template_data['channel'],
                    message_template=template_data['message_template'],
                    is_active=True,
                    is_default=True
                )
                db.session.add(template)


def insert_default_settings():
    """Insert default system settings"""
    
    default_settings = [
        {
            'key': 'academic_year_start',
            'value': '2024-04-01',
            'setting_type': SettingType.DATE,
            'category': 'academic',
            'display_name': 'Academic Year Start Date',
            'description': 'Start date of the academic year'
        },
        {
            'key': 'academic_year_end',
            'value': '2025-03-31',
            'setting_type': SettingType.DATE,
            'category': 'academic',
            'display_name': 'Academic Year End Date',
            'description': 'End date of the academic year'
        },
        {
            'key': 'fee_currency',
            'value': 'INR',
            'setting_type': SettingType.STRING,
            'category': 'financial',
            'display_name': 'Fee Currency',
            'description': 'Currency for fee calculations'
        },
        {
            'key': 'attendance_time',
            'value': '09:00',
            'setting_type': SettingType.STRING,
            'category': 'academic',
            'display_name': 'Default Attendance Time',
            'description': 'Default time for marking attendance'
        },
        {
            'key': 'enable_sms_notifications',
            'value': 'true',
            'setting_type': SettingType.BOOLEAN,
            'category': 'notification',
            'display_name': 'Enable SMS Notifications',
            'description': 'Enable or disable SMS notifications'
        },
        {
            'key': 'enable_whatsapp_notifications',
            'value': 'true',
            'setting_type': SettingType.BOOLEAN,
            'category': 'notification',
            'display_name': 'Enable WhatsApp Notifications',
            'description': 'Enable or disable WhatsApp notifications'
        },
        {
            'key': 'auto_backup_enabled',
            'value': 'true',
            'setting_type': SettingType.BOOLEAN,
            'category': 'system',
            'display_name': 'Enable Auto Backup',
            'description': 'Enable automatic daily backups'
        },
        {
            'key': 'max_file_upload_size',
            'value': '10485760',
            'setting_type': SettingType.INTEGER,
            'category': 'system',
            'display_name': 'Max File Upload Size (bytes)',
            'description': 'Maximum file upload size in bytes (10MB default)'
        }
    ]
    
    # Get all schools to create settings for each (using raw SQL to avoid enum issues)
    schools = db.session.execute(db.text("SELECT id FROM schools")).fetchall()
    
    for school in schools:
        school_id = school[0]
        for setting_data in default_settings:
            # Check if setting already exists
            existing = SystemSettings.query.filter_by(
                school_id=school_id,
                key=setting_data['key']
            ).first()
            
            if not existing:
                setting = SystemSettings(
                    school_id=school_id,
                    key=setting_data['key'],
                    value=setting_data['value'],
                    setting_type=setting_data['setting_type'],
                    category=setting_data['category'],
                    display_name=setting_data['display_name'],
                    description=setting_data['description'],
                    default_value=setting_data['value']
                )
                db.session.add(setting)


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        create_enhanced_database()