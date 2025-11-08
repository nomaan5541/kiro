"""
Validation utilities for forms and data
"""
import re
from datetime import datetime, date
from decimal import Decimal, InvalidOperation


class ValidationError(Exception):
    """Custom validation error"""
    pass


class Validators:
    """Collection of validation functions"""
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        if not email:
            return False, "Email is required"
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Invalid email format"
        
        return True, None
    
    @staticmethod
    def validate_phone(phone):
        """Validate Indian phone number"""
        if not phone:
            return False, "Phone number is required"
        
        # Remove all non-digit characters
        phone_digits = re.sub(r'\D', '', phone)
        
        # Check for valid Indian mobile number
        if len(phone_digits) == 10 and phone_digits[0] in '6789':
            return True, None
        elif len(phone_digits) == 12 and phone_digits.startswith('91') and phone_digits[2] in '6789':
            return True, None
        
        return False, "Invalid phone number. Must be a valid 10-digit Indian mobile number"
    
    @staticmethod
    def validate_admission_number(admission_no, school_id=None):
        """Validate admission number format"""
        if not admission_no:
            return False, "Admission number is required"
        
        # Basic format validation
        if len(admission_no) < 3 or len(admission_no) > 20:
            return False, "Admission number must be between 3 and 20 characters"
        
        # Check for valid characters (alphanumeric)
        if not re.match(r'^[A-Za-z0-9]+$', admission_no):
            return False, "Admission number can only contain letters and numbers"
        
        # Check uniqueness if school_id provided
        if school_id:
            from models.student import Student
            existing = Student.query.filter_by(
                school_id=school_id,
                admission_no=admission_no
            ).first()
            if existing:
                return False, "Admission number already exists"
        
        return True, None
    
    @staticmethod
    def validate_roll_number(roll_number, class_id=None, school_id=None):
        """Validate roll number"""
        if not roll_number:
            return False, "Roll number is required"
        
        # Basic format validation
        if len(roll_number) > 20:
            return False, "Roll number must be less than 20 characters"
        
        # Check uniqueness within class if provided
        if class_id and school_id:
            from models.student import Student
            existing = Student.query.filter_by(
                school_id=school_id,
                class_id=class_id,
                roll_number=roll_number
            ).first()
            if existing:
                return False, "Roll number already exists in this class"
        
        return True, None
    
    @staticmethod
    def validate_date_of_birth(dob_str):
        """Validate date of birth"""
        if not dob_str:
            return False, "Date of birth is required"
        
        try:
            if isinstance(dob_str, str):
                dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            else:
                dob = dob_str
            
            # Check if date is not in future
            if dob > date.today():
                return False, "Date of birth cannot be in the future"
            
            # Check reasonable age limits (3-25 years for students)
            age = (date.today() - dob).days // 365
            if age < 3 or age > 25:
                return False, "Student age must be between 3 and 25 years"
            
            return True, None
            
        except ValueError:
            return False, "Invalid date format. Use YYYY-MM-DD"
    
    @staticmethod
    def validate_amount(amount_str):
        """Validate monetary amount"""
        if not amount_str:
            return False, "Amount is required"
        
        try:
            amount = Decimal(str(amount_str))
            
            if amount < 0:
                return False, "Amount cannot be negative"
            
            if amount > Decimal('999999.99'):
                return False, "Amount is too large"
            
            # Check decimal places
            if amount.as_tuple().exponent < -2:
                return False, "Amount can have maximum 2 decimal places"
            
            return True, None
            
        except (InvalidOperation, ValueError):
            return False, "Invalid amount format"
    
    @staticmethod
    def validate_name(name, field_name="Name"):
        """Validate person name"""
        if not name:
            return False, f"{field_name} is required"
        
        name = name.strip()
        
        if len(name) < 2:
            return False, f"{field_name} must be at least 2 characters long"
        
        if len(name) > 100:
            return False, f"{field_name} must be less than 100 characters"
        
        # Check for valid characters (letters, spaces, dots, apostrophes)
        if not re.match(r"^[a-zA-Z\s.']+$", name):
            return False, f"{field_name} can only contain letters, spaces, dots, and apostrophes"
        
        return True, None
    
    @staticmethod
    def validate_password(password):
        """Validate password strength"""
        if not password:
            return False, "Password is required"
        
        if len(password) < 6:
            return False, "Password must be at least 6 characters long"
        
        if len(password) > 128:
            return False, "Password must be less than 128 characters"
        
        # Check for at least one letter and one number
        if not re.search(r'[a-zA-Z]', password):
            return False, "Password must contain at least one letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        
        return True, None
    
    @staticmethod
    def validate_class_name(class_name):
        """Validate class name"""
        if not class_name:
            return False, "Class name is required"
        
        valid_classes = [
            'Nursery', 'LKG', 'UKG',
            'Class 1', 'Class 2', 'Class 3', 'Class 4', 'Class 5',
            'Class 6', 'Class 7', 'Class 8', 'Class 9', 'Class 10',
            'Class 11', 'Class 12'
        ]
        
        if class_name not in valid_classes:
            return False, f"Invalid class name. Must be one of: {', '.join(valid_classes)}"
        
        return True, None
    
    @staticmethod
    def validate_section(section):
        """Validate section name"""
        if section and len(section) > 5:
            return False, "Section name must be less than 5 characters"
        
        if section and not re.match(r'^[A-Za-z0-9]+$', section):
            return False, "Section can only contain letters and numbers"
        
        return True, None
    
    @staticmethod
    def validate_blood_group(blood_group):
        """Validate blood group"""
        if not blood_group:
            return True, None  # Optional field
        
        valid_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        
        if blood_group not in valid_groups:
            return False, f"Invalid blood group. Must be one of: {', '.join(valid_groups)}"
        
        return True, None
    
    @staticmethod
    def validate_file_upload(file, allowed_extensions=None, max_size_mb=5):
        """Validate file upload"""
        if not file:
            return False, "No file selected"
        
        if not file.filename:
            return False, "No file selected"
        
        # Check file extension
        if allowed_extensions is None:
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
        
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if file_ext not in allowed_extensions:
            return False, f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        
        # Check file size (if we can access it)
        try:
            file.seek(0, 2)  # Seek to end
            size = file.tell()
            file.seek(0)  # Reset to beginning
            
            max_size_bytes = max_size_mb * 1024 * 1024
            if size > max_size_bytes:
                return False, f"File size too large. Maximum {max_size_mb}MB allowed"
        except:
            pass  # Skip size check if not accessible
        
        return True, None
    
    @staticmethod
    def sanitize_input(text, max_length=None):
        """Sanitize text input"""
        if not text:
            return ""
        
        # Strip whitespace
        text = text.strip()
        
        # Remove potentially dangerous characters
        text = re.sub(r'[<>"\']', '', text)
        
        # Limit length if specified
        if max_length and len(text) > max_length:
            text = text[:max_length]
        
        return text
    
    @staticmethod
    def validate_form_data(data, rules):
        """Validate form data against rules"""
        errors = {}
        
        for field, field_rules in rules.items():
            value = data.get(field)
            
            for rule in field_rules:
                if rule == 'required' and not value:
                    errors[field] = f"{field.replace('_', ' ').title()} is required"
                    break
                elif rule.startswith('min_length:'):
                    min_len = int(rule.split(':')[1])
                    if value and len(value) < min_len:
                        errors[field] = f"{field.replace('_', ' ').title()} must be at least {min_len} characters"
                        break
                elif rule.startswith('max_length:'):
                    max_len = int(rule.split(':')[1])
                    if value and len(value) > max_len:
                        errors[field] = f"{field.replace('_', ' ').title()} must be less than {max_len} characters"
                        break
                elif rule == 'email' and value:
                    is_valid, error = Validators.validate_email(value)
                    if not is_valid:
                        errors[field] = error
                        break
                elif rule == 'phone' and value:
                    is_valid, error = Validators.validate_phone(value)
                    if not is_valid:
                        errors[field] = error
                        break
        
        return len(errors) == 0, errors