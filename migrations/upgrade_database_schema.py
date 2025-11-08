"""
Database schema upgrade script for enhanced school management system
"""
from extensions import db
from sqlalchemy import text


def upgrade_database():
    """Upgrade database schema with new fields and tables"""
    
    print("🔧 Upgrading database schema...")
    
    try:
        # Add new fields to students table
        print("📚 Enhancing students table...")
        db.session.execute(text("""
            ALTER TABLE students 
            ADD COLUMN IF NOT EXISTS city VARCHAR(100),
            ADD COLUMN IF NOT EXISTS state VARCHAR(100),
            ADD COLUMN IF NOT EXISTS pincode VARCHAR(10)
        """))
        
        # Add new fields to teachers table
        print("👩‍🏫 Enhancing teachers table...")
        db.session.execute(text("""
            ALTER TABLE teachers 
            ADD COLUMN IF NOT EXISTS city VARCHAR(100),
            ADD COLUMN IF NOT EXISTS state VARCHAR(100),
            ADD COLUMN IF NOT EXISTS pincode VARCHAR(10),
            ADD COLUMN IF NOT EXISTS gender VARCHAR(10),
            ADD COLUMN IF NOT EXISTS blood_group VARCHAR(10),
            ADD COLUMN IF NOT EXISTS marital_status VARCHAR(20),
            ADD COLUMN IF NOT EXISTS aadhaar_number VARCHAR(20),
            ADD COLUMN IF NOT EXISTS pan_number VARCHAR(20),
            ADD COLUMN IF NOT EXISTS nationality VARCHAR(50) DEFAULT 'Indian',
            ADD COLUMN IF NOT EXISTS religion VARCHAR(50),
            ADD COLUMN IF NOT EXISTS languages_known VARCHAR(200),
            ADD COLUMN IF NOT EXISTS communication_preference VARCHAR(20) DEFAULT 'WhatsApp'
        """))
        
        # Enhance assignments table
        print("📝 Enhancing assignments table...")
        db.session.execute(text("""
            ALTER TABLE assignments 
            ADD COLUMN IF NOT EXISTS assignment_type VARCHAR(20) DEFAULT 'homework',
            ADD COLUMN IF NOT EXISTS file_type VARCHAR(20),
            ADD COLUMN IF NOT EXISTS posted_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active',
            ADD COLUMN IF NOT EXISTS allow_submissions BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS max_file_size INTEGER DEFAULT 10485760,
            ADD COLUMN IF NOT EXISTS total_marks INTEGER,
            ADD COLUMN IF NOT EXISTS remarks TEXT
        """))
        
        # Create holidays table
        print("🎉 Creating holidays table...")
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS holidays (
                id SERIAL PRIMARY KEY,
                school_id INTEGER NOT NULL REFERENCES schools(id),
                created_by INTEGER NOT NULL REFERENCES users(id),
                title VARCHAR(200) NOT NULL,
                description TEXT,
                start_date DATE NOT NULL,
                end_date DATE,
                notify_teachers BOOLEAN DEFAULT TRUE,
                notify_students BOOLEAN DEFAULT TRUE,
                notify_parents BOOLEAN DEFAULT TRUE,
                status VARCHAR(20) DEFAULT 'upcoming',
                is_recurring BOOLEAN DEFAULT FALSE,
                recurrence_pattern VARCHAR(50),
                notifications_sent BOOLEAN DEFAULT FALSE,
                notification_sent_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create notification_templates table
        print("📧 Creating notification_templates table...")
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS notification_templates (
                id SERIAL PRIMARY KEY,
                school_id INTEGER NOT NULL REFERENCES schools(id),
                name VARCHAR(100) NOT NULL,
                type VARCHAR(30) NOT NULL,
                channel VARCHAR(20) NOT NULL,
                subject VARCHAR(200),
                message_template TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                is_default BOOLEAN DEFAULT FALSE,
                available_variables TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create notification_logs table
        print("📋 Creating notification_logs table...")
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS notification_logs (
                id SERIAL PRIMARY KEY,
                school_id INTEGER NOT NULL REFERENCES schools(id),
                template_id INTEGER REFERENCES notification_templates(id),
                recipient_type VARCHAR(20) NOT NULL,
                recipient_id INTEGER,
                recipient_phone VARCHAR(15),
                recipient_email VARCHAR(120),
                recipient_name VARCHAR(100),
                type VARCHAR(30) NOT NULL,
                channel VARCHAR(20) NOT NULL,
                subject VARCHAR(200),
                message TEXT NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                sent_at TIMESTAMP,
                delivered_at TIMESTAMP,
                read_at TIMESTAMP,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                external_id VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create system_settings table
        print("⚙️ Creating system_settings table...")
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS system_settings (
                id SERIAL PRIMARY KEY,
                school_id INTEGER NOT NULL REFERENCES schools(id),
                key VARCHAR(100) NOT NULL,
                value TEXT,
                setting_type VARCHAR(20) DEFAULT 'string',
                category VARCHAR(50) NOT NULL,
                display_name VARCHAR(200) NOT NULL,
                description TEXT,
                is_required BOOLEAN DEFAULT FALSE,
                default_value TEXT,
                validation_rules TEXT,
                is_public BOOLEAN DEFAULT FALSE,
                is_editable BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(school_id, key)
            )
        """))
        
        # Create school_backups table
        print("💾 Creating school_backups table...")
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS school_backups (
                id SERIAL PRIMARY KEY,
                school_id INTEGER NOT NULL REFERENCES schools(id),
                created_by INTEGER NOT NULL REFERENCES users(id),
                backup_name VARCHAR(200) NOT NULL,
                backup_type VARCHAR(20) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                file_size BIGINT,
                includes_students BOOLEAN DEFAULT TRUE,
                includes_teachers BOOLEAN DEFAULT TRUE,
                includes_classes BOOLEAN DEFAULT TRUE,
                includes_fees BOOLEAN DEFAULT TRUE,
                includes_attendance BOOLEAN DEFAULT TRUE,
                includes_assignments BOOLEAN DEFAULT TRUE,
                includes_settings BOOLEAN DEFAULT TRUE,
                status VARCHAR(20) DEFAULT 'completed',
                compression_type VARCHAR(10) DEFAULT 'zip',
                checksum VARCHAR(64),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """))
        
        # Create indexes for better performance
        print("🚀 Creating database indexes...")
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_students_school_class ON students(school_id, class_id)"))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_teachers_school ON teachers(school_id)"))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_assignments_class_subject ON assignments(class_id, subject_id)"))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_holidays_school_date ON holidays(school_id, start_date)"))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_notification_logs_school_type ON notification_logs(school_id, type)"))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_system_settings_school_category ON system_settings(school_id, category)"))
        
        # Insert default notification templates
        print("📝 Creating default notification templates...")
        insert_default_templates()
        
        # Insert default system settings
        print("⚙️ Creating default system settings...")
        insert_default_settings()
        
        db.session.commit()
        print("✅ Database schema upgrade completed successfully!")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error upgrading database schema: {str(e)}")
        raise


