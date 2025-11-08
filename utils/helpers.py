"""
Helper utilities for the school management system
"""
import random
import string
from datetime import datetime, date
import os
from werkzeug.utils import secure_filename


def generate_admission_number(school_id, year=None):
    """Generate unique admission number"""
    if year is None:
        year = datetime.now().year
    
    # Format: SCH{school_id}{year}{random_4_digits}
    random_part = ''.join(random.choices(string.digits, k=4))
    return f"SCH{school_id:03d}{year}{random_part}"


def generate_roll_number(class_name, section=None):
    """Generate roll number for a class"""
    # Simple sequential numbering - in real implementation, 
    # you'd query the database for the next available number
    random_part = ''.join(random.choices(string.digits, k=3))
    if section:
        return f"{class_name}{section}{random_part}"
    return f"{class_name}{random_part}"


def generate_receipt_number(school_id):
    """Generate unique receipt number for payments"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = ''.join(random.choices(string.digits, k=3))
    return f"RCP{school_id:03d}{timestamp}{random_part}"


def calculate_age(birth_date):
    """Calculate age from birth date"""
    if not birth_date:
        return None
    
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def format_phone_number(phone):
    """Format phone number to standard format"""
    # Remove all non-digit characters
    phone = ''.join(filter(str.isdigit, phone))
    
    # Add country code if not present
    if len(phone) == 10:
        phone = '91' + phone
    
    return phone


def validate_email(email):
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def allowed_file(filename, allowed_extensions=None):
    """Check if file extension is allowed"""
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def save_uploaded_file(file, subfolder):
    """Save uploaded file and return the filename"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        # Add timestamp to avoid filename conflicts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
        filename = timestamp + filename
        
        # Create upload directory structure
        upload_path = os.path.join('static', 'uploads', subfolder)
        os.makedirs(upload_path, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_path, filename)
        file.save(file_path)
        
        # Return just the filename for database storage
        return filename
    
    return None


def format_currency(amount):
    """Format amount as currency"""
    return f"₹{amount:,.2f}"


def get_academic_year(date_obj=None):
    """Get academic year string (e.g., '2024-25')"""
    if date_obj is None:
        date_obj = datetime.now()
    
    # Academic year typically starts in April
    if date_obj.month >= 4:
        start_year = date_obj.year
        end_year = date_obj.year + 1
    else:
        start_year = date_obj.year - 1
        end_year = date_obj.year
    
    return f"{start_year}-{str(end_year)[2:]}"


def get_class_subjects(class_name):
    """Get default subjects for a class"""
    subjects_map = {
        'Nursery': ['English', 'Hindi', 'Mathematics', 'Drawing', 'Games'],
        'LKG': ['English', 'Hindi', 'Mathematics', 'Drawing', 'Games'],
        'UKG': ['English', 'Hindi', 'Mathematics', 'Drawing', 'Games', 'General Knowledge'],
        'Class 1': ['English', 'Hindi', 'Mathematics', 'EVS', 'Drawing', 'Games'],
        'Class 2': ['English', 'Hindi', 'Mathematics', 'EVS', 'Drawing', 'Games'],
        'Class 3': ['English', 'Hindi', 'Mathematics', 'EVS', 'Drawing', 'Games', 'Computer'],
        'Class 4': ['English', 'Hindi', 'Mathematics', 'EVS', 'Drawing', 'Games', 'Computer'],
        'Class 5': ['English', 'Hindi', 'Mathematics', 'EVS', 'Drawing', 'Games', 'Computer'],
        'Class 6': ['English', 'Hindi', 'Mathematics', 'Science', 'Social Science', 'Computer', 'Physical Education'],
        'Class 7': ['English', 'Hindi', 'Mathematics', 'Science', 'Social Science', 'Computer', 'Physical Education'],
        'Class 8': ['English', 'Hindi', 'Mathematics', 'Science', 'Social Science', 'Computer', 'Physical Education'],
        'Class 9': ['English', 'Hindi', 'Mathematics', 'Science', 'Social Science', 'Computer', 'Physical Education'],
        'Class 10': ['English', 'Hindi', 'Mathematics', 'Science', 'Social Science', 'Computer', 'Physical Education'],
        'Class 11': ['English', 'Physics', 'Chemistry', 'Mathematics', 'Biology', 'Computer Science', 'Physical Education'],
        'Class 12': ['English', 'Physics', 'Chemistry', 'Mathematics', 'Biology', 'Computer Science', 'Physical Education']
    }
    
    return subjects_map.get(class_name, ['English', 'Mathematics', 'Science'])


