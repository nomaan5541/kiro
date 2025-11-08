"""
Database initialization script
"""
from app import create_app
from extensions import db, bcrypt
from models.user import User, UserRole
from models.school import School, SchoolStatus
from models import Class, Subject
from models.student import Student, StudentStatus
from models.attendance import Attendance, AttendanceStatus, AttendanceSummary
from models.fee import FeeStructure, Payment, PaymentHistory, StudentFeeStatus, PaymentMode, PaymentStatus
from models.activity import ActivityLog, SystemMetrics, ActivityType
from models.notification import NotificationTemplate, NotificationLog, NotificationType, NotificationChannel, DeliveryStatus
from datetime import datetime, timedelta, date
from decimal import Decimal
import json


def init_database():
    """Initialize database with sample data"""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if super admin already exists
        super_admin = User.query.filter_by(role=UserRole.SUPER_ADMIN).first()
        
        if not super_admin:
            # Create default super admin
            password_hash = bcrypt.generate_password_hash('admin123').decode('utf-8')
            super_admin = User(
                name='Super Administrator',
                email='admin@schoolsystem.com',
                password_hash=password_hash,
                role=UserRole.SUPER_ADMIN
            )
            db.session.add(super_admin)
            
            print("Created super admin user:")
            print("Email: admin@schoolsystem.com")
            print("Password: admin123")
            print()
        
        # Create sample school for testing
        sample_school = School.query.filter_by(email='demo@school.com').first()
        
        if not sample_school:
            sample_school = School(
                name='Demo School',
                email='demo@school.com',
                phone='1234567890',
                address='123 Demo Street, Demo City',
                subscription_start=datetime.utcnow(),
                subscription_end=datetime.utcnow() + timedelta(days=365),
                status=SchoolStatus.ACTIVE,
                setup_completed=True  # Mark as completed for testing
            )
            db.session.add(sample_school)
            db.session.flush()  # Get school ID
            
            # Create school admin for demo school
            password_hash = bcrypt.generate_password_hash('school123').decode('utf-8')
            school_admin = User(
                name='Demo School Admin',
                email='demo@school.com',
                password_hash=password_hash,
                role=UserRole.SCHOOL_ADMIN,
                school_id=sample_school.id
            )
            db.session.add(school_admin)
            
            # Create teacher user
            teacher_password_hash = bcrypt.generate_password_hash('teacher123').decode('utf-8')
            teacher_user = User(
                name='John Smith',
                email='teacher@demo.com',
                password_hash=teacher_password_hash,
                role=UserRole.TEACHER,
                school_id=sample_school.id
            )
            db.session.add(teacher_user)
            db.session.flush()  # Get user ID
            
            # Create teacher profile
            from models.teacher import Teacher, TeacherStatus, TeacherClassAssignment, TeacherSubjectAssignment
            teacher_profile = Teacher(
                user_id=teacher_user.id,
                school_id=sample_school.id,
                employee_id='TCH001',
                designation='Senior Teacher',
                department='Mathematics',
                qualification='M.Sc Mathematics, B.Ed',
                experience_years=5,
                phone='9876543220',
                date_of_joining=date(2020, 6, 15),
                status=TeacherStatus.ACTIVE
            )
            db.session.add(teacher_profile)
            db.session.flush()  # Get teacher profile ID
            
            # Create student user
            student_password_hash = bcrypt.generate_password_hash('student123').decode('utf-8')
            student_user = User(
                name='Ravi Kumar',
                email='student@demo.com',
                password_hash=student_password_hash,
                role=UserRole.STUDENT,
                school_id=sample_school.id
            )
            db.session.add(student_user)
            db.session.flush()  # Get user ID
            
            print("Created demo school:")
            print("School: Demo School")
            print("Email: demo@school.com")
            print("Password: school123")
            print()
            print("Created teacher user:")
            print("Email: teacher@demo.com")
            print("Password: teacher123")
            print()
            print("Created student user:")
            print("Email: student@demo.com")
            print("Password: student123")
            print("(For student login, use: Admission: STU001, Phone: 9876543210, DOB: 2010-01-15)")
            print()
            
            # Create sample classes
            class_10a = Class(
                school_id=sample_school.id,
                class_name="Class 10",
                section="A",
                capacity=60,
                academic_year="2024-25"
            )
            db.session.add(class_10a)
            
            class_9a = Class(
                school_id=sample_school.id,
                class_name="Class 9",
                section="A",
                capacity=60,
                academic_year="2024-25"
            )
            db.session.add(class_9a)
            db.session.flush()  # Get class IDs
            
            # Create sample subjects for Class 10A
            subjects_10 = ['English', 'Hindi', 'Mathematics', 'Science', 'Social Science', 'Computer', 'Physical Education']
            math_subject = None
            for subject_name in subjects_10:
                subject = Subject(
                    school_id=sample_school.id,
                    class_id=class_10a.id,
                    name=subject_name,
                    code=subject_name[:3].upper()
                )
                db.session.add(subject)
                if subject_name == 'Mathematics':
                    math_subject = subject
            
            db.session.flush()  # Get subject IDs
            
            # Assign teacher to class and subject
            class_assignment = TeacherClassAssignment(
                teacher_id=teacher_profile.id,
                class_id=class_10a.id,
                school_id=sample_school.id,
                academic_year="2024-25",
                is_class_teacher=True
            )
            db.session.add(class_assignment)
            
            if math_subject:
                subject_assignment = TeacherSubjectAssignment(
                    teacher_id=teacher_profile.id,
                    subject_id=math_subject.id,
                    class_id=class_10a.id,
                    school_id=sample_school.id,
                    academic_year="2024-25"
                )
                db.session.add(subject_assignment)
            
            # Create sample students
            sample_student = Student(
                school_id=sample_school.id,
                class_id=class_10a.id,
                roll_number="10A001",
                admission_no="STU001",
                admission_date=date(2024, 4, 1),
                name="Ravi Kumar",
                father_name="Raj Kumar",
                mother_name="Sunita Kumar",
                gender="male",
                date_of_birth=date(2010, 1, 15),
                phone="9876543210",
                email="ravi.kumar@demo.com",
                address="456 Student Lane, Demo City",
                blood_group="O+",
                status=StudentStatus.ACTIVE
            )
            db.session.add(sample_student)
            
            # Create another sample student
            sample_student2 = Student(
                school_id=sample_school.id,
                class_id=class_10a.id,
                roll_number="10A002",
                admission_no="STU002",
                admission_date=date(2024, 4, 1),
                name="Priya Sharma",
                father_name="Amit Sharma",
                mother_name="Neha Sharma",
                gender="female",
                date_of_birth=date(2010, 3, 20),
                phone="9876543211",
                email="priya.sharma@demo.com",
                address="789 Student Avenue, Demo City",
                blood_group="A+",
                status=StudentStatus.ACTIVE
            )
            db.session.add(sample_student2)
            db.session.flush()  # Get student IDs
            
            # Create fee structure
            fee_structure = FeeStructure(
                school_id=sample_school.id,
                class_id=class_10a.id,
                academic_year="2024-25",
                total_fee=Decimal("50000.00"),
                tuition_fee=Decimal("35000.00"),
                admission_fee=Decimal("5000.00"),
                development_fee=Decimal("3000.00"),
                transport_fee=Decimal("4000.00"),
                library_fee=Decimal("1000.00"),
                lab_fee=Decimal("1500.00"),
                sports_fee=Decimal("500.00"),
                installments=4
            )
            db.session.add(fee_structure)
            db.session.flush()  # Get fee structure ID
            
            # Create student fee status
            student_fee_status1 = StudentFeeStatus(
                school_id=sample_school.id,
                student_id=sample_student.id,
                fee_structure_id=fee_structure.id,
                total_fee=fee_structure.total_fee,
                paid_amount=Decimal("12500.00"),
                remaining_amount=Decimal("37500.00"),
                payment_percentage=25.0,
                next_due_date=date(2024, 7, 1)
            )
            db.session.add(student_fee_status1)
            
            student_fee_status2 = StudentFeeStatus(
                school_id=sample_school.id,
                student_id=sample_student2.id,
                fee_structure_id=fee_structure.id,
                total_fee=fee_structure.total_fee,
                paid_amount=Decimal("25000.00"),
                remaining_amount=Decimal("25000.00"),
                payment_percentage=50.0,
                next_due_date=date(2024, 7, 1)
            )
            db.session.add(student_fee_status2)
            
            # Create notification settings
            notification_settings = NotificationSettings(
                school_id=sample_school.id,
                sms_enabled=False,
                whatsapp_enabled=False,
                email_enabled=False,
                attendance_notifications=True,
                payment_notifications=True,
                fee_reminder_notifications=True,
                auto_attendance_alerts=True,
                auto_payment_confirmations=True,
                auto_fee_reminders=True,
                fee_reminder_days=7
            )
            db.session.add(notification_settings)
            
            # Create sample notification templates
            attendance_template = NotificationTemplate(
                school_id=sample_school.id,
                name="Attendance Alert",
                notification_type=NotificationType.ATTENDANCE_ALERT,
                method=NotificationMethod.SMS,
                message_template="Dear Parent, {student_name} was marked {status} today ({date}). - {school_name}",
                available_variables=json.dumps(["student_name", "status", "date", "school_name"]),
                is_active=True,
                is_default=True
            )
            db.session.add(attendance_template)
            
            payment_template = NotificationTemplate(
                school_id=sample_school.id,
                name="Payment Confirmation",
                notification_type=NotificationType.PAYMENT_CONFIRMATION,
                method=NotificationMethod.SMS,
                message_template="Dear Parent, Payment of ₹{amount} received for {student_name} (Receipt: {receipt_no}). Thank you! - {school_name}",
                available_variables=json.dumps(["student_name", "amount", "receipt_no", "school_name"]),
                is_active=True,
                is_default=True
            )
            db.session.add(payment_template)
            
            print("Created sample data:")
            print(f"- Classes: {class_10a.get_display_name()}, {class_9a.get_display_name()}")
            print(f"- Students: {sample_student.name}, {sample_student2.name}")
            print(f"- Fee structure for Class 10A: ₹{fee_structure.total_fee}")
            print()
        
        db.session.commit()
        print("Database initialized successfully!")


if __name__ == '__main__':
    init_database()