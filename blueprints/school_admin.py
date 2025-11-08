"""
School Admin Blueprint - Handles school operations and management
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from extensions import db
from models.user import User
from models.school import School
from utils.auth import login_required, role_required
from sqlalchemy import func

school_admin_bp = Blueprint('school_admin', __name__)


@school_admin_bp.route('/dashboard')
@role_required('school_admin')
def dashboard():
    """Enhanced school admin dashboard with comprehensive KPIs and charts"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    # Check if setup wizard is completed
    if not school.setup_completed:
        return redirect(url_for('school_admin.setup_wizard'))
    
    # Import required models
    from models.student import Student, StudentStatus
    from models.teacher import Teacher, TeacherStatus
    from models.classes import Class
    from models.attendance import Attendance, AttendanceStatus
    from models.fee import Payment, StudentFeeStatus, FeeStructure
    from datetime import datetime, date, timedelta
    from decimal import Decimal
    from sqlalchemy import func, and_, extract
    
    # Calculate comprehensive KPIs
    kpis = calculate_dashboard_kpis(school.id)
    
    # Generate chart data
    chart_data = generate_chart_data(school.id)
    
    # Get recent activities
    recent_activities = get_recent_activities(school.id)
    
    # Get top performing students
    top_students = get_top_students(school.id)
    
    # Calculate subscription status
    subscription_data = calculate_subscription_status(school)
    
    return render_template('school_admin/dashboard.html',
                         school=school,
                         user=user,
                         # KPIs
                         total_students=kpis['total_students'],
                         active_students=kpis['active_students'],
                         inactive_students=kpis['inactive_students'],
                         students_growth=kpis['students_growth'],
                         total_teachers=kpis['total_teachers'],
                         active_teachers=kpis['active_teachers'],
                         teachers_growth=kpis['teachers_growth'],
                         subjects_covered=kpis['subjects_covered'],
                         attendance_percentage=kpis['attendance_percentage'],
                         attendance_trend=kpis['attendance_trend'],
                         present_today=kpis['present_today'],
                         absent_today=kpis['absent_today'],
                         fees_collected=kpis['fees_collected'],
                         fees_due=kpis['fees_due'],
                         collection_rate=kpis['collection_rate'],
                         fees_growth=kpis['fees_growth'],
                         classes_active=kpis['classes_active'],
                         # Chart data
                         attendance_chart_data=chart_data['attendance'],
                         fee_chart_data=chart_data['fees'],
                         class_distribution_data=chart_data['class_distribution'],
                         students_trend_data=chart_data['students_trend'],
                         teachers_trend_data=chart_data['teachers_trend'],
                         # Additional data
                         recent_activities=recent_activities,
                         top_students=top_students,
                         subscription_days_remaining=subscription_data['days_remaining'],
                         subscription_status=subscription_data['status'])


# Removed duplicate setup_wizard function - using the more complete one below