def insert_default_templates():
    """Insert default notification templates"""
    
    # Check if we're using SQLite or PostgreSQL
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    
    # Default templates for all schools
    default_templates = [
        {
            'name': 'Attendance Alert SMS',
            'type': 'attendance_alert',
            'channel': 'sms',
            'message_template': 'Dear Parent, Your child {{student_name}} (Class {{class_name}}) was marked ABSENT on {{date}}. Please ensure regular attendance. - {{school_name}}'
        },
        {
            'name': 'Attendance Alert WhatsApp',
            'type': 'attendance_alert',
            'channel': 'whatsapp',
            'message_template': '👋 Dear Parent, This is to inform you that your child {{student_name}} (Class: {{class_name}}) was absent on {{date}}. Please contact the class teacher if needed. 📘 Regards, {{school_name}}'
        },
        {
            'name': 'Fee Payment Confirmation',
            'type': 'fee_confirmation',
            'channel': 'sms',
            'message_template': 'Fee payment of ₹{{amount}} received for {{student_name}} on {{date}}. Receipt: {{receipt_no}}. Thank you! - {{school_name}}'
        },
        {
            'name': 'Holiday Announcement',
            'type': 'holiday_announcement',
            'channel': 'whatsapp',
            'message_template': '🎉 Holiday Announcement: {{holiday_title}} on {{date}}. {{description}} Have a great day! - {{school_name}}'
        },
        {
            'name': 'Assignment Notification',
            'type': 'assignment_notification',
            'channel': 'whatsapp',
            'message_template': '📚 New Assignment: {{assignment_title}} has been posted for {{class_name}} - {{subject_name}}. Due date: {{due_date}}. Please check the student portal. - {{school_name}}'
        }
    ]
    
    # Get all schools to create templates for each
    schools = db.session.execute(text("SELECT id FROM schools")).fetchall()
    
    for school in schools:
        school_id = school[0]
        for template in default_templates:
            # Check if template already exists
            existing = db.session.execute(text("""
                SELECT id FROM notification_templates 
                WHERE school_id = :school_id AND name = :name
            """), {'school_id': school_id, 'name': template['name']}).fetchone()
            
            if not existing:
                db.session.execute(text("""
                    INSERT INTO notification_templates 
                    (school_id, name, type, channel, message_template, is_active, is_default)
                    VALUES (:school_id, :name, :type, :channel, :message_template, TRUE, TRUE)
                """), {
                    'school_id': school_id,
                    'name': template['name'],
                    'type': template['type'],
                    'channel': template['channel'],
                    'message_template': template['message_template']
                })


