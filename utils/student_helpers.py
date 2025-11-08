"""
Student management helper utilities
"""
import random
import string
from datetime import datetime
from models.student import Student
from extensions import db


def generate_admission_number(school_id, prefix='STU'):
    """Generate unique admission number for a student"""
    year = datetime.now().year
    
    # Try to generate a unique admission number
    max_attempts = 100
    for attempt in range(max_attempts):
        # Generate random 4-digit number
        random_num = random.randint(1000, 9999)
        admission_no = f"{prefix}{year}{random_num}"
        
        # Check if this admission number already exists for this school
        existing = Student.query.filter_by(
            school_id=school_id,
            admission_no=admission_no
        ).first()
        
        if not existing:
            return admission_no
    
    # If we couldn't generate a unique number, use timestamp
    timestamp = int(datetime.now().timestamp())
    return f"{prefix}{year}{timestamp % 10000}"


def generate_roll_number(school_id, class_id=None):
    """Generate roll number for a student in a class"""
    if class_id:
        # Get the next roll number for this class
        last_student = Student.query.filter_by(
            school_id=school_id,
            class_id=class_id
        ).order_by(Student.roll_number.desc()).first()
        
        if last_student and last_student.roll_number.isdigit():
            try:
                next_roll = int(last_student.roll_number) + 1
                return str(next_roll).zfill(2)  # Pad with zeros
            except ValueError:
                pass
    
    # Default: generate random 2-digit number
    return str(random.randint(1, 99)).zfill(2)


def validate_student_data(form_data, school_id, student_id=None):
    """Validate student form data"""
    errors = []
    
    # Required fields
    required_fields = [
        'name', 'father_name', 'mother_name', 'gender', 
        'date_of_birth', 'phone', 'address', 'admission_date'
    ]
    
    for field in required_fields:
        if not form_data.get(field, '').strip():
            errors.append(f"{field.replace('_', ' ').title()} is required")
    
    # Validate admission number uniqueness
    admission_no = form_data.get('admission_no', '').strip()
    if admission_no:
        query = Student.query.filter_by(school_id=school_id, admission_no=admission_no)
        if student_id:
            query = query.filter(Student.id != student_id)
        
        if query.first():
            errors.append("Admission number already exists")
    
    # Validate roll number uniqueness within class
    roll_number = form_data.get('roll_number', '').strip()
    class_id = form_data.get('class_id')
    if roll_number and class_id:
        query = Student.query.filter_by(
            school_id=school_id, 
            class_id=class_id, 
            roll_number=roll_number
        )
        if student_id:
            query = query.filter(Student.id != student_id)
        
        if query.first():
            errors.append("Roll number already exists in this class")
    
    # Validate phone number
    phone = form_data.get('phone', '').strip()
    if phone and not phone.replace('+', '').replace('-', '').replace(' ', '').isdigit():
        errors.append("Invalid phone number format")
    
    # Validate email
    email = form_data.get('email', '').strip()
    if email and '@' not in email:
        errors.append("Invalid email format")
    
    # Validate pincode
    pincode = form_data.get('pincode', '').strip()
    if pincode and (not pincode.isdigit() or len(pincode) != 6):
        errors.append("Pincode must be 6 digits")
    
    # Validate dates
    try:
        if form_data.get('date_of_birth'):
            dob = datetime.strptime(form_data['date_of_birth'], '%Y-%m-%d').date()
            if dob >= datetime.now().date():
                errors.append("Date of birth must be in the past")
    except ValueError:
        errors.append("Invalid date of birth format")
    
    try:
        if form_data.get('admission_date'):
            admission_date = datetime.strptime(form_data['admission_date'], '%Y-%m-%d').date()
            # Admission date can be in the future for pre-admissions
    except ValueError:
        errors.append("Invalid admission date format")
    
    return errors


def get_student_statistics(school_id):
    """Get student statistics for a school"""
    from models.classes import Class
    from sqlalchemy import func
    
    stats = {}
    
    # Total students
    stats['total_students'] = Student.query.filter_by(school_id=school_id).count()
    
    # Active students
    stats['active_students'] = Student.query.filter_by(
        school_id=school_id, 
        status='active'
    ).count()
    
    # Students by gender
    gender_stats = db.session.query(
        Student.gender,
        func.count(Student.id)
    ).filter_by(school_id=school_id).group_by(Student.gender).all()
    
    stats['gender_distribution'] = {gender: count for gender, count in gender_stats}
    
    # Students by class
    class_stats = db.session.query(
        Class.class_name,
        Class.section,
        func.count(Student.id)
    ).join(Student, Class.id == Student.class_id)\
     .filter(Student.school_id == school_id)\
     .group_by(Class.id, Class.class_name, Class.section).all()
    
    stats['class_distribution'] = [
        {
            'class_name': f"{class_name} {section}" if section else class_name,
            'student_count': count
        }
        for class_name, section, count in class_stats
    ]
    
    # Recent admissions (last 30 days)
    from datetime import date, timedelta
    thirty_days_ago = date.today() - timedelta(days=30)
    
    stats['recent_admissions'] = Student.query.filter(
        Student.school_id == school_id,
        Student.admission_date >= thirty_days_ago
    ).count()
    
    return stats


