"""
API Blueprint - Handles REST API endpoints for mobile app integration
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from extensions import db, bcrypt
from models.user import User, UserRole
from models.student import Student
from models.teacher import Teacher
from models.attendance import Attendance, AttendanceStatus
from models.fee import Payment, StudentFeeStatus
from models.notification import NotificationLog
from models.classes import Class
from datetime import datetime, date, timedelta
from decimal import Decimal

api_bp = Blueprint('api', __name__)


# Authentication endpoints
@api_bp.route('/auth/login', methods=['POST'])
def api_login():
    """API login endpoint"""
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
    """Get current user profile"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user.to_dict())


# Student endpoints
@api_bp.route('/student/dashboard')
@jwt_required()
def student_dashboard():
    """Get student dashboard data"""
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
    """Get student attendance records"""
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
    """Get student fee information"""
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
    """Get teacher dashboard data"""
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
    """Get students in a class"""
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
    """Mark attendance via API"""
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
        
        db.session.commit()
        
        return jsonify({'message': 'Attendance marked successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Payment endpoints
@api_bp.route('/payment/create-order', methods=['POST'])
@jwt_required()
def create_payment_order():
    """Create payment order for online payment"""
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
    """Verify and process payment"""
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
    """Get user notifications"""
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
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy', 
        'message': 'School Management System API is running',
        'timestamp': datetime.utcnow().isoformat()
    })


@api_bp.route('/version')
def version_info():
    """API version information"""
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