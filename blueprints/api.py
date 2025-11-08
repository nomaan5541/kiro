"""API Blueprint for the School Management System.

This blueprint handles all the RESTful API endpoints, primarily intended for
integration with a mobile application or other external services. It covers
authentication, student and teacher data, attendance, fees, and notifications.
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from extensions import db, bcrypt
from models.user import User, UserRole
from models.student import Student
from models.teacher import Teacher
from models.attendance import Attendance, AttendanceStatus
from models.fee import Payment, StudentFeeStatus
from utils.notification_service import NotificationService
from models.notification import NotificationLog
from models.classes import Class
from datetime import datetime, date, timedelta
from decimal import Decimal

api_bp = Blueprint('api', __name__)


# Authentication endpoints
@api_bp.route('/auth/login', methods=['POST'])
def api_login():
    """API login endpoint for all user roles.

    Authenticates a user based on email and password and returns a JWT
    access token along with user and profile information.

    Args:
        email (str): The user's email address.
        password (str): The user's password.

    Returns:
        dict: A dictionary containing the access token, user data, and
              role-specific profile data.
    """
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if user and bcrypt.check_password_hash(user.password_hash, data['password']):
        access_token = create_access_token(identity=user.id)
        
        # Get additional profile data based on role
        profile_data = {}
        if user.role == UserRole.STUDENT:
            student = Student.query.filter_by(school_id=user.school_id).first()
            if student:
                profile_data = student.to_dict()
        elif user.role == UserRole.TEACHER:
            teacher = Teacher.query.filter_by(user_id=user.id).first()
            if teacher:
                profile_data = teacher.to_dict()
        
        return jsonify({
            'access_token': access_token,
            'user': user.to_dict(),
            'profile': profile_data
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401


@api_bp.route('/user/profile')
@jwt_required()
def get_user_profile():
    """Get the profile of the currently authenticated user.

    Requires a valid JWT token.

    Returns:
        dict: A dictionary containing the user's profile information.
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user.to_dict())