def export_students_csv(school_id, class_id=None):
    """Export students data to CSV format"""
    import csv
    import io
    
    # Build query
    query = Student.query.filter_by(school_id=school_id)
    if class_id:
        query = query.filter_by(class_id=class_id)
    
    students = query.all()
    
    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    headers = [
        'Admission No', 'Roll Number', 'Name', 'Father Name', 'Mother Name',
        'Gender', 'Date of Birth', 'Phone', 'Email', 'Address', 'City', 
        'State', 'Pincode', 'Blood Group', 'PEN No', 'Class', 'Status',
        'Admission Date'
    ]
    writer.writerow(headers)
    
    # Write student data
    for student in students:
        class_name = student.class_info.get_display_name() if student.class_info else ''
        
        row = [
            student.admission_no,
            student.roll_number,
            student.name,
            student.father_name,
            student.mother_name,
            student.gender,
            student.date_of_birth.strftime('%Y-%m-%d') if student.date_of_birth else '',
            student.phone,
            student.email or '',
            student.address,
            student.city or '',
            student.state or '',
            student.pincode or '',
            student.blood_group or '',
            student.pen_no or '',
            class_name,
            student.status.value if hasattr(student.status, 'value') else student.status,
            student.admission_date.strftime('%Y-%m-%d') if student.admission_date else ''
        ]
        writer.writerow(row)
    
    output.seek(0)
    return output.getvalue()


def import_students_csv(school_id, csv_file):
    """Import students from CSV file"""
    import csv
    import io
    from models.student import StudentStatus
    from models.classes import Class
    
    results = {
        'success': 0,
        'errors': [],
        'warnings': []
    }
    
    try:
        # Read CSV content
        csv_content = csv_file.read().decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start from 2 (after header)
            try:
                # Validate required fields
                if not all([row.get('Name'), row.get('Father Name'), row.get('Mother Name')]):
                    results['errors'].append(f"Row {row_num}: Missing required fields")
                    continue
                
                # Check if admission number already exists
                admission_no = row.get('Admission No', '').strip()
                if admission_no and Student.query.filter_by(
                    school_id=school_id, 
                    admission_no=admission_no
                ).first():
                    results['warnings'].append(f"Row {row_num}: Admission number {admission_no} already exists, skipping")
                    continue
                
                # Generate admission number if not provided
                if not admission_no:
                    admission_no = generate_admission_number(school_id)
                
                # Find class by name
                class_id = None
                class_name = row.get('Class', '').strip()
                if class_name:
                    class_obj = Class.query.filter_by(
                        school_id=school_id
                    ).filter(
                        db.or_(
                            Class.class_name == class_name,
                            db.func.concat(Class.class_name, ' ', Class.section) == class_name
                        )
                    ).first()
                    
                    if class_obj:
                        class_id = class_obj.id
                    else:
                        results['warnings'].append(f"Row {row_num}: Class '{class_name}' not found")
                
                # Parse dates
                try:
                    dob = datetime.strptime(row.get('Date of Birth', ''), '%Y-%m-%d').date()
                except ValueError:
                    results['errors'].append(f"Row {row_num}: Invalid date of birth format")
                    continue
                
                try:
                    admission_date = datetime.strptime(row.get('Admission Date', ''), '%Y-%m-%d').date()
                except ValueError:
                    admission_date = datetime.now().date()
                
                # Create student
                student = Student(
                    school_id=school_id,
                    class_id=class_id,
                    admission_no=admission_no,
                    roll_number=row.get('Roll Number', generate_roll_number(school_id, class_id)),
                    admission_date=admission_date,
                    name=row.get('Name').strip(),
                    father_name=row.get('Father Name').strip(),
                    mother_name=row.get('Mother Name').strip(),
                    gender=row.get('Gender', 'male').lower(),
                    date_of_birth=dob,
                    phone=row.get('Phone', '').strip(),
                    email=row.get('Email', '').strip() or None,
                    address=row.get('Address', '').strip(),
                    city=row.get('City', '').strip() or None,
                    state=row.get('State', '').strip() or None,
                    pincode=row.get('Pincode', '').strip() or None,
                    blood_group=row.get('Blood Group', '').strip() or None,
                    pen_no=row.get('PEN No', '').strip() or None,
                    status=StudentStatus.ACTIVE
                )
                
                db.session.add(student)
                results['success'] += 1
                
            except Exception as e:
                results['errors'].append(f"Row {row_num}: {str(e)}")
        
        # Commit all changes
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        results['errors'].append(f"File processing error: {str(e)}")
    
    return results


def search_students(school_id, search_term, filters=None):
    """Search students with advanced filtering"""
    query = Student.query.filter_by(school_id=school_id)
    
    # Apply search term
    if search_term:
        search_pattern = f"%{search_term}%"
        query = query.filter(
            db.or_(
                Student.name.ilike(search_pattern),
                Student.admission_no.ilike(search_pattern),
                Student.roll_number.ilike(search_pattern),
                Student.phone.ilike(search_pattern),
                Student.father_name.ilike(search_pattern),
                Student.mother_name.ilike(search_pattern)
            )
        )
    
    # Apply filters
    if filters:
        if filters.get('class_id'):
            query = query.filter_by(class_id=filters['class_id'])
        
        if filters.get('status'):
            query = query.filter_by(status=filters['status'])
        
        if filters.get('gender'):
            query = query.filter_by(gender=filters['gender'])
        
        if filters.get('blood_group'):
            query = query.filter_by(blood_group=filters['blood_group'])
    
    return query