def insert_default_settings():
    """Insert default system settings"""
    
    default_settings = [
        {
            'key': 'academic_year_start',
            'value': '2024-04-01',
            'setting_type': 'date',
            'category': 'academic',
            'display_name': 'Academic Year Start Date',
            'description': 'Start date of the academic year'
        },
        {
            'key': 'academic_year_end',
            'value': '2025-03-31',
            'setting_type': 'date',
            'category': 'academic',
            'display_name': 'Academic Year End Date',
            'description': 'End date of the academic year'
        },
        {
            'key': 'fee_currency',
            'value': 'INR',
            'setting_type': 'string',
            'category': 'financial',
            'display_name': 'Fee Currency',
            'description': 'Currency for fee calculations'
        },
        {
            'key': 'attendance_time',
            'value': '09:00',
            'setting_type': 'string',
            'category': 'academic',
            'display_name': 'Default Attendance Time',
            'description': 'Default time for marking attendance'
        },
        {
            'key': 'enable_sms_notifications',
            'value': 'true',
            'setting_type': 'boolean',
            'category': 'notification',
            'display_name': 'Enable SMS Notifications',
            'description': 'Enable or disable SMS notifications'
        },
        {
            'key': 'enable_whatsapp_notifications',
            'value': 'true',
            'setting_type': 'boolean',
            'category': 'notification',
            'display_name': 'Enable WhatsApp Notifications',
            'description': 'Enable or disable WhatsApp notifications'
        },
        {
            'key': 'auto_backup_enabled',
            'value': 'true',
            'setting_type': 'boolean',
            'category': 'system',
            'display_name': 'Enable Auto Backup',
            'description': 'Enable automatic daily backups'
        },
        {
            'key': 'max_file_upload_size',
            'value': '10485760',
            'setting_type': 'integer',
            'category': 'system',
            'display_name': 'Max File Upload Size (bytes)',
            'description': 'Maximum file upload size in bytes (10MB default)'
        }
    ]
    
    # Get all schools to create settings for each
    schools = db.session.execute(text("SELECT id FROM schools")).fetchall()
    
    for school in schools:
        school_id = school[0]
        for setting in default_settings:
            # Check if setting already exists
            existing = db.session.execute(text("""
                SELECT id FROM system_settings 
                WHERE school_id = :school_id AND key = :key
            """), {'school_id': school_id, 'key': setting['key']}).fetchone()
            
            if not existing:
                db.session.execute(text("""
                    INSERT INTO system_settings 
                    (school_id, key, value, setting_type, category, display_name, description, default_value)
                    VALUES (:school_id, :key, :value, :setting_type, :category, :display_name, :description, :value)
                """), {
                    'school_id': school_id,
                    'key': setting['key'],
                    'value': setting['value'],
                    'setting_type': setting['setting_type'],
                    'category': setting['category'],
                    'display_name': setting['display_name'],
                    'description': setting['description']
                })


if __name__ == '__main__':
    import sys
    import os
    
    # Add the parent directory to the path so we can import modules
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from app import create_app
    
    app = create_app()
    with app.app_context():
        upgrade_database()