# Student endpoints
@api_bp.route('/student/dashboard')
@jwt_required()
def student_dashboard():
    """Get dashboard data for a student.

    Provides a summary of the student's attendance, fee status, and recent
    payments. Requires a valid student JWT token.

    Returns:
        dict: A dictionary containing the student's dashboard data.
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or user.role != UserRole.STUDENT:
        return jsonify({'error': 'Access denied'}), 403
    
    # Find student record
    student = Student.query.filter_by(school_id=user.school_id).first()
    if not student:
        return jsonify({'error': 'Student profile not found'}), 404
    
    # Get attendance summary (last 30 days)
    thirty_days_ago = date.today() - timedelta(days=30)
    attendance_records = Attendance.query.filter(
        Attendance.student_id == student.id,
        Attendance.date >= thirty_days_ago
    ).all()
    
    attendance_summary = {
        'total_days': len(attendance_records),
        'present_days': len([a for a in attendance_records if a.status == AttendanceStatus.PRESENT]),
        'absent_days': len([a for a in attendance_records if a.status == AttendanceStatus.ABSENT]),
        'leave_days': len([a for a in attendance_records if a.status == AttendanceStatus.LEAVE])
    }
    
    if attendance_summary['total_days'] > 0:
        attendance_summary['percentage'] = (attendance_summary['present_days'] / attendance_summary['total_days']) * 100
    else:
        attendance_summary['percentage'] = 0
    
    # Get fee status
    fee_status = StudentFeeStatus.query.filter_by(student_id=student.id).first()
    fee_summary = {}
    if fee_status:
        fee_summary = {
            'total_fee': float(fee_status.total_fee),
            'paid_amount': float(fee_status.paid_amount),
            'remaining_amount': float(fee_status.remaining_amount),
            'payment_percentage': fee_status.payment_percentage,
            'is_overdue': fee_status.is_overdue
        }
    
    # Get recent payments
    recent_payments = Payment.query.filter_by(
        student_id=student.id
    ).order_by(Payment.payment_date.desc()).limit(5).all()
    
    return jsonify({
        'student': student.to_dict(),
        'attendance_summary': attendance_summary,
        'fee_summary': fee_summary,
        'recent_payments': [payment.to_dict() for payment in recent_payments]
    })


@api_bp.route('/student/attendance')
@jwt_required()
def student_attendance():
    """Get attendance records for a student.

    Allows filtering by start and end dates. Requires a valid student
    JWT token.

    Args:
        start_date (str, optional): The start date in 'YYYY-MM-DD' format.
        end_date (str, optional): The end date in 'YYYY-MM-DD' format.

    Returns:
        dict: A dictionary containing a list of attendance records.
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or user.role != UserRole.STUDENT:
        return jsonify({'error': 'Access denied'}), 403
    
    student = Student.query.filter_by(school_id=user.school_id).first()
    if not student:
        return jsonify({'error': 'Student profile not found'}), 404
    
    # Get query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Attendance.query.filter_by(student_id=student.id)
    
    if start_date:
        query = query.filter(Attendance.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(Attendance.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    
    attendance_records = query.order_by(Attendance.date.desc()).all()
    
    return jsonify({
        'attendance_records': [record.to_dict() for record in attendance_records]
    })


@api_bp.route('/student/fees')
@jwt_required()
def student_fees():
    """Get fee information for a student.

    Provides the student's fee status and a complete payment history.
    Requires a valid student JWT token.

    Returns:
        dict: A dictionary containing the fee status and payment history.
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or user.role != UserRole.STUDENT:
        return jsonify({'error': 'Access denied'}), 403
    
    student = Student.query.filter_by(school_id=user.school_id).first()
    if not student:
        return jsonify({'error': 'Student profile not found'}), 404
    
    # Get fee status
    fee_status = StudentFeeStatus.query.filter_by(student_id=student.id).first()
    
    # Get payment history
    payments = Payment.query.filter_by(
        student_id=student.id
    ).order_by(Payment.payment_date.desc()).all()
    
    return jsonify({
        'fee_status': fee_status.to_dict() if fee_status else None,
        'payment_history': [payment.to_dict() for payment in payments]
    })


# Teacher endpoints
@api_bp.route('/teacher/dashboard')
@jwt_required()
def teacher_dashboard():
    """Get dashboard data for a teacher.

    Provides a list of assigned classes and the attendance status for today.
    Requires a valid teacher JWT token.

    Returns:
        dict: A dictionary containing the teacher's dashboard data.
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or user.role != UserRole.TEACHER:
        return jsonify({'error': 'Access denied'}), 403
    
    teacher = Teacher.query.filter_by(user_id=user.id).first()
    if not teacher:
        return jsonify({'error': 'Teacher profile not found'}), 404
    
    # Get assigned classes
    assigned_classes = teacher.get_assigned_classes()
    
    # Get today's attendance status
    today = date.today()
    attendance_status = []
    
    for class_info in assigned_classes:
        total_students = len(class_info.students)
        marked_attendance = Attendance.query.filter_by(
            class_id=class_info.id,
            date=today
        ).count()
        
        attendance_status.append({
            'class': class_info.to_dict(),
            'total_students': total_students,
            'marked_attendance': marked_attendance,
            'completion_percentage': (marked_attendance / total_students * 100) if total_students > 0 else 0
        })
    
    return jsonify({
        'teacher': teacher.to_dict(),
        'assigned_classes': [cls.to_dict() for cls in assigned_classes],
        'attendance_status': attendance_status
    })


@api_bp.route('/teacher/classes/<int:class_id>/students')
@jwt_required()
def get_class_students(class_id):
    """Get a list of students in a specific class.

    Verifies that the teacher is assigned to the requested class.
    Requires a valid teacher JWT token.

    Args:
        class_id (int): The ID of the class.

    Returns:
        dict: A dictionary containing the class information and a list of
              students.
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or user.role != UserRole.TEACHER:
        return jsonify({'error': 'Access denied'}), 403
    
    teacher = Teacher.query.filter_by(user_id=user.id).first()
    if not teacher:
        return jsonify({'error': 'Teacher profile not found'}), 404
    
    # Verify teacher has access to this class
    from models.teacher import TeacherClassAssignment
    assignment = TeacherClassAssignment.query.filter_by(
        teacher_id=teacher.id,
        class_id=class_id,
        is_active=True
    ).first()
    
    if not assignment:
        return jsonify({'error': 'Access denied to this class'}), 403
    
    students = Student.query.filter_by(class_id=class_id).all()
    
    return jsonify({
        'class': assignment.class_info.to_dict(),
        'students': [student.to_dict() for student in students]
    })


@api_bp.route('/teacher/attendance', methods=['POST'])
@jwt_required()
def mark_attendance_api():
    """Mark attendance for a class.

    Allows a teacher to submit attendance records for multiple students at
    once. Verifies that the teacher is assigned to the class. Requires a
    valid teacher JWT token.

    Args:
        class_id (int): The ID of the class.
        date (str): The date of attendance in 'YYYY-MM-DD' format.
        attendance_records (list): A list of dictionaries, each containing
                                   'student_id' and 'status'.

    Returns:
        dict: A success message or an error.
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or user.role != UserRole.TEACHER:
        return jsonify({'error': 'Access denied'}), 403
    
    teacher = Teacher.query.filter_by(user_id=user.id).first()
    if not teacher:
        return jsonify({'error': 'Teacher profile not found'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    class_id = data.get('class_id')
    attendance_date = data.get('date')
    attendance_records = data.get('attendance_records', [])
    
    if not all([class_id, attendance_date, attendance_records]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Verify teacher has access to this class
    from models.teacher import TeacherClassAssignment
    assignment = TeacherClassAssignment.query.filter_by(
        teacher_id=teacher.id,
        class_id=class_id,
        is_active=True
    ).first()
    
    if not assignment:
        return jsonify({'error': 'Access denied to this class'}), 403
    
    try:
        attendance_date = datetime.strptime(attendance_date, '%Y-%m-%d').date()
        
        # Process attendance records
        notification_service = NotificationService(teacher.school_id)
        for record in attendance_records:
            student_id = record.get('student_id')
            status = record.get('status')
            
            if not student_id or not status:
                continue
            
            # Check if attendance already exists
            existing = Attendance.query.filter_by(
                student_id=student_id,
                date=attendance_date
            ).first()
            
            if existing:
                existing.status = AttendanceStatus(status)
                existing.marked_by = user.id
                existing.marked_at = datetime.utcnow()
            else:
                attendance = Attendance(
                    school_id=teacher.school_id,
                    student_id=student_id,
                    class_id=class_id,
                    date=attendance_date,
                    status=AttendanceStatus(status),
                    marked_by=user.id
                )
                db.session.add(attendance)

            # Send notification if student is absent or on leave
            if status in ['absent', 'leave']:
                student = Student.query.get(student_id)
                if student:
                    notification_service.send_attendance_alert(student, status, attendance_date)
        
        db.session.commit()
        
        return jsonify({'message': 'Attendance marked successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Payment endpoints
@api_bp.route('/payment/create-order', methods=['POST'])
@jwt_required()
def create_payment_order():
    """Create a payment order for online fee payment.

    Interfaces with a payment gateway service (e.g., Razorpay, Stripe) to
    create a payment order. Requires a valid JWT token.

    Args:
        student_id (int): The ID of the student making the payment.
        amount (float): The amount to be paid.
        payment_method (str, optional): The payment gateway to use.
                                        Defaults to 'razorpay'.

    Returns:
        dict: The payment order details from the gateway.
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    student_id = data.get('student_id')
    amount = data.get('amount')
    payment_method = data.get('payment_method', 'razorpay')
    
    if not all([student_id, amount]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        from services.payment_gateway import PaymentGatewayService
        gateway_service = PaymentGatewayService()
        
        if payment_method == 'razorpay':
            success, order = gateway_service.create_razorpay_order(
                amount=float(amount),
                receipt=f"fee_payment_{student_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            )
        elif payment_method == 'stripe':
            success, order = gateway_service.create_stripe_payment_intent(
                amount=float(amount),
                metadata={'student_id': student_id, 'user_id': user.id}
            )
        else:
            return jsonify({'error': 'Unsupported payment method'}), 400
        
        if success:
            return jsonify({
                'success': True,
                'order': order,
                'payment_method': payment_method
            })
        else:
            return jsonify({'error': order}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/payment/verify', methods=['POST'])
@jwt_required()
def verify_payment():
    """Verify and process a fee payment.

    Verifies the payment with the payment gateway and, if successful,
    updates the student's fee status. Requires a valid JWT token.

    Args:
        student_id (int): The ID of the student.
        amount (float): The payment amount.
        payment_method (str): The payment gateway used.
        payment_id (str): The payment ID from the gateway.
        order_id (str): The order ID from the gateway.
        signature (str, optional): The payment signature for verification
                                   (e.g., from Razorpay).

    Returns:
        dict: The payment details upon successful verification.
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        from services.payment_gateway import PaymentGatewayService
        gateway_service = PaymentGatewayService()
        
        success, result = gateway_service.process_fee_payment(
            student_id=data.get('student_id'),
            amount=data.get('amount'),
            payment_method=data.get('payment_method'),
            gateway_payment_id=data.get('payment_id'),
            gateway_order_id=data.get('order_id'),
            gateway_signature=data.get('signature')
        )
        
        if success:
            return jsonify({
                'success': True,
                'payment_details': result
            })
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Notification endpoints
@api_bp.route('/notifications')
@jwt_required()
def get_notifications():
    """Get notifications for the authenticated user.

    Retrieves notifications based on the user's role and school.
    Requires a valid JWT token.

    Returns:
        dict: A dictionary containing a list of notifications.
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get notifications based on user role
    if user.role == UserRole.STUDENT:
        student = Student.query.filter_by(school_id=user.school_id).first()
        if student:
            notifications = Notification.query.filter_by(
                student_id=student.id
            ).order_by(Notification.created_at.desc()).limit(50).all()
        else:
            notifications = []
    else:
        # For teachers and admins, get school-level notifications
        notifications = Notification.query.filter_by(
            school_id=user.school_id,
            student_id=None  # General notifications
        ).order_by(Notification.created_at.desc()).limit(50).all()
    
    return jsonify({
        'notifications': [notification.to_dict() for notification in notifications]
    })


# General endpoints
@api_bp.route('/health')
def health_check():
    """Health check endpoint.

    Provides a simple health check to verify that the API is running.

    Returns:
        dict: A dictionary with the API status and timestamp.
    """
    return jsonify({
        'status': 'healthy', 
        'message': 'School Management System API is running',
        'timestamp': datetime.utcnow().isoformat()
    })


@api_bp.route('/version')
def version_info():
    """API version information.

    Returns the current version and a list of features of the API.

    Returns:
        dict: A dictionary containing the API version and features.
    """
    return jsonify({
        'version': '1.0.0',
        'api_name': 'School Management System API',
        'features': [
            'Authentication',
            'Student Dashboard',
            'Teacher Dashboard',
            'Attendance Management',
            'Fee Management',
            'Payment Gateway',
            'Notifications'
        ]
    })