@school_admin_bp.route('/students')
@role_required('school_admin')
def students():
    """List all students"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    # Get search and filter parameters
    search = request.args.get('search', '')
    class_filter = request.args.get('class', '')
    status_filter = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    
    # Build query
    from models.student import Student
    from models.classes import Class
    
    query = Student.query.filter_by(school_id=school.id)
    
    # Apply filters
    if search:
        query = query.filter(
            db.or_(
                Student.name.contains(search),
                Student.admission_no.contains(search),
                Student.roll_number.contains(search),
                Student.phone.contains(search)
            )
        )
    
    if class_filter:
        query = query.filter_by(class_id=class_filter)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    # Paginate results
    students = query.order_by(Student.created_at.desc()).paginate(
        page=page, per_page=25, error_out=False
    )
    
    # Get classes for filter dropdown
    classes = Class.query.filter_by(school_id=school.id).all()
    
    return render_template('school_admin/students.html', 
                         students=students, 
                         classes=classes,
                         search=search,
                         class_filter=class_filter,
                         status_filter=status_filter)


@school_admin_bp.route('/students/add', methods=['GET', 'POST'])
@role_required('school_admin')
def add_student():
    """Add new student"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    if request.method == 'POST':
        from utils.student_helpers import validate_student_data, generate_admission_number
        from models.student import Student, StudentStatus
        from models.classes import Class
        from datetime import datetime
        
        # Validate form data
        form_data = request.form.to_dict()
        validation_errors = validate_student_data(form_data, school.id)
        
        if validation_errors:
            for error in validation_errors:
                flash(error, 'error')
            # Get classes for dropdown
            from models.classes import Class
            classes = Class.query.filter_by(school_id=school.id).all()
            return render_template('school_admin/add_student.html', classes=classes)
        
        try:
            # Generate admission number if not provided
            admission_no = form_data.get('admission_no', '').strip()
            if not admission_no:
                admission_no = generate_admission_number(school.id)
            
            # Get form data with all new fields
            student_data = {
                'school_id': school.id,
                'class_id': request.form.get('class_id') or None,
                'roll_number': request.form.get('roll_number'),
                'admission_no': admission_no,
                'admission_date': datetime.strptime(request.form.get('admission_date'), '%Y-%m-%d').date(),
                'name': request.form.get('name'),
                'father_name': request.form.get('father_name'),
                'mother_name': request.form.get('mother_name'),
                'gender': request.form.get('gender'),
                'date_of_birth': datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date(),
                'phone': request.form.get('phone'),
                'email': request.form.get('email') or None,
                'address': request.form.get('address'),
                'city': request.form.get('city') or None,
                'state': request.form.get('state') or None,
                'pincode': request.form.get('pincode') or None,
                'blood_group': request.form.get('blood_group') or None,
                'pen_no': request.form.get('pen_no') or None,
                'bio': request.form.get('bio') or None,
                'status': StudentStatus.ACTIVE
            }
            
            # Create student
            student = Student(**student_data)
            db.session.add(student)
            db.session.flush()  # Get student ID for photo upload
            
            # Handle photo upload
            if 'photo' in request.files and request.files['photo'].filename != '':
                from services.file_upload_service import save_student_photo
                success, message, file_info = save_student_photo(request.files['photo'], student.id)
                if success:
                    student.photo_url = file_info['file_path']
                else:
                    flash(f'Photo upload failed: {message}', 'warning')
            
            db.session.commit()
            
            flash(f'Student {student.name} added successfully!', 'success')
            return redirect(url_for('school_admin.students'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding student: {str(e)}', 'error')
    
    # Get classes for dropdown
    from models.classes import Class
    classes = Class.query.filter_by(school_id=school.id).all()
    
    # Get today's date for form
    from datetime import date
    today = date.today()
    
    # Get user and school context
    user = User.query.get(session['user_id'])
    school = user.school
    
    return render_template('school_admin/add_student.html', 
                         classes=classes, today=today, user=user, school=school)


@school_admin_bp.route('/students/<int:student_id>')
@role_required('school_admin')
def student_profile(student_id):
    """View student profile"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    from models.student import Student
    student = Student.query.filter_by(id=student_id, school_id=school.id).first_or_404()
    
    return render_template('school_admin/student_profile.html', student=student)


@school_admin_bp.route('/students/<int:student_id>/edit', methods=['GET', 'POST'])
@role_required('school_admin')
def edit_student(student_id):
    """Edit student information"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    from models.student import Student, StudentStatus
    from models.classes import Class
    
    student = Student.query.filter_by(id=student_id, school_id=school.id).first_or_404()
    
    if request.method == 'POST':
        try:
            from datetime import datetime
            
            # Update student data with all fields
            student.class_id = request.form.get('class_id') or None
            student.roll_number = request.form.get('roll_number')
            student.admission_no = request.form.get('admission_no')
            student.admission_date = datetime.strptime(request.form.get('admission_date'), '%Y-%m-%d').date()
            student.name = request.form.get('name')
            student.father_name = request.form.get('father_name')
            student.mother_name = request.form.get('mother_name')
            student.gender = request.form.get('gender')
            student.date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date()
            student.phone = request.form.get('phone')
            student.email = request.form.get('email') or None
            student.address = request.form.get('address')
            student.city = request.form.get('city') or None
            student.state = request.form.get('state') or None
            student.pincode = request.form.get('pincode') or None
            student.blood_group = request.form.get('blood_group') or None
            student.pen_no = request.form.get('pen_no') or None
            student.bio = request.form.get('bio') or None
            student.status = StudentStatus(request.form.get('status'))
            
            # Handle photo upload
            if 'photo' in request.files and request.files['photo'].filename != '':
                from services.file_upload_service import save_student_photo
                success, message, file_info = save_student_photo(request.files['photo'], student.id)
                if success:
                    # Delete old photo if exists
                    if student.photo_url:
                        from services.file_upload_service import delete_file_safely
                        delete_file_safely(student.photo_url)
                    student.photo_url = file_info['file_path']
                else:
                    flash(f'Photo upload failed: {message}', 'warning')
            
            db.session.commit()
            
            flash(f'Student {student.name} updated successfully!', 'success')
            return redirect(url_for('school_admin.student_profile', student_id=student.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating student: {str(e)}', 'error')
    
    # Get classes for dropdown
    classes = Class.query.filter_by(school_id=school.id).all()
    
    return render_template('school_admin/edit_student.html', student=student, classes=classes)

@school_admin_bp.route('/attendance', methods=['GET', 'POST'])
@role_required('school_admin')
def attendance():
    """Mark attendance for students"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    from models.classes import Class
    from models.student import Student
    from models.attendance import Attendance, AttendanceStatus
    from datetime import datetime, date
    
    # Get classes for dropdown
    classes = Class.query.filter_by(school_id=school.id).all()
    
    selected_date = None
    selected_class_id = None
    selected_class = None
    students = []
    attendance_data = {}
    
    if request.method == 'POST':
        # Handle attendance submission
        try:
            selected_date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
            selected_class_id = int(request.form.get('class_id'))
            
            # Get all students in the class
            students = Student.query.filter_by(school_id=school.id, class_id=selected_class_id).all()
            
            # Process attendance data
            for student in students:
                attendance_status = request.form.get(f'attendance_{student.id}')
                if attendance_status:
                    # Check if attendance already exists for this date
                    existing_attendance = Attendance.query.filter_by(
                        student_id=student.id,
                        date=selected_date
                    ).first()
                    
                    if existing_attendance:
                        # Update existing attendance
                        existing_attendance.status = AttendanceStatus(attendance_status)
                        existing_attendance.marked_by = user.id
                        existing_attendance.marked_at = datetime.utcnow()
                    else:
                        # Create new attendance record
                        attendance = Attendance(
                            school_id=school.id,
                            student_id=student.id,
                            class_id=selected_class_id,
                            date=selected_date,
                            status=AttendanceStatus(attendance_status),
                            marked_by=user.id
                        )
                        db.session.add(attendance)
            
            db.session.commit()
            flash('Attendance saved successfully!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving attendance: {str(e)}', 'error')
    
    # Handle GET request with date and class selection
    if request.args.get('date') and request.args.get('class_id'):
        try:
            selected_date = datetime.strptime(request.args.get('date'), '%Y-%m-%d').date()
            selected_class_id = int(request.args.get('class_id'))
            selected_class = Class.query.get(selected_class_id)
            
            # Get students for the selected class
            students = Student.query.filter_by(school_id=school.id, class_id=selected_class_id).all()
            
            # Get existing attendance data for the date
            existing_attendance = Attendance.query.filter_by(
                school_id=school.id,
                class_id=selected_class_id,
                date=selected_date
            ).all()
            
            # Create attendance data dictionary
            for att in existing_attendance:
                attendance_data[att.student_id] = att.status.value
                
        except Exception as e:
            flash(f'Error loading attendance data: {str(e)}', 'error')
    
    # Get user and school context
    user = User.query.get(session['user_id'])
    school = user.school
    
    return render_template('school_admin/attendance.html',
                         classes=classes,
                         selected_date=selected_date,
                         selected_class_id=selected_class_id,
                         selected_class=selected_class,
                         students=students,
                         attendance_data=attendance_data,
                         user=user,
                         school=school)


@school_admin_bp.route('/fees')
@role_required('school_admin')
def fees():
    """Enhanced fee management dashboard with comprehensive analytics"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    # Get comprehensive fee statistics
    fee_stats = get_comprehensive_fee_stats(school.id)
    
    # Get classes for filter
    from models.classes import Class
    classes = Class.query.filter_by(school_id=school.id).order_by(Class.class_name, Class.section).all()
    
    # Get recent payments
    from models.fee import Payment
    recent_payments = Payment.query.filter_by(school_id=school.id)\
        .order_by(Payment.payment_date.desc())\
        .limit(10).all()
    
    # Get pending fee students
    from models.fee import StudentFeeStatus
    pending_students = StudentFeeStatus.query.filter(
        StudentFeeStatus.school_id == school.id,
        StudentFeeStatus.remaining_amount > 0
    ).order_by(StudentFeeStatus.next_due_date.asc()).limit(10).all()
    
    return render_template('school_admin/fees.html',
                         fee_stats=fee_stats,
                         classes=classes,
                         recent_payments=recent_payments,
                         pending_students=pending_students,
                         today=date.today().isoformat())


@school_admin_bp.route('/fees/statistics')
@role_required('school_admin')
def get_fee_statistics():
    """API endpoint for fee statistics"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    stats = get_comprehensive_fee_stats(school.id)
    
    return jsonify({
        'success': True,
        'statistics': stats
    })


@school_admin_bp.route('/fees/search_students')
@role_required('school_admin')
def search_students():
    """Search students for fee collection"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:
        return jsonify({'students': []})
    
    from models.student import Student
    from models.fee import StudentFeeStatus
    
    # Search students
    students = Student.query.filter(
        Student.school_id == school.id,
        db.or_(
            Student.name.ilike(f'%{query}%'),
            Student.admission_no.ilike(f'%{query}%'),
            Student.roll_number.ilike(f'%{query}%')
        )
    ).limit(10).all()
    
    # Get fee status for each student
    student_data = []
    for student in students:
        fee_status = StudentFeeStatus.query.filter_by(
            student_id=student.id,
            school_id=school.id
        ).first()
        
        balance = fee_status.remaining_amount if fee_status else 0
        
        student_data.append({
            'id': student.id,
            'name': student.name,
            'admission_no': student.admission_no,
            'roll_number': student.roll_number,
            'class_name': student.class_info.get_display_name() if student.class_info else 'No Class',
            'phone': student.phone,
            'email': student.email,
            'balance': float(balance)
        })
    
    return jsonify({'students': student_data})


@school_admin_bp.route('/fees/student/<int:student_id>/structure')
@role_required('school_admin')
def get_student_fee_structure(student_id):
    """Get fee structure for a specific student"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    from models.student import Student
    from models.fee import FeeStructure, StudentFeeStatus
    
    student = Student.query.filter_by(id=student_id, school_id=school.id).first_or_404()
    
    # Get fee structure for student's class
    fee_structure = FeeStructure.query.filter_by(
        school_id=school.id,
        class_id=student.class_id,
        is_active=True
    ).first()
    
    if not fee_structure:
        return jsonify({
            'success': False,
            'message': 'No active fee structure found for this student'
        }), 404
    
    # Get student's fee status
    fee_status = StudentFeeStatus.query.filter_by(
        student_id=student_id,
        fee_structure_id=fee_structure.id
    ).first()
    
    # Build fee structure data
    structure_data = {
        'total': float(fee_structure.total_fee),
        'total_paid': float(fee_status.paid_amount) if fee_status else 0,
        'total_pending': float(fee_status.remaining_amount) if fee_status else float(fee_structure.total_fee),
        'items': []
    }
    
    # Add fee items (this would come from a fee_items table in a real system)
    # For now, we'll create a basic structure
    fee_items = [
        {'name': 'Tuition Fee', 'amount': float(fee_structure.tuition_fee or 0), 'description': 'Monthly tuition charges'},
        {'name': 'Transport Fee', 'amount': float(fee_structure.transport_fee or 0), 'description': 'School bus charges'},
        {'name': 'Library Fee', 'amount': float(fee_structure.library_fee or 0), 'description': 'Library usage charges'},
        {'name': 'Lab Fee', 'amount': float(fee_structure.lab_fee or 0), 'description': 'Laboratory charges'},
        {'name': 'Sports Fee', 'amount': float(fee_structure.sports_fee or 0), 'description': 'Sports activities charges'},
        {'name': 'Other Fees', 'amount': float(fee_structure.other_fees or 0), 'description': 'Miscellaneous charges'}
    ]
    
    total_paid = structure_data['total_paid']
    for item in fee_items:
        if item['amount'] > 0:
            # Simple allocation - in reality, you'd track payments per fee type
            paid_for_item = min(item['amount'], total_paid)
            total_paid -= paid_for_item
            
            structure_data['items'].append({
                'name': item['name'],
                'description': item['description'],
                'amount': item['amount'],
                'paid': paid_for_item,
                'pending': item['amount'] - paid_for_item
            })
    
    return jsonify({
        'success': True,
        'fee_structure': structure_data
    })


@school_admin_bp.route('/fees/process_payment', methods=['POST'])
@role_required('school_admin')
def process_payment():
    """Process fee payment"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    data = request.get_json()
    
    try:
        from models.student import Student
        from models.fee import Payment, PaymentMode, PaymentStatus, StudentFeeStatus, FeeStructure
        from utils.helpers import generate_receipt_number
        from decimal import Decimal
        
        student_id = data.get('student_id')
        amount = Decimal(str(data.get('amount')))
        payment_method = data.get('payment_method')
        payment_date = datetime.strptime(data.get('payment_date'), '%Y-%m-%d').date()
        reference_number = data.get('reference_number', '')
        remarks = data.get('remarks', '')
        
        # Get student and fee structure
        student = Student.query.filter_by(id=student_id, school_id=school.id).first_or_404()
        fee_structure = FeeStructure.query.filter_by(
            school_id=school.id,
            class_id=student.class_id,
            is_active=True
        ).first()
        
        if not fee_structure:
            return jsonify({
                'success': False,
                'message': 'No active fee structure found for this student'
            }), 400
        
        # Create payment record
        payment = Payment(
            school_id=school.id,
            student_id=student_id,
            fee_structure_id=fee_structure.id,
            receipt_no=generate_receipt_number(school.id),
            amount=amount,
            payment_date=payment_date,
            payment_mode=PaymentMode(payment_method),
            status=PaymentStatus.COMPLETED,
            reference_number=reference_number,
            remarks=remarks,
            collected_by=user.id
        )
        db.session.add(payment)
        db.session.flush()  # Get payment ID
        
        # Update student fee status
        fee_status = StudentFeeStatus.query.filter_by(
            student_id=student_id,
            fee_structure_id=fee_structure.id
        ).first()
        
        if fee_status:
            fee_status.paid_amount += amount
            fee_status.remaining_amount = max(Decimal('0'), fee_status.remaining_amount - amount)
            fee_status.last_payment_date = payment_date
        else:
            # Create new fee status
            fee_status = StudentFeeStatus(
                school_id=school.id,
                student_id=student_id,
                fee_structure_id=fee_structure.id,
                total_amount=fee_structure.total_fee,
                paid_amount=amount,
                remaining_amount=max(Decimal('0'), fee_structure.total_fee - amount),
                last_payment_date=payment_date
            )
            db.session.add(fee_status)
        
        db.session.commit()
        
        # Generate digital receipt
        receipt_data = generate_digital_receipt(payment, student, school)
        
        return jsonify({
            'success': True,
            'message': 'Payment processed successfully',
            'receipt': receipt_data
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@school_admin_bp.route('/fees/create_payment_order', methods=['POST'])
@role_required('school_admin')
def create_payment_order():
    """Create payment order for online payment gateways"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    data = request.get_json()
    
    try:
        student_id = data.get('student_id')
        amount = float(data.get('amount'))
        gateway = data.get('gateway')
        
        from models.student import Student
        student = Student.query.filter_by(id=student_id, school_id=school.id).first_or_404()
        
        if gateway == 'razorpay':
            # Create Razorpay order
            from services.payment_gateway import RazorpayService
            razorpay_service = RazorpayService()
            order = razorpay_service.create_order(
                amount=amount,
                currency='INR',
                receipt=f"fee_{student_id}_{int(datetime.now().timestamp())}"
            )
            
            return jsonify({
                'success': True,
                'order_id': order['id'],
                'amount': order['amount']
            })
        
        elif gateway == 'stripe':
            # Create Stripe payment intent
            from services.payment_gateway import StripeService
            stripe_service = StripeService()
            intent = stripe_service.create_payment_intent(
                amount=int(amount * 100),  # Stripe uses cents
                currency='inr'
            )
            
            return jsonify({
                'success': True,
                'client_secret': intent.client_secret
            })
        
        else:
            return jsonify({
                'success': False,
                'message': 'Unsupported payment gateway'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@school_admin_bp.route('/fees/verify_payment', methods=['POST'])
@role_required('school_admin')
def verify_payment():
    """Verify online payment"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    data = request.get_json()
    
    try:
        payment_response = data.get('payment_response')
        gateway = data.get('gateway')
        student_id = data.get('student_id')
        
        if gateway == 'razorpay':
            from services.payment_gateway import RazorpayService
            razorpay_service = RazorpayService()
            
            # Verify payment signature
            if razorpay_service.verify_payment_signature(payment_response):
                # Payment is verified, process it
                amount = payment_response.get('razorpay_amount', 0) / 100  # Convert from paise
                
                # Process the payment (similar to process_payment but for online)
                receipt_data = process_verified_payment(
                    student_id, amount, 'online', payment_response.get('razorpay_payment_id'), user, school
                )
                
                return jsonify({
                    'success': True,
                    'receipt': receipt_data
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Payment verification failed'
                }), 400
        
        else:
            return jsonify({
                'success': False,
                'message': 'Unsupported payment gateway'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


def get_comprehensive_fee_stats(school_id):
    """Get comprehensive fee statistics"""
    from models.fee import Payment, StudentFeeStatus, PaymentMode
    from models.student import Student
    from datetime import datetime, date, timedelta
    from decimal import Decimal
    
    today = date.today()
    current_month = today.replace(day=1)
    last_month = (current_month - timedelta(days=1)).replace(day=1)
    
    # Basic statistics
    total_collected = db.session.query(func.sum(Payment.amount)).filter(
        Payment.school_id == school_id
    ).scalar() or Decimal('0')
    
    this_month_collected = db.session.query(func.sum(Payment.amount)).filter(
        Payment.school_id == school_id,
        Payment.payment_date >= current_month
    ).scalar() or Decimal('0')
    
    last_month_collected = db.session.query(func.sum(Payment.amount)).filter(
        Payment.school_id == school_id,
        Payment.payment_date >= last_month,
        Payment.payment_date < current_month
    ).scalar() or Decimal('0')
    
    # Calculate growth
    if last_month_collected > 0:
        collection_growth = round(((this_month_collected - last_month_collected) / last_month_collected) * 100, 1)
    else:
        collection_growth = 100 if this_month_collected > 0 else 0
    
    # Pending fees
    pending_amount = db.session.query(func.sum(StudentFeeStatus.remaining_amount)).filter(
        StudentFeeStatus.school_id == school_id,
        StudentFeeStatus.remaining_amount > 0
    ).scalar() or Decimal('0')
    
    pending_students = db.session.query(func.count(StudentFeeStatus.id)).filter(
        StudentFeeStatus.school_id == school_id,
        StudentFeeStatus.remaining_amount > 0
    ).scalar() or 0
    
    # Overdue statistics
    overdue_count = db.session.query(func.count(StudentFeeStatus.id)).filter(
        StudentFeeStatus.school_id == school_id,
        StudentFeeStatus.next_due_date < today,
        StudentFeeStatus.remaining_amount > 0
    ).scalar() or 0
    
    overdue_amount = db.session.query(func.sum(StudentFeeStatus.remaining_amount)).filter(
        StudentFeeStatus.school_id == school_id,
        StudentFeeStatus.next_due_date < today,
        StudentFeeStatus.remaining_amount > 0
    ).scalar() or Decimal('0')
    
    # Collection rate
    total_fee_due = total_collected + pending_amount
    if total_fee_due > 0:
        collection_rate = round((total_collected / total_fee_due) * 100, 1)
    else:
        collection_rate = 100
    
    # Payment methods statistics
    online_payments = db.session.query(func.count(Payment.id)).filter(
        Payment.school_id == school_id,
        Payment.payment_date >= current_month,
        Payment.payment_mode.in_([PaymentMode.ONLINE, PaymentMode.BANK_TRANSFER])
    ).scalar() or 0
    
    total_payments_this_month = db.session.query(func.count(Payment.id)).filter(
        Payment.school_id == school_id,
        Payment.payment_date >= current_month
    ).scalar() or 0
    
    online_percentage = round((online_payments / max(total_payments_this_month, 1)) * 100, 1)
    
    # Receipts generated
    receipts_generated = db.session.query(func.count(Payment.id)).filter(
        Payment.school_id == school_id,
        Payment.payment_date >= current_month
    ).scalar() or 0
    
    return {
        'total_collected': float(total_collected),
        'collection_growth': collection_growth,
        'pending_amount': float(pending_amount),
        'pending_students': pending_students,
        'collection_rate': collection_rate,
        'overdue_count': overdue_count,
        'overdue_amount': float(overdue_amount),
        'online_payments': online_percentage,
        'receipts_generated': receipts_generated,
        'digital_receipts': receipts_generated,  # All receipts are digital
        'payment_methods': {
            'online': online_payments,
            'total': total_payments_this_month
        }
    }


def generate_digital_receipt(payment, student, school):
    """Generate digital receipt data"""
    from utils.helpers import generate_qr_verification_url
    
    # Generate fee breakdown (simplified)
    fee_breakdown = [
        {'name': 'Tuition Fee', 'amount': float(payment.amount * Decimal('0.7'))},
        {'name': 'Transport Fee', 'amount': float(payment.amount * Decimal('0.2'))},
        {'name': 'Other Fees', 'amount': float(payment.amount * Decimal('0.1'))}
    ]
    
    verification_url = generate_qr_verification_url(payment.receipt_no)
    
    return {
        'receipt_no': payment.receipt_no,
        'payment_date': payment.payment_date.strftime('%d/%m/%Y'),
        'student_name': student.name,
        'admission_no': student.admission_no,
        'class_name': student.class_info.get_display_name() if student.class_info else 'No Class',
        'total_amount': float(payment.amount),
        'payment_method': payment.payment_mode.value.title(),
        'reference_number': payment.reference_number,
        'collected_by': payment.collector.name if payment.collector else 'System',
        'school_name': school.name,
        'school_address': school.address or '',
        'school_phone': school.phone or '',
        'school_email': school.email or '',
        'fee_breakdown': fee_breakdown,
        'verification_url': verification_url
    }


def process_verified_payment(student_id, amount, payment_method, reference_number, user, school):
    """Process a verified online payment"""
    from models.student import Student
    from models.fee import Payment, PaymentMode, PaymentStatus, StudentFeeStatus, FeeStructure
    from utils.helpers import generate_receipt_number
    from decimal import Decimal
    
    student = Student.query.filter_by(id=student_id, school_id=school.id).first()
    fee_structure = FeeStructure.query.filter_by(
        school_id=school.id,
        class_id=student.class_id,
        is_active=True
    ).first()
    
    # Create payment record
    payment = Payment(
        school_id=school.id,
        student_id=student_id,
        fee_structure_id=fee_structure.id,
        receipt_no=generate_receipt_number(school.id),
        amount=Decimal(str(amount)),
        payment_date=date.today(),
        payment_mode=PaymentMode.ONLINE,
        status=PaymentStatus.COMPLETED,
        reference_number=reference_number,
        collected_by=user.id
    )
    db.session.add(payment)
    
    # Update fee status
    fee_status = StudentFeeStatus.query.filter_by(
        student_id=student_id,
        fee_structure_id=fee_structure.id
    ).first()
    
    if fee_status:
        fee_status.paid_amount += Decimal(str(amount))
        fee_status.remaining_amount = max(Decimal('0'), fee_status.remaining_amount - Decimal(str(amount)))
        fee_status.last_payment_date = date.today()
    else:
        fee_status = StudentFeeStatus(
            school_id=school.id,
            student_id=student_id,
            fee_structure_id=fee_structure.id,
            total_amount=fee_structure.total_fee,
            paid_amount=Decimal(str(amount)),
            remaining_amount=max(Decimal('0'), fee_structure.total_fee - Decimal(str(amount))),
            last_payment_date=date.today()
        )
        db.session.add(fee_status)
    
    db.session.commit()
    
    return generate_digital_receipt(payment, student, school)


# Notification Management Routes
@school_admin_bp.route('/notifications')
@role_required('school_admin')
def notifications():
    """Notification management dashboard"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    from services.notification_service import NotificationService
    from models.notification import NotificationTemplate, NotificationLog
    
    # Get notification statistics
    notification_service = NotificationService(school.id)
    notification_stats = notification_service.get_delivery_statistics(days=30)
    
    # Get recent notification logs
    notification_logs = NotificationLog.query.filter_by(school_id=school.id)\
        .order_by(NotificationLog.created_at.desc())\
        .limit(50).all()
    
    # Get notification templates
    notification_templates = NotificationTemplate.query.filter_by(school_id=school.id)\
        .order_by(NotificationTemplate.created_at.desc()).all()
    
    return render_template('school_admin/notifications.html',
                         notification_stats=notification_stats,
                         notification_logs=notification_logs,
                         notification_templates=notification_templates)


@school_admin_bp.route('/notifications/send', methods=['POST'])
@role_required('school_admin')
def send_notification():
    """Send notification to selected recipients"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    data = request.get_json()
    
    try:
        from services.notification_service import NotificationService
        from models.notification import NotificationType, NotificationChannel
        from models.student import Student
        from models.teacher import Teacher
        
        notification_service = NotificationService(school.id)
        
        # Parse notification data
        notification_type = NotificationType(data.get('type'))
        channel = NotificationChannel(data.get('channel'))
        subject = data.get('subject', '')
        message = data.get('message')
        recipients_groups = data.get('recipients', [])
        
        # Build recipients list
        recipients = []
        
        for group in recipients_groups:
            if group == 'all_parents':
                students = Student.query.filter_by(school_id=school.id).all()
                for student in students:
                    if student.parent_phone or student.email:
                        recipients.append({
                            'type': 'parent',
                            'id': student.id,
                            'phone': student.parent_phone,
                            'email': student.email,
                            'name': student.father_name or student.mother_name or 'Parent',
                            'variables': {
                                'student_name': student.name,
                                'class_name': student.class_info.get_display_name() if student.class_info else 'N/A',
                                'school_name': school.name,
                                'date': datetime.now().strftime('%d/%m/%Y')
                            }
                        })
            
            elif group == 'all_teachers':
                teachers = Teacher.query.filter_by(school_id=school.id).all()
                for teacher in teachers:
                    if teacher.phone or teacher.email:
                        recipients.append({
                            'type': 'teacher',
                            'id': teacher.id,
                            'phone': teacher.phone,
                            'email': teacher.email,
                            'name': teacher.user.name if teacher.user else 'Teacher',
                            'variables': {
                                'teacher_name': teacher.user.name if teacher.user else 'Teacher',
                                'school_name': school.name,
                                'date': datetime.now().strftime('%d/%m/%Y')
                            }
                        })
        
        if not recipients:
            return jsonify({
                'success': False,
                'message': 'No recipients found for the selected groups'
            }), 400
        
        # Send notifications
        results = []
        sent_count = 0
        
        for recipient in recipients:
            # Create custom template for this message
            from models.notification import NotificationTemplate
            
            # Use the message directly
            success, result = notification_service.send_notification(
                notification_type,
                channel,
                recipient,
                recipient.get('variables', {}),
                template_id=None  # We'll create a temporary template
            )
            
            if success:
                sent_count += 1
            
            results.append({
                'recipient': recipient.get('name'),
                'success': success,
                'result': result
            })
        
        return jsonify({
            'success': True,
            'message': f'Notifications processed successfully',
            'sent_count': sent_count,
            'total_count': len(recipients),
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@school_admin_bp.route('/notifications/log/<int:log_id>')
@role_required('school_admin')
def get_notification_log(log_id):
    """Get notification log details"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    from models.notification import NotificationLog
    
    log = NotificationLog.query.filter_by(
        id=log_id,
        school_id=school.id
    ).first_or_404()
    
    return jsonify({
        'success': True,
        'log': log.to_dict()
    })


@school_admin_bp.route('/notifications/retry', methods=['POST'])
@role_required('school_admin')
def retry_notification():
    """Retry failed notification"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    data = request.get_json()
    log_id = data.get('log_id')
    
    try:
        from models.notification import NotificationLog
        from services.notification_service import NotificationService
        
        log = NotificationLog.query.filter_by(
            id=log_id,
            school_id=school.id
        ).first_or_404()
        
        if log.status.value != 'failed':
            return jsonify({
                'success': False,
                'message': 'Only failed notifications can be retried'
            }), 400
        
        notification_service = NotificationService(school.id)
        
        # Prepare recipient data
        recipient_data = {
            'type': log.recipient_type,
            'id': log.recipient_id,
            'phone': log.recipient_phone,
            'email': log.recipient_email,
            'name': log.recipient_name
        }
        
        # Retry sending
        success, result = notification_service.send_notification(
            log.type,
            log.channel,
            recipient_data,
            {},  # Variables would need to be stored/reconstructed
            log.template_id
        )
        
        if success:
            # Update retry count
            log.retry_count += 1
            db.session.commit()
        
        return jsonify({
            'success': success,
            'message': 'Notification retry completed' if success else f'Retry failed: {result}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@school_admin_bp.route('/notifications/templates', methods=['GET', 'POST'])
@role_required('school_admin')
def manage_notification_templates():
    """Manage notification templates"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    if request.method == 'POST':
        # Create new template
        data = request.get_json()
        
        try:
            from models.notification import NotificationTemplate, NotificationType, NotificationChannel
            
            template = NotificationTemplate(
                school_id=school.id,
                name=data.get('name'),
                type=NotificationType(data.get('type')),
                channel=NotificationChannel(data.get('channel')),
                subject=data.get('subject'),
                message_template=data.get('message_template'),
                is_active=data.get('is_active', True),
                is_default=data.get('is_default', False),
                available_variables=data.get('available_variables')
            )
            
            db.session.add(template)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Template created successfully',
                'template': template.to_dict()
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    else:
        # Get templates
        from models.notification import NotificationTemplate
        
        templates = NotificationTemplate.query.filter_by(school_id=school.id)\
            .order_by(NotificationTemplate.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'templates': [template.to_dict() for template in templates]
        })


@school_admin_bp.route('/notifications/auto-send')
@role_required('school_admin')
def auto_send_notifications():
    """Trigger automatic notifications (for testing/manual trigger)"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    try:
        from services.notification_service import NotificationScheduler
        
        scheduler = NotificationScheduler(school.id)
        
        # Run scheduled notifications
        scheduler.schedule_daily_attendance_alerts()
        scheduler.schedule_fee_reminders()
        scheduler.schedule_holiday_announcements()
        
        return jsonify({
            'success': True,
            'message': 'Automatic notifications triggered successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@school_admin_bp.route('/record_payment', methods=['POST'])
@role_required('school_admin')
def record_payment():
    """Record a fee payment"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    from models.student import Student
    from models.fee import Payment, PaymentMode, PaymentStatus, StudentFeeStatus, FeeStructure
    from utils.helpers import generate_receipt_number
    from decimal import Decimal
    from datetime import datetime, date
    
    try:
        student_id = int(request.form.get('student_id'))
        amount = Decimal(request.form.get('amount'))
        payment_mode = PaymentMode(request.form.get('payment_mode'))
        remarks = request.form.get('remarks', '')
        
        # Get student and fee structure
        student = Student.query.filter_by(id=student_id, school_id=school.id).first_or_404()
        fee_structure = FeeStructure.query.filter_by(
            school_id=school.id,
            class_id=student.class_id,
            is_active=True
        ).first()
        
        if not fee_structure:
            flash('No active fee structure found for this student', 'error')
            return redirect(url_for('school_admin.fees'))
        
        # Create payment record
        payment = Payment(
            school_id=school.id,
            student_id=student_id,
            fee_structure_id=fee_structure.id,
            receipt_no=generate_receipt_number(school.id),
            amount=amount,
            payment_date=date.today(),
            payment_mode=payment_mode,
            status=PaymentStatus.COMPLETED,
            remarks=remarks,
            collected_by=user.id
        )
        db.session.add(payment)
        
        # Update student fee status
        fee_status = StudentFeeStatus.query.filter_by(
            student_id=student_id,
            fee_structure_id=fee_structure.id
        ).first()
        
        if fee_status:
            fee_status.paid_amount += amount
            fee_status.last_payment_date = date.today()
            fee_status.calculate_status()
        else:
            # Create new fee status
            fee_status = StudentFeeStatus(
                school_id=school.id,
                student_id=student_id,
                fee_structure_id=fee_structure.id,
                total_fee=fee_structure.total_fee,
                paid_amount=amount,
                remaining_amount=fee_structure.total_fee - amount,
                last_payment_date=date.today()
            )
            fee_status.calculate_status()
            db.session.add(fee_status)
        
        db.session.commit()
        
        flash(f'Payment of ₹{amount} recorded successfully! Receipt: {payment.receipt_no}', 'success')
        
        # Send payment notification if enabled
        try:
            from utils.notification_service import NotificationService
            notification_service = NotificationService(school.id)
            notification_service.send_payment_confirmation(student, payment)
        except Exception as e:
            # Don't fail the payment if notification fails
            print(f"Notification error: {e}")
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error recording payment: {str(e)}', 'error')
    
    return redirect(url_for('school_admin.fees'))


@school_admin_bp.route('/teachers')
@role_required('school_admin')
def teachers():
    """List all teachers"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    # Get search and filter parameters
    search = request.args.get('search', '')
    subject_filter = request.args.get('subject', '')
    status_filter = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    
    # Build query
    from models.teacher import Teacher
    from models.classes import Subject
    
    query = Teacher.query.filter_by(school_id=school.id)
    
    # Apply filters
    if search:
        query = query.filter(
            db.or_(
                Teacher.name.contains(search),
                Teacher.employee_id.contains(search),
                Teacher.phone.contains(search),
                Teacher.email.contains(search)
            )
        )
    
    if subject_filter:
        query = query.filter(Teacher.subjects.any(Subject.id == subject_filter))
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    # Paginate results
    teachers = query.order_by(Teacher.created_at.desc()).paginate(
        page=page, per_page=25, error_out=False
    )
    
    # Get subjects for filter dropdown
    subjects = Subject.query.filter_by(school_id=school.id).all()
    
    return render_template('school_admin/teachers.html', 
                         teachers=teachers, 
                         subjects=subjects,
                         search=search,
                         subject_filter=subject_filter,
                         status_filter=status_filter,
                         user=user,
                         school=school)


@school_admin_bp.route('/teachers/<int:teacher_id>')
@role_required('school_admin')
def view_teacher(teacher_id):
    """View teacher profile with comprehensive information"""
    user = User.query.get(session['user_id'])
    school = user.school
    
    from models.teacher import Teacher
    from models.classes import Class, Subject
    from models.assignment import Assignment
    from models.attendance import Attendance
    from datetime import datetime, timedelta
    
    teacher = Teacher.query.filter_by(id=teacher_id, school_id=school.id).first_or_404()
    
    # Get teacher's classes and subjects
    teacher_classes = Class.query.filter_by(class_teacher_id=teacher.id).all()
    teacher_subjects = teacher.subjects
    
    # Get recent assignments
    recent_assignments = Assignment.query.filter_by(
        teacher_id=teacher.id,
        school_id=school.id
    ).order_by(Assignment.created_at.desc()).limit(5).all()
    
    # Calculate teacher statistics
    total_assignments = Assignment.query.filter_by(teacher_id=teacher.id).count()
    
    # Get attendance statistics (if teacher marks attendance)
    attendance_stats = {
        'classes_managed': len(teacher_classes),
        'subjects_taught': len(teacher_subjects),
        'total_assignments': total_assignments,
        'active_assignments': Assignment.query.filter_by(
            teacher_id=teacher.id,
            status='published'
        ).count()
    }
    
    return render_template('school_admin/teacher_profile.html',
                         teacher=teacher,
                         teacher_classes=teacher_classes,
                         teacher_subjects=teacher_subjects,
                         recent_assignments=recent_assignments,
                         attendance_stats=attendance_stats,
                         user=user,
                         school=school)


@school_admin_bp.route('/teachers/<int:teacher_id>/edit', methods=['GET', 'POST'])
@role_required('school_admin')
def edit_teacher(teacher_id):
    """Edit teacher information"""
    user = User.query.get(session['user_id'])
    school = user.school
    
    from models.teacher import Teacher, TeacherStatus
    from models.classes import Class, Subject
    from models.user import User as UserModel
    
    teacher = Teacher.query.filter_by(id=teacher_id, school_id=school.id).first_or_404()
    
    if request.method == 'POST':
        try:
            # Update teacher information
            teacher.name = request.form.get('name')
            teacher.employee_id = request.form.get('employee_id')
            teacher.phone = request.form.get('phone')
            teacher.email = request.form.get('email')
            teacher.address = request.form.get('address')
            teacher.qualification = request.form.get('qualification')
            teacher.experience_years = int(request.form.get('experience_years', 0))
            teacher.salary = float(request.form.get('salary', 0))
            teacher.status = TeacherStatus(request.form.get('status'))
            
            # Update subjects
            subject_ids = request.form.getlist('subjects')
            teacher.subjects = Subject.query.filter(Subject.id.in_(subject_ids)).all()
            
            # Update user account if exists
            if teacher.user:
                teacher.user.name = teacher.name
                teacher.user.email = teacher.email
            
            db.session.commit()
            flash('Teacher information updated successfully!', 'success')
            return redirect(url_for('school_admin.view_teacher', teacher_id=teacher.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating teacher: {str(e)}', 'error')
    
    # Get all subjects for the form
    subjects = Subject.query.filter_by(school_id=school.id).all()
    classes = Class.query.filter_by(school_id=school.id).all()
    
    return render_template('school_admin/edit_teacher.html',
                         teacher=teacher,
                         subjects=subjects,
                         classes=classes,
                         user=user,
                         school=school)


@school_admin_bp.route('/teachers/add', methods=['GET', 'POST'])
@role_required('school_admin')
def add_teacher():
    """Add new teacher"""
    user = User.query.get(session['user_id'])
    school = user.school
    
    if request.method == 'POST':
        try:
            from models.teacher import Teacher, TeacherStatus
            from models.classes import Subject
            from models.user import User as UserModel, UserRole
            from werkzeug.security import generate_password_hash
            
            # Create teacher record
            teacher = Teacher(
                school_id=school.id,
                name=request.form.get('name'),
                employee_id=request.form.get('employee_id'),
                phone=request.form.get('phone'),
                email=request.form.get('email'),
                address=request.form.get('address'),
                qualification=request.form.get('qualification'),
                experience_years=int(request.form.get('experience_years', 0)),
                salary=float(request.form.get('salary', 0)),
                status=TeacherStatus.ACTIVE
            )
            
            db.session.add(teacher)
            db.session.flush()  # Get teacher ID
            
            # Create user account
            if request.form.get('create_account') == 'on':
                password = request.form.get('password', 'teacher123')
                user_account = UserModel(
                    name=teacher.name,
                    email=teacher.email,
                    password_hash=generate_password_hash(password),
                    role=UserRole.TEACHER,
                    school_id=school.id,
                    teacher_id=teacher.id
                )
                db.session.add(user_account)
                teacher.user_id = user_account.id
            
            # Assign subjects
            subject_ids = request.form.getlist('subjects')
            teacher.subjects = Subject.query.filter(Subject.id.in_(subject_ids)).all()
            
            db.session.commit()
            flash('Teacher added successfully!', 'success')
            return redirect(url_for('school_admin.teachers'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding teacher: {str(e)}', 'error')
    
    # Get subjects for the form
    from models.classes import Subject
    subjects = Subject.query.filter_by(school_id=school.id).all()
    
    return render_template('school_admin/add_teacher.html',
                         subjects=subjects,
                         user=user,
                         school=school)


@school_admin_bp.route('/classes')
@role_required('school_admin')
def classes():
    """List all classes"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    # Get search and filter parameters
    search = request.args.get('search', '')
    academic_year_filter = request.args.get('academic_year', '')
    page = request.args.get('page', 1, type=int)
    
    # Build query
    from models.classes import Class
    from models.student import Student
    
    query = Class.query.filter_by(school_id=school.id)
    
    # Apply filters
    if search:
        query = query.filter(
            db.or_(
                Class.class_name.contains(search),
                Class.section.contains(search)
            )
        )
    
    if academic_year_filter:
        query = query.filter_by(academic_year=academic_year_filter)
    
    # Paginate results
    classes = query.order_by(Class.class_name, Class.section).paginate(
        page=page, per_page=25, error_out=False
    )
    
    # Add student count to each class
    for class_obj in classes.items:
        class_obj.student_count = Student.query.filter_by(class_id=class_obj.id).count()
    
    # Get academic years for filter dropdown
    academic_years = db.session.query(Class.academic_year).filter_by(school_id=school.id).distinct().all()
    academic_years = [year[0] for year in academic_years]
    
    return render_template('school_admin/classes.html', 
                         classes=classes, 
                         academic_years=academic_years,
                         search=search,
                         academic_year_filter=academic_year_filter,
                         user=user,
                         school=school)


@school_admin_bp.route('/classes/<int:class_id>')
@role_required('school_admin')
def view_class(class_id):
    """View class details with student list"""
    user = User.query.get(session['user_id'])
    school = user.school
    
    from models.classes import Class
    from models.student import Student
    from models.teacher import Teacher
    
    class_obj = Class.query.filter_by(id=class_id, school_id=school.id).first_or_404()
    
    # Get students in this class
    students = Student.query.filter_by(class_id=class_id).order_by(Student.roll_number).all()
    
    # Get class teacher
    class_teacher = Teacher.query.get(class_obj.class_teacher_id) if class_obj.class_teacher_id else None
    
    # Get class statistics
    class_stats = {
        'total_students': len(students),
        'male_students': len([s for s in students if s.gender and s.gender.value == 'male']),
        'female_students': len([s for s in students if s.gender and s.gender.value == 'female']),
        'active_students': len([s for s in students if s.status and s.status.value == 'active']),
    }
    
    return render_template('school_admin/class_profile.html',
                         class_obj=class_obj,
                         students=students,
                         class_teacher=class_teacher,
                         class_stats=class_stats,
                         user=user,
                         school=school)


@school_admin_bp.route('/classes/<int:class_id>/edit', methods=['GET', 'POST'])
@role_required('school_admin')
def edit_class(class_id):
    """Edit class information"""
    user = User.query.get(session['user_id'])
    school = user.school
    
    from models.classes import Class
    from models.teacher import Teacher
    
    class_obj = Class.query.filter_by(id=class_id, school_id=school.id).first_or_404()
    
    if request.method == 'POST':
        try:
            class_obj.class_name = request.form.get('class_name')
            class_obj.section = request.form.get('section')
            class_obj.academic_year = request.form.get('academic_year')
            class_obj.class_teacher_id = request.form.get('class_teacher_id') or None
            class_obj.room_number = request.form.get('room_number')
            class_obj.capacity = int(request.form.get('capacity', 0))
            
            db.session.commit()
            flash('Class information updated successfully!', 'success')
            return redirect(url_for('school_admin.view_class', class_id=class_obj.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating class: {str(e)}', 'error')
    
    # Get teachers for dropdown
    teachers = Teacher.query.filter_by(school_id=school.id).all()
    
    return render_template('school_admin/edit_class.html',
                         class_obj=class_obj,
                         teachers=teachers,
                         user=user,
                         school=school)


@school_admin_bp.route('/classes/add', methods=['GET', 'POST'])
@role_required('school_admin')
def add_class():
    """Add new class"""
    user = User.query.get(session['user_id'])
    school = user.school
    
    if request.method == 'POST':
        try:
            from models.classes import Class
            
            class_obj = Class(
                school_id=school.id,
                class_name=request.form.get('class_name'),
                section=request.form.get('section'),
                academic_year=request.form.get('academic_year'),
                class_teacher_id=request.form.get('class_teacher_id') or None,
                room_number=request.form.get('room_number'),
                capacity=int(request.form.get('capacity', 0))
            )
            
            db.session.add(class_obj)
            db.session.commit()
            
            flash('Class added successfully!', 'success')
            return redirect(url_for('school_admin.classes'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding class: {str(e)}', 'error')
    
    # Get teachers for dropdown
    from models.teacher import Teacher
    teachers = Teacher.query.filter_by(school_id=school.id).all()
    
    return render_template('school_admin/add_class.html',
                         teachers=teachers,
                         user=user,
                         school=school)


@school_admin_bp.route('/classes/<int:class_id>/promote', methods=['GET', 'POST'])
@role_required('school_admin')
def promote_class(class_id):
    """Promote students to next class"""
    user = User.query.get(session['user_id'])
    school = user.school
    
    from models.classes import Class
    from models.student import Student
    
    current_class = Class.query.filter_by(id=class_id, school_id=school.id).first_or_404()
    
    if request.method == 'POST':
        try:
            target_class_id = request.form.get('target_class_id')
            student_ids = request.form.getlist('student_ids')
            
            if not target_class_id:
                flash('Please select a target class', 'error')
                return redirect(request.url)
            
            # Update selected students
            promoted_count = 0
            for student_id in student_ids:
                student = Student.query.get(student_id)
                if student and student.class_id == class_id:
                    student.class_id = target_class_id
                    promoted_count += 1
            
            db.session.commit()
            flash(f'Successfully promoted {promoted_count} students!', 'success')
            return redirect(url_for('school_admin.view_class', class_id=class_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error promoting students: {str(e)}', 'error')
    
    # Get students in current class
    students = Student.query.filter_by(class_id=class_id).order_by(Student.roll_number).all()
    
    # Get available target classes
    target_classes = Class.query.filter_by(school_id=school.id).filter(Class.id != class_id).all()
    
    return render_template('school_admin/promote_class.html',
                         current_class=current_class,
                         students=students,
                         target_classes=target_classes,
                         user=user,
                         school=school)


@school_admin_bp.route('/subjects')
@role_required('school_admin')
def subjects():
    """List all subjects"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)

    # Get search and filter parameters
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)

    # Build query
    from models.classes import Subject

    query = Subject.query.filter_by(school_id=school.id)

    # Apply filters
    if search:
        query = query.filter(
            db.or_(
                Subject.name.contains(search),
                Subject.code.contains(search)
            )
        )

    # Paginate results
    subjects = query.order_by(Subject.name).paginate(
        page=page, per_page=25, error_out=False
    )

    return render_template('school_admin/subjects.html',
                         subjects=subjects,
                         search=search,
                         user=user,
                         school=school)


@school_admin_bp.route('/subjects/add', methods=['GET', 'POST'])
@role_required('school_admin')
def add_subject():
    """Add new subject"""
    user = User.query.get(session['user_id'])
    school = user.school

    if request.method == 'POST':
        try:
            from models.classes import Subject, Class

            subject = Subject(
                school_id=school.id,
                name=request.form.get('name'),
                code=request.form.get('code'),
                class_id=request.form.get('class_id'),
                description=request.form.get('description')
            )

            db.session.add(subject)
            db.session.commit()

            flash('Subject added successfully!', 'success')
            return redirect(url_for('school_admin.subjects'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error adding subject: {str(e)}', 'error')

    # Get classes for dropdown
    from models.classes import Class
    classes = Class.query.filter_by(school_id=school.id).all()

    return render_template('school_admin/add_subject.html',
                         classes=classes,
                         user=user,
                         school=school)


@school_admin_bp.route('/subjects/<int:subject_id>/edit', methods=['GET', 'POST'])
@role_required('school_admin')
def edit_subject(subject_id):
    """Edit subject information"""
    user = User.query.get(session['user_id'])
    school = user.school

    from models.classes import Subject, Class

    subject = Subject.query.filter_by(id=subject_id, school_id=school.id).first_or_404()

    if request.method == 'POST':
        try:
            subject.name = request.form.get('name')
            subject.code = request.form.get('code')
            subject.class_id = request.form.get('class_id')
            subject.description = request.form.get('description')

            db.session.commit()
            flash('Subject updated successfully!', 'success')
            return redirect(url_for('school_admin.subjects'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating subject: {str(e)}', 'error')

    # Get classes for dropdown
    classes = Class.query.filter_by(school_id=school.id).all()

    return render_template('school_admin/edit_subject.html',
                         subject=subject,
                         classes=classes,
                         user=user,
                         school=school)


@school_admin_bp.route('/subjects/<int:subject_id>/delete', methods=['POST'])
@role_required('school_admin')
def delete_subject(subject_id):
    """Delete a subject"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)

    from models.classes import Subject

    try:
        subject = Subject.query.filter_by(id=subject_id, school_id=school.id).first_or_404()
        subject_name = subject.name

        db.session.delete(subject)
        db.session.commit()

        flash(f'Subject {subject_name} deleted successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting subject: {str(e)}', 'error')

    return redirect(url_for('school_admin.subjects'))


@school_admin_bp.route('/reports')
@role_required('school_admin')
def reports():
    """Enhanced reports dashboard with comprehensive analytics"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    # Get comprehensive statistics
    stats = get_comprehensive_stats(school.id)
    
    # Get classes for filter dropdown
    classes = Class.query.filter_by(school_id=school.id).order_by(Class.class_name, Class.section).all()
    
    # Get recent activities
    recent_activities = get_recent_activities(school.id, limit=10)
    
    return render_template('school_admin/reports.html', 
                         stats=stats,
                         classes=classes,
                         recent_activities=recent_activities)


@school_admin_bp.route('/reports/generate', methods=['POST'])
@role_required('school_admin')
def generate_report():
    """Generate comprehensive reports based on category and type"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    data = request.get_json()
    category = data.get('category')
    report_type = data.get('type')
    filters = data.get('filters', {})
    
    try:
        # Import the advanced report service
        from services.advanced_report_service import AdvancedReportService
        
        report_service = AdvancedReportService(school.id)
        report_data = report_service.generate_report(category, report_type, filters)
        
        return jsonify({
            'success': True,
            'report': report_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@school_admin_bp.route('/reports/export', methods=['POST'])
@role_required('school_admin')
def export_report():
    """Export reports in various formats (PDF, Excel, CSV)"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    data = request.get_json()
    report_data = data.get('reportData')
    export_format = data.get('format', 'pdf')
    filters = data.get('filters', {})
    
    try:
        from services.advanced_report_service import AdvancedReportService
        
        report_service = AdvancedReportService(school.id)
        
        if export_format == 'pdf':
            file_data, filename = report_service.export_to_pdf(report_data, filters)
            mimetype = 'application/pdf'
        elif export_format == 'excel':
            file_data, filename = report_service.export_to_excel(report_data, filters)
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif export_format == 'csv':
            file_data, filename = report_service.export_to_csv(report_data, filters)
            mimetype = 'text/csv'
        else:
            return jsonify({'error': 'Unsupported format'}), 400
        
        from flask import Response
        return Response(
            file_data,
            mimetype=mimetype,
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_comprehensive_stats(school_id):
    """Get comprehensive statistics for the reports dashboard"""
    from models.student import Student, StudentStatus
    from models.teacher import Teacher
    from models.classes import Class, Subject
    from models.fee import Payment, StudentFeeStatus
    from models.attendance import Attendance, AttendanceStatus
    from datetime import datetime, date, timedelta
    from decimal import Decimal
    
    today = date.today()
    current_month = today.replace(day=1)
    last_month = (current_month - timedelta(days=1)).replace(day=1)
    thirty_days_ago = today - timedelta(days=30)
    
    # Basic counts
    total_students = Student.query.filter_by(school_id=school_id, status=StudentStatus.ACTIVE).count()
    total_teachers = Teacher.query.filter_by(school_id=school_id).count()
    total_classes = Class.query.filter_by(school_id=school_id).count()
    
    # Active teachers
    active_teachers = Teacher.query.filter_by(school_id=school_id, status='active').count()
    
    # Student growth calculation
    students_this_month = Student.query.filter(
        Student.school_id == school_id,
        Student.admission_date >= current_month
    ).count()
    
    students_last_month = Student.query.filter(
        Student.school_id == school_id,
        Student.admission_date >= last_month,
        Student.admission_date < current_month
    ).count()
    
    if students_last_month > 0:
        student_growth = round(((students_this_month - students_last_month) / students_last_month) * 100, 1)
    else:
        student_growth = 100 if students_this_month > 0 else 0
    
    # Average class size
    if total_classes > 0:
        avg_class_size = round(total_students / total_classes, 1)
    else:
        avg_class_size = 0
    
    # Revenue calculations
    payments_this_month = Payment.query.filter(
        Payment.school_id == school_id,
        Payment.payment_date >= current_month
    ).all()
    
    payments_last_month = Payment.query.filter(
        Payment.school_id == school_id,
        Payment.payment_date >= last_month,
        Payment.payment_date < current_month
    ).all()
    
    total_revenue = sum(payment.amount for payment in payments_this_month)
    last_month_revenue = sum(payment.amount for payment in payments_last_month)
    
    if last_month_revenue > 0:
        revenue_growth = round(((total_revenue - last_month_revenue) / last_month_revenue) * 100, 1)
    else:
        revenue_growth = 100 if total_revenue > 0 else 0
    
    # Attendance calculations
    total_attendance = Attendance.query.filter(
        Attendance.school_id == school_id,
        Attendance.date >= thirty_days_ago
    ).count()
    
    present_attendance = Attendance.query.filter(
        Attendance.school_id == school_id,
        Attendance.date >= thirty_days_ago,
        Attendance.status == AttendanceStatus.PRESENT
    ).count()
    
    if total_attendance > 0:
        attendance_rate = round((present_attendance / total_attendance) * 100, 1)
    else:
        attendance_rate = 0
    
    # Fee collection calculations
    total_fee_due = db.session.query(
        func.sum(StudentFeeStatus.total_amount)
    ).filter(
        StudentFeeStatus.school_id == school_id
    ).scalar() or Decimal('0')
    
    collected_fees = db.session.query(
        func.sum(Payment.amount)
    ).filter(
        Payment.school_id == school_id
    ).scalar() or Decimal('0')
    
    if total_fee_due > 0:
        collection_rate = round((float(collected_fees) / float(total_fee_due)) * 100, 1)
    else:
        collection_rate = 100
    
    pending_fees = total_fee_due - collected_fees
    
    return {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_classes': total_classes,
        'active_teachers': active_teachers,
        'student_growth': student_growth,
        'avg_class_size': avg_class_size,
        'total_revenue': float(total_revenue),
        'revenue_growth': revenue_growth,
        'attendance_rate': attendance_rate,
        'collection_rate': collection_rate,
        'pending_fees': float(pending_fees)
    }


@school_admin_bp.route('/students/<int:student_id>/delete', methods=['POST'])
@role_required('school_admin')
def delete_student(student_id):
    """Delete a student"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    from models.student import Student
    
    try:
        student = Student.query.filter_by(id=student_id, school_id=school.id).first_or_404()
        student_name = student.name
        
        # Delete related records first
        from models.attendance import Attendance
        from models.fee import Payment, StudentFeeStatus
        
        # Delete attendance records
        Attendance.query.filter_by(student_id=student_id).delete()
        
        # Delete payment records
        Payment.query.filter_by(student_id=student_id).delete()
        
        # Delete fee status records
        StudentFeeStatus.query.filter_by(student_id=student_id).delete()
        
        # Delete the student
        db.session.delete(student)
        db.session.commit()
        
        flash(f'Student {student_name} deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting student: {str(e)}', 'error')
    
    return redirect(url_for('school_admin.students'))


@school_admin_bp.route('/students/export')
@role_required('school_admin')
def export_students():
    """Export students to CSV"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    from utils.student_helpers import export_students_csv
    from flask import Response
    
    class_id = request.args.get('class_id')
    csv_data = export_students_csv(school.id, class_id)
    
    filename = f"students_{school.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv"
    
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


@school_admin_bp.route('/students/import', methods=['GET', 'POST'])
@role_required('school_admin')
def import_students():
    """Import students from CSV"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    if request.method == 'POST':
        if 'csv_file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('school_admin.students'))
        
        csv_file = request.files['csv_file']
        if csv_file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('school_admin.students'))
        
        if not csv_file.filename.endswith('.csv'):
            flash('Please upload a CSV file', 'error')
            return redirect(url_for('school_admin.students'))
        
        from utils.student_helpers import import_students_csv
        results = import_students_csv(school.id, csv_file)
        
        if results['success'] > 0:
            flash(f'Successfully imported {results["success"]} students', 'success')
        
        for error in results['errors']:
            flash(error, 'error')
        
        for warning in results['warnings']:
            flash(warning, 'warning')
        
        return redirect(url_for('school_admin.students'))
    
    return render_template('school_admin/import_students.html')


@school_admin_bp.route('/students/generate-admission-number')
@role_required('school_admin')
def generate_admission_number_api():
    """Generate admission number via API"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    from utils.student_helpers import generate_admission_number
    from flask import jsonify
    
    admission_no = generate_admission_number(school.id)
    return jsonify({'admission_no': admission_no})


@school_admin_bp.route('/setup_wizard', methods=['GET', 'POST'])
@role_required('school_admin')
def setup_wizard():
    """Setup wizard for new schools"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    from models.classes import Class, Subject
    from models.fee import FeeStructure
    from utils.helpers import get_available_classes, get_class_subjects
    from decimal import Decimal
    
    # Get current step
    step = int(request.args.get('step', 1))
    
    # Initialize session data
    if 'setup_data' not in session:
        session['setup_data'] = {}
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'next' or action == 'complete':
            # Save current step data
            if step == 1:
                # Save selected classes
                selected_classes = request.form.getlist('selected_classes')
                if not selected_classes:
                    flash('Please select at least one class', 'error')
                    return redirect(url_for('school_admin.setup_wizard', step=1))
                session['setup_data']['selected_classes'] = selected_classes
                
            elif step == 2:
                # Save fee structure
                fees = {}
                installments = {}
                for class_name in session['setup_data']['selected_classes']:
                    fee_key = f"fee_{class_name.replace(' ', '_')}"
                    installment_key = f"installments_{class_name.replace(' ', '_')}"
                    
                    fee_amount = request.form.get(fee_key)
                    installment_count = request.form.get(installment_key)
                    
                    if not fee_amount or float(fee_amount) <= 0:
                        flash(f'Please enter valid fee for {class_name}', 'error')
                        return redirect(url_for('school_admin.setup_wizard', step=2))
                    
                    fees[class_name] = float(fee_amount)
                    installments[class_name] = int(installment_count)
                
                session['setup_data']['fees'] = fees
                session['setup_data']['installments'] = installments
                
            elif step == 3:
                # Save subjects
                subjects = {}
                for class_name in session['setup_data']['selected_classes']:
                    subject_key = f"subjects_{class_name.replace(' ', '_')}"
                    selected_subjects = request.form.getlist(subject_key)
                    subjects[class_name] = selected_subjects
                
                session['setup_data']['subjects'] = subjects
            
            # Move to next step or complete setup
            if action == 'complete':
                # Create classes, subjects, and fee structures
                try:
                    academic_year = "2024-25"  # Current academic year
                    
                    for class_name in session['setup_data']['selected_classes']:
                        # Create class
                        new_class = Class(
                            school_id=school.id,
                            class_name=class_name,
                            section="A",  # Default section
                            capacity=60,
                            academic_year=academic_year
                        )
                        db.session.add(new_class)
                        db.session.flush()  # Get class ID
                        
                        # Create subjects for this class
                        if class_name in session['setup_data']['subjects']:
                            for subject_name in session['setup_data']['subjects'][class_name]:
                                subject = Subject(
                                    school_id=school.id,
                                    class_id=new_class.id,
                                    name=subject_name,
                                    code=subject_name[:3].upper()
                                )
                                db.session.add(subject)
                        
                        # Create fee structure
                        if class_name in session['setup_data']['fees']:
                            fee_structure = FeeStructure(
                                school_id=school.id,
                                class_id=new_class.id,
                                academic_year=academic_year,
                                total_fee=Decimal(str(session['setup_data']['fees'][class_name])),
                                tuition_fee=Decimal(str(session['setup_data']['fees'][class_name] * 0.7)),  # 70% tuition
                                admission_fee=Decimal(str(session['setup_data']['fees'][class_name] * 0.1)),  # 10% admission
                                development_fee=Decimal(str(session['setup_data']['fees'][class_name] * 0.1)),  # 10% development
                                other_fee=Decimal(str(session['setup_data']['fees'][class_name] * 0.1)),  # 10% other
                                installments=session['setup_data']['installments'][class_name],
                                is_active=True
                            )
                            db.session.add(fee_structure)
                    
                    # Mark setup as completed
                    school.setup_completed = True
                    db.session.commit()
                    
                    # Clear setup data
                    session.pop('setup_data', None)
                    
                    flash('School setup completed successfully!', 'success')
                    return redirect(url_for('school_admin.dashboard'))
                    
                except Exception as e:
                    db.session.rollback()
                    flash(f'Error completing setup: {str(e)}', 'error')
                    return redirect(url_for('school_admin.setup_wizard', step=3))
            else:
                # Move to next step
                return redirect(url_for('school_admin.setup_wizard', step=step + 1))
        
        elif action == 'previous':
            return redirect(url_for('school_admin.setup_wizard', step=step - 1))
    
    # Prepare template data
    template_data = {
        'step': step,
        'progress': (step / 3) * 100,
        'available_classes': get_available_classes(),
        'selected_classes': session['setup_data'].get('selected_classes', []),
        'fees': session['setup_data'].get('fees', {}),
        'installments': session['setup_data'].get('installments', {}),
        'class_subjects': {}
    }
    
    # Get subjects for selected classes
    if 'selected_classes' in session['setup_data']:
        for class_name in session['setup_data']['selected_classes']:
            template_data['class_subjects'][class_name] = get_class_subjects(class_name)
    
    return render_template('school_admin/setup_wizard.html', **template_data)


@school_admin_bp.route('/file_manager')
@role_required('school_admin')
def file_manager():
    """File manager page"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    if not school:
        flash('School not found.', 'error')
        return redirect(url_for('auth.logout'))
    
    # Get storage statistics
    from services.file_upload_service import FileUploadService
    import os
    service = FileUploadService()
    
    try:
        # Calculate basic storage stats
        directories = [
            'students/photos', 'teachers/photos', 'assignments/materials',
            'assignments/submissions', 'system/receipts', 'system/backups', 'temp'
        ]
        
        total_size = 0
        file_counts = {'image': 0, 'document': 0, 'assignment': 0, 'total': 0}
        
        for directory in directories:
            dir_size = service.get_directory_size(directory)
            total_size += dir_size
            
            # Count files
            full_path = os.path.join(service.upload_folder, directory)
            if os.path.exists(full_path):
                for filename in os.listdir(full_path):
                    if os.path.isfile(os.path.join(full_path, filename)):
                        file_counts['total'] += 1
                        
                        ext = filename.split('.')[-1].lower()
                        if ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
                            file_counts['image'] += 1
                        elif ext in ['pdf', 'doc', 'docx', 'txt', 'rtf']:
                            file_counts['document'] += 1
                        elif directory.startswith('assignments'):
                            file_counts['assignment'] += 1
        
        storage_stats = {
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'image_count': file_counts['image'],
            'document_count': file_counts['document'],
            'assignment_count': file_counts['assignment'],
            'total_files': file_counts['total']
        }
        
    except Exception as e:
        storage_stats = {
            'total_size_mb': 0,
            'image_count': 0,
            'document_count': 0,
            'assignment_count': 0,
            'total_files': 0
        }
    
    return render_template('admin/file_manager.html', 
                         user=user, 
                         school=school,
                         storage_stats=storage_stats)


@school_admin_bp.route('/fee_analytics')
@role_required('school_admin')
def fee_analytics():
    """Fee analytics dashboard"""
    user = User.query.get(session['user_id'])
    school = user.school
    
    return render_template('school_admin/fee_analytics_dashboard.html',
                         user=user, school=school)



@school_admin_bp.route('/fee_management')
@role_required('school_admin')
def fee_management():
    """Fee management dashboard"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    if not school:
        flash('School not found.', 'error')
        return redirect(url_for('auth.logout'))
    
    from services.fee_service import FeeService
    from models.fee import FeeStructure, Payment, StudentFeeStatus
    from models.student import Student
    from models.classes import Class
    from datetime import datetime, date, timedelta
    
    fee_service = FeeService(school.id)
    
    # Get fee analytics
    analytics_result = fee_service.get_fee_analytics()
    fee_analytics = analytics_result.get('analytics', {}) if analytics_result.get('success') else {}
    
    # Add growth calculation (mock data for now)
    fee_analytics['collection_growth'] = 12.5  # This would be calculated from historical data
    
    # Get recent payments
    recent_payments = Payment.query.filter_by(
        school_id=school.id
    ).order_by(Payment.created_at.desc()).limit(10).all()
    
    # Get outstanding fees
    outstanding_fees = StudentFeeStatus.query.filter(
        StudentFeeStatus.school_id == school.id,
        StudentFeeStatus.remaining_amount > 0
    ).order_by(StudentFeeStatus.payment_percentage.asc()).limit(20).all()
    
    # Get fee structures
    fee_structures = FeeStructure.query.filter_by(
        school_id=school.id,
        is_active=True
    ).order_by(FeeStructure.created_at.desc()).all()
    
    # Get defaulters
    defaulters_result = fee_service.get_defaulter_list()
    defaulters = defaulters_result.get('defaulters', []) if defaulters_result.get('success') else []
    
    # Get students and classes for forms
    students = Student.query.filter_by(school_id=school.id, status='active').all()
    classes = Class.query.filter_by(school_id=school.id).all()
    
    return render_template('school_admin/fee_management.html',
                         user=user,
                         school=school,
                         fee_analytics=fee_analytics,
                         recent_payments=recent_payments,
                         outstanding_fees=outstanding_fees,
                         fee_structures=fee_structures,
                         defaulters=defaulters,
                         students=students,
                         classes=classes)


@school_admin_bp.route('/notification_center')
@role_required('school_admin')
def notification_center():
    """Notification center dashboard"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    if not school:
        flash('School not found.', 'error')
        return redirect(url_for('auth.logout'))
    
    from services.notification_service import NotificationService
    from models.notification import NotificationLog, NotificationTemplate
    from models.student import Student
    
    notification_service = NotificationService(school.id)
    
    # Get notification statistics
    stats = notification_service.get_delivery_statistics(30)
    
    # Format statistics for display
    notification_stats = {
        'total_sent': sum(channel_stats['sent'] for channel_stats in stats.values()),
        'sms_sent': stats.get('sms', {}).get('sent', 0),
        'sms_delivered': stats.get('sms', {}).get('delivered', 0),
        'whatsapp_sent': stats.get('whatsapp', {}).get('sent', 0),
        'whatsapp_delivered': stats.get('whatsapp', {}).get('delivered', 0),
        'email_sent': stats.get('email', {}).get('sent', 0),
        'email_delivered': stats.get('email', {}).get('delivered', 0)
    }
    
    # Get recent notifications
    recent_notifications = NotificationLog.query.filter_by(
        school_id=school.id
    ).order_by(NotificationLog.created_at.desc()).limit(20).all()
    
    # Get notification templates
    notification_templates = NotificationTemplate.query.filter_by(
        school_id=school.id,
        is_active=True
    ).order_by(NotificationTemplate.created_at.desc()).all()
    
    # Get students for recipient selection
    students = Student.query.filter_by(
        school_id=school.id,
        status='active'
    ).order_by(Student.name).all()
    
    return render_template('school_admin/notification_center.html',
                         user=user,
                         school=school,
                         notification_stats=notification_stats,
                         recent_notifications=recent_notifications,
                         notification_templates=notification_templates,
                         students=students)


@school_admin_bp.route('/settings')
@role_required('school_admin')
def settings():
    """School settings page"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    return render_template('school_admin/settings.html', school=school)

# Dashboard Helper Functions

def calculate_dashboard_kpis(school_id):
    """Calculate comprehensive KPIs for dashboard"""
    from models.student import Student, StudentStatus
    from models.teacher import Teacher, TeacherStatus
    from models.classes import Class, Subject
    from models.attendance import Attendance, AttendanceStatus
    from models.fee import Payment, StudentFeeStatus, FeeStructure
    from datetime import datetime, date, timedelta
    from decimal import Decimal
    from sqlalchemy import func, and_, extract
    
    kpis = {}
    
    # Student KPIs
    total_students = Student.query.filter_by(school_id=school_id).count()
    active_students = Student.query.filter_by(school_id=school_id, status=StudentStatus.ACTIVE).count()
    inactive_students = total_students - active_students
    
    # Calculate student growth (last 30 days vs previous 30 days)
    thirty_days_ago = date.today() - timedelta(days=30)
    sixty_days_ago = date.today() - timedelta(days=60)
    
    recent_students = Student.query.filter(
        Student.school_id == school_id,
        Student.created_at >= thirty_days_ago
    ).count()
    
    previous_students = Student.query.filter(
        Student.school_id == school_id,
        Student.created_at >= sixty_days_ago,
        Student.created_at < thirty_days_ago
    ).count()
    
    students_growth = ((recent_students - previous_students) / max(previous_students, 1)) * 100 if previous_students > 0 else 0
    
    # Teacher KPIs
    total_teachers = Teacher.query.filter_by(school_id=school_id).count()
    active_teachers = Teacher.query.filter_by(school_id=school_id, status=TeacherStatus.ACTIVE).count()
    subjects_covered = Subject.query.filter_by(school_id=school_id).count()
    
    # Calculate teacher growth
    recent_teachers = Teacher.query.filter(
        Teacher.school_id == school_id,
        Teacher.created_at >= thirty_days_ago
    ).count()
    
    previous_teachers = Teacher.query.filter(
        Teacher.school_id == school_id,
        Teacher.created_at >= sixty_days_ago,
        Teacher.created_at < thirty_days_ago
    ).count()
    
    teachers_growth = ((recent_teachers - previous_teachers) / max(previous_teachers, 1)) * 100 if previous_teachers > 0 else 0
    
    # Attendance KPIs (today)
    today = date.today()
    total_attendance_today = Attendance.query.filter_by(school_id=school_id, date=today).count()
    present_today = Attendance.query.filter_by(
        school_id=school_id, 
        date=today, 
        status=AttendanceStatus.PRESENT
    ).count()
    absent_today = total_attendance_today - present_today
    
    attendance_percentage = (present_today / max(total_attendance_today, 1)) * 100 if total_attendance_today > 0 else 0
    
    # Calculate attendance trend (today vs yesterday)
    yesterday = today - timedelta(days=1)
    yesterday_total = Attendance.query.filter_by(school_id=school_id, date=yesterday).count()
    yesterday_present = Attendance.query.filter_by(
        school_id=school_id, 
        date=yesterday, 
        status=AttendanceStatus.PRESENT
    ).count()
    
    yesterday_percentage = (yesterday_present / max(yesterday_total, 1)) * 100 if yesterday_total > 0 else 0
    attendance_trend = attendance_percentage - yesterday_percentage
    
    # Fee KPIs
    current_month = date.today().replace(day=1)
    fees_collected = db.session.query(func.sum(Payment.amount)).filter(
        Payment.school_id == school_id,
        Payment.payment_date >= current_month
    ).scalar() or Decimal('0')
    
    # Calculate total fees due for current month
    active_fee_structures = FeeStructure.query.filter_by(school_id=school_id, is_active=True).all()
    total_expected = sum(fs.total_fee for fs in active_fee_structures) * active_students
    fees_due = total_expected
    
    collection_rate = (float(fees_collected) / float(max(fees_due, 1))) * 100 if fees_due > 0 else 0
    
    # Calculate fee growth
    last_month = (current_month - timedelta(days=1)).replace(day=1)
    last_month_collected = db.session.query(func.sum(Payment.amount)).filter(
        Payment.school_id == school_id,
        Payment.payment_date >= last_month,
        Payment.payment_date < current_month
    ).scalar() or Decimal('0')
    
    fees_growth = ((float(fees_collected) - float(last_month_collected)) / max(float(last_month_collected), 1)) * 100 if last_month_collected > 0 else 0
    
    # Classes KPI
    classes_active = Class.query.filter_by(school_id=school_id).count()
    
    kpis.update({
        'total_students': total_students,
        'active_students': active_students,
        'inactive_students': inactive_students,
        'students_growth': round(students_growth, 1),
        'total_teachers': total_teachers,
        'active_teachers': active_teachers,
        'teachers_growth': round(teachers_growth, 1),
        'subjects_covered': subjects_covered,
        'attendance_percentage': round(attendance_percentage, 1),
        'attendance_trend': round(attendance_trend, 1),
        'present_today': present_today,
        'absent_today': absent_today,
        'fees_collected': float(fees_collected),
        'fees_due': float(fees_due),
        'collection_rate': round(collection_rate, 1),
        'fees_growth': round(fees_growth, 1),
        'classes_active': classes_active
    })
    
    return kpis


def generate_chart_data(school_id):
    """Generate data for dashboard charts"""
    from models.student import Student
    from models.teacher import Teacher
    from models.classes import Class
    from models.attendance import Attendance, AttendanceStatus
    from models.fee import Payment
    from datetime import datetime, date, timedelta
    from sqlalchemy import func, extract
    
    chart_data = {}
    
    # Attendance trend data (last 6 months)
    attendance_data = []
    for i in range(6):
        month_date = date.today().replace(day=1) - timedelta(days=30*i)
        month_name = month_date.strftime('%b %Y')
        
        # Calculate attendance percentage for the month
        month_start = month_date.replace(day=1)
        if i == 0:
            month_end = date.today()
        else:
            next_month = month_start + timedelta(days=32)
            month_end = next_month.replace(day=1) - timedelta(days=1)
        
        total_attendance = Attendance.query.filter(
            Attendance.school_id == school_id,
            Attendance.date >= month_start,
            Attendance.date <= month_end
        ).count()
        
        present_attendance = Attendance.query.filter(
            Attendance.school_id == school_id,
            Attendance.date >= month_start,
            Attendance.date <= month_end,
            Attendance.status == AttendanceStatus.PRESENT
        ).count()
        
        percentage = (present_attendance / max(total_attendance, 1)) * 100 if total_attendance > 0 else 0
        
        attendance_data.insert(0, {
            'month': month_name,
            'percentage': round(percentage, 1)
        })
    
    chart_data['attendance'] = attendance_data
    
    # Fee collection data (last 4 weeks)
    fee_data = []
    for i in range(4):
        week_start = date.today() - timedelta(days=7*(i+1))
        week_end = date.today() - timedelta(days=7*i)
        
        collected = db.session.query(func.sum(Payment.amount)).filter(
            Payment.school_id == school_id,
            Payment.payment_date >= week_start,
            Payment.payment_date < week_end
        ).scalar() or 0
        
        # Estimate pending (simplified calculation)
        pending = max(0, 50000 - float(collected))  # Placeholder logic
        
        fee_data.insert(0, {
            'period': f'Week {4-i}',
            'collected': float(collected),
            'pending': pending
        })
    
    chart_data['fees'] = fee_data
    
    # Class distribution data
    class_distribution = []
    classes = Class.query.filter_by(school_id=school_id).all()
    colors = ['#FF6B35', '#F7931E', '#FFD23F', '#06FFA5', '#118AB2', '#4D5AAF', '#9B59B6', '#E74C3C']
    
    for i, class_obj in enumerate(classes):
        student_count = Student.query.filter_by(class_id=class_obj.id).count()
        if student_count > 0:
            class_distribution.append({
                'class': class_obj.get_display_name(),
                'students': student_count,
                'color': colors[i % len(colors)]
            })
    
    chart_data['class_distribution'] = class_distribution
    
    # Students trend (last 6 months)
    students_trend = []
    for i in range(6):
        month_date = date.today() - timedelta(days=30*i)
        count = Student.query.filter(
            Student.school_id == school_id,
            Student.created_at <= month_date
        ).count()
        students_trend.insert(0, count)
    
    chart_data['students_trend'] = students_trend
    
    # Teachers trend (last 6 months)
    teachers_trend = []
    for i in range(6):
        month_date = date.today() - timedelta(days=30*i)
        count = Teacher.query.filter(
            Teacher.school_id == school_id,
            Teacher.created_at <= month_date
        ).count()
        teachers_trend.insert(0, count)
    
    chart_data['teachers_trend'] = teachers_trend
    
    return chart_data


def get_recent_activities(school_id, limit=10):
    """Get recent activities for the school"""
    from models.student import Student
    from models.teacher import Teacher
    from models.fee import Payment
    from models.attendance import Attendance
    from datetime import datetime, timedelta
    
    activities = []
    
    # Recent student additions
    recent_students = Student.query.filter(
        Student.school_id == school_id,
        Student.created_at >= datetime.now() - timedelta(days=7)
    ).order_by(Student.created_at.desc()).limit(5).all()
    
    for student in recent_students:
        activities.append({
            'type': 'students',
            'icon': 'user-plus',
            'description': f'New student {student.name} added to {student.class_info.get_display_name() if student.class_info else "school"}',
            'timestamp': int(student.created_at.timestamp() * 1000),
            'time_ago': get_time_ago(student.created_at)
        })
    
    # Recent payments
    recent_payments = Payment.query.filter(
        Payment.school_id == school_id,
        Payment.payment_date >= datetime.now().date() - timedelta(days=7)
    ).order_by(Payment.created_at.desc()).limit(5).all()
    
    for payment in recent_payments:
        activities.append({
            'type': 'fees',
            'icon': 'money-bill-wave',
            'description': f'Payment of ₹{payment.amount:,.0f} received (Receipt: {payment.receipt_no})',
            'timestamp': int(payment.created_at.timestamp() * 1000),
            'time_ago': get_time_ago(payment.created_at)
        })
    
    # Recent attendance marking
    recent_attendance = db.session.query(Attendance.date, func.count(Attendance.id)).filter(
        Attendance.school_id == school_id,
        Attendance.date >= datetime.now().date() - timedelta(days=7)
    ).group_by(Attendance.date).order_by(Attendance.date.desc()).limit(3).all()
    
    for att_date, count in recent_attendance:
        activities.append({
            'type': 'attendance',
            'icon': 'calendar-check',
            'description': f'Attendance marked for {count} students on {att_date.strftime("%B %d")}',
            'timestamp': int(datetime.combine(att_date, datetime.min.time()).timestamp() * 1000),
            'time_ago': get_time_ago(datetime.combine(att_date, datetime.min.time()))
        })
    
    # Sort by timestamp and return limited results
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    return activities[:limit]


def get_top_students(school_id, limit=5):
    """Get top performing students (placeholder implementation)"""
    from models.student import Student
    import random
    
    students = Student.query.filter_by(school_id=school_id).limit(limit).all()
    
    # Add mock performance scores
    for student in students:
        student.performance_score = random.randint(75, 98)
    
    return sorted(students, key=lambda s: s.performance_score, reverse=True)


def calculate_subscription_status(school):
    """Calculate subscription status and days remaining"""
    from datetime import date, datetime
    
    if school.subscription_end:
        # Convert subscription_end to date if it's datetime, or use today as datetime
        if isinstance(school.subscription_end, datetime):
            subscription_date = school.subscription_end.date()
        else:
            subscription_date = school.subscription_end
        
        days_remaining = (subscription_date - date.today()).days
        
        if days_remaining <= 0:
            status = 'expired'
        elif days_remaining <= 7:
            status = 'critical'
        elif days_remaining <= 30:
            status = 'warning'
        else:
            status = 'active'
        
        return {
            'days_remaining': max(0, days_remaining),
            'status': status
        }
    
    return {
        'days_remaining': 365,  # Default for new schools
        'status': 'active'
    }


def get_time_ago(dt):
    """Get human readable time ago string"""
    from datetime import datetime
    
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days}d ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours}h ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes}m ago"
    else:
        return "Just now"


# Real-time dashboard data API endpoint
@school_admin_bp.route('/dashboard/data')
@role_required('school_admin')
def dashboard_data():
    """API endpoint for real-time dashboard data updates"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    from flask import jsonify
    
    # Get updated KPIs
    kpis = calculate_dashboard_kpis(school.id)
    
    # Get new activities
    recent_activities = get_recent_activities(school.id, 5)
    
    return jsonify({
        'totalStudents': kpis['total_students'],
        'totalTeachers': kpis['total_teachers'],
        'attendancePercentage': kpis['attendance_percentage'],
        'feesCollected': kpis['fees_collected'],
        'newActivities': recent_activities,
        'timestamp': datetime.now().isoformat()
    })


# Advanced Reporting Routes

@school_admin_bp.route('/reports/student-reports')
@role_required('school_admin')
def student_reports():
    """Student reports dashboard"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    from services.advanced_report_service import AdvancedReportService
    from models.classes import Class
    
    report_service = AdvancedReportService(school.id)
    
    # Get filter parameters
    report_type = request.args.get('type', 'enrollment')
    class_filter = request.args.get('class_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Parse dates
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Generate report based on type
    report_data = {}
    if report_type == 'enrollment':
        report_data = report_service.generate_enrollment_report(start_date, end_date, class_filter)
    elif report_type == 'performance':
        report_data = report_service.generate_performance_report(class_filter)
    elif report_type == 'attendance':
        report_data = report_service.generate_attendance_report(start_date, end_date, class_filter)
    elif report_type == 'demographics':
        report_data = report_service.generate_demographics_report()
    
    # Get classes for filter
    classes = Class.query.filter_by(school_id=school.id).all()
    
    return render_template('school_admin/reports/student_reports.html',
                         user=user,
                         school=school,
                         report_type=report_type,
                         report_data=report_data,
                         classes=classes,
                         selected_class=class_filter,
                         start_date=start_date,
                         end_date=end_date)


@school_admin_bp.route('/reports/financial-reports')
@role_required('school_admin')
def financial_reports():
    """Financial reports dashboard"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    from services.advanced_report_service import AdvancedReportService
    from models.classes import Class
    
    report_service = AdvancedReportService(school.id)
    
    # Get filter parameters
    report_type = request.args.get('type', 'collection')
    class_filter = request.args.get('class_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    
    # Parse dates
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Generate report based on type
    report_data = {}
    if report_type == 'collection':
        report_data = report_service.generate_fee_collection_report(start_date, end_date, class_filter)
    elif report_type == 'outstanding':
        report_data = report_service.generate_outstanding_fees_report(class_filter)
    elif report_type == 'monthly':
        report_data = report_service.generate_monthly_revenue_report(year, month)
    elif report_type == 'yearly':
        report_data = report_service.generate_yearly_summary(year)
    
    # Get classes for filter
    classes = Class.query.filter_by(school_id=school.id).all()
    
    return render_template('school_admin/reports/financial_reports.html',
                         user=user,
                         school=school,
                         report_type=report_type,
                         report_data=report_data,
                         classes=classes,
                         selected_class=class_filter,
                         start_date=start_date,
                         end_date=end_date,
                         selected_year=year,
                         selected_month=month)


@school_admin_bp.route('/reports/academic-reports')
@role_required('school_admin')
def academic_reports():
    """Academic reports dashboard"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    from services.advanced_report_service import AdvancedReportService
    from models.classes import Class
    
    report_service = AdvancedReportService(school.id)
    
    # Get filter parameters
    report_type = request.args.get('type', 'class_wise')
    class_filter = request.args.get('class_id')
    
    # Generate report based on type
    report_data = {}
    if report_type == 'class_wise':
        report_data = report_service.generate_class_wise_report(class_filter)
    elif report_type == 'teacher_performance':
        report_data = report_service.generate_teacher_performance_report()
    
    # Get classes for filter
    classes = Class.query.filter_by(school_id=school.id).all()
    
    return render_template('school_admin/reports/academic_reports.html',
                         user=user,
                         school=school,
                         report_type=report_type,
                         report_data=report_data,
                         classes=classes,
                         selected_class=class_filter)


@school_admin_bp.route('/reports/administrative-reports')
@role_required('school_admin')
def administrative_reports():
    """Administrative reports dashboard"""
    user = User.query.get(session['user_id'])
    school = School.query.get(user.school_id)
    
    from services.advanced_report_service import AdvancedReportService
    
    report_service = AdvancedReportService(school.id)
    
    # Get filter parameters
    report_type = request.args.get('type', 'staff')
    
    # Generate report based on type
    report_data = {}
    if report_type == 'staff':
        report_data = report_service.generate_staff_report()
    elif report_type == 'infrastructure':
        report_data = {'message': 'Infrastructure report coming soon'}
    elif report_type == 'compliance':
        report_data = {'message': 'Compliance report coming soon'}
    elif report_type == 'activity_log':
        report_data = get_recent_activities(school.id, 50)
    
    return render_template('school_admin/reports/administrative_reports.html',
                         user=user,
                         school=school,
                         report_type=report_type,
                         report_data=report_data)


# Duplicate function removed - using the enhanced export_report function above