def get_available_classes():
    """Get list of available classes"""
    return [
        'Nursery', 'LKG', 'UKG',
        'Class 1', 'Class 2', 'Class 3', 'Class 4', 'Class 5',
        'Class 6', 'Class 7', 'Class 8', 'Class 9', 'Class 10',
        'Class 11', 'Class 12'
    ]


def get_available_sections():
    """Get list of available sections"""
    return ['A', 'B', 'C', 'D', 'E']


def generate_qr_verification_url(receipt_no):
    """Generate QR code verification URL for receipts"""
    from flask import url_for, current_app
    
    # In production, this would be the actual domain
    base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')
    verification_path = f"/verify-receipt/{receipt_no}"
    
    return f"{base_url}{verification_path}"


def generate_employee_id(school_id, department=None):
    """Generate unique employee ID for teachers/staff"""
    timestamp = datetime.now().strftime("%y%m")
    random_part = ''.join(random.choices(string.digits, k=3))
    
    if department:
        dept_code = department[:3].upper()
        return f"EMP{school_id:03d}{dept_code}{timestamp}{random_part}"
    
    return f"EMP{school_id:03d}{timestamp}{random_part}"


def calculate_fee_due_date(payment_date, grace_period_days=30):
    """Calculate fee due date based on payment date and grace period"""
    from datetime import timedelta
    
    if isinstance(payment_date, str):
        payment_date = datetime.strptime(payment_date, '%Y-%m-%d').date()
    
    return payment_date + timedelta(days=grace_period_days)


def format_receipt_data(payment, student, school):
    """Format payment data for receipt generation"""
    return {
        'receipt_no': payment.receipt_no,
        'payment_date': payment.payment_date.strftime('%d/%m/%Y'),
        'student_name': student.name,
        'student_id': student.admission_no,
        'class_section': f"{student.class_info.class_name} {student.class_info.section}" if student.class_info else 'N/A',
        'amount_paid': float(payment.amount),
        'payment_method': payment.payment_mode.value.title() if payment.payment_mode else 'Cash',
        'transaction_id': payment.transaction_id or payment.reference_number or 'N/A',
        'school_name': school.name,
        'school_address': school.address or '',
        'school_phone': school.phone or '',
        'school_email': school.email or '',
        'academic_year': get_academic_year(payment.payment_date),
        'collected_by': payment.collector.name if hasattr(payment, 'collector') and payment.collector else 'System'
    }


def validate_payment_amount(amount, min_amount=1, max_amount=1000000):
    """Validate payment amount"""
    try:
        amount = float(amount)
        if amount < min_amount:
            return False, f"Amount must be at least ₹{min_amount}"
        if amount > max_amount:
            return False, f"Amount cannot exceed ₹{max_amount:,}"
        return True, "Valid amount"
    except (ValueError, TypeError):
        return False, "Invalid amount format"


def generate_payment_reference():
    """Generate unique payment reference number"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"PAY{timestamp}{random_part}"


def calculate_late_fee(original_amount, days_overdue, late_fee_percentage=2):
    """Calculate late fee based on overdue days"""
    if days_overdue <= 0:
        return 0
    
    # Calculate late fee as percentage of original amount
    late_fee = (original_amount * late_fee_percentage / 100)
    
    # Cap late fee at 20% of original amount
    max_late_fee = original_amount * 0.20
    
    return min(late_fee, max_late_fee)


def get_payment_method_display_name(payment_mode):
    """Get display name for payment method"""
    method_names = {
        'cash': 'Cash',
        'cheque': 'Cheque',
        'bank_transfer': 'Bank Transfer',
        'upi': 'UPI',
        'card': 'Credit/Debit Card',
        'online': 'Online Payment',
        'netbanking': 'Net Banking'
    }
    
    return method_names.get(payment_mode.lower(), payment_mode.title())


def format_student_balance_summary(student_fee_status):
    """Format student balance summary for display"""
    if not student_fee_status:
        return {
            'total_fee': 0,
            'paid_amount': 0,
            'pending_amount': 0,
            'status': 'No Fee Structure',
            'is_overdue': False,
            'days_overdue': 0
        }
    
    days_overdue = 0
    if student_fee_status.due_date and student_fee_status.due_date < date.today():
        days_overdue = (date.today() - student_fee_status.due_date).days
    
    return {
        'total_fee': float(student_fee_status.total_amount or 0),
        'paid_amount': float(student_fee_status.paid_amount or 0),
        'pending_amount': float(student_fee_status.remaining_amount or 0),
        'status': 'Paid' if student_fee_status.remaining_amount <= 0 else 'Pending',
        'is_overdue': days_overdue > 0,
        'days_overdue': days_overdue,
        'last_payment_date': student_fee_status.last_payment_date.strftime('%d/%m/%Y') if student_fee_status.last_payment_date else None
    }