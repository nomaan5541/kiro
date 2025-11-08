"""
Student Blueprint - Handles student/parent functionality
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from extensions import db
from models.user import User
from models.student import Student
from models.attendance import Attendance, AttendanceStatus
from models.fee import Payment, StudentFeeStatus, FeeStructure
from models.assignment import Assignment, AssignmentSubmission, AssignmentStatus, SubmissionStatus
from models.notification import NotificationLog
from models.classes import Class
from utils.auth import login_required, role_required
from datetime import datetime, date, timedelta
from decimal import Decimal
import os

student_bp = Blueprint('student', __name__)


@student_bp.route('/dashboard')
@role_required('student')
def dashboard():
    """Student/Parent dashboard"""
    user = User.query.get(session['user_id'])
    
    # Find student record - for demo, we'll use the first student
    student = Student.query.filter_by(school_id=user.school_id).first()
    
    if not student:
        flash('Student profile not found. Please contact administrator.', 'error')
        return redirect(url_for('auth.logout'))
    
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
        attendance_summary['percentage'] = round(
            (attendance_summary['present_days'] / attendance_summary['total_days']) * 100, 2
        )
    else:
        attendance_summary['percentage'] = 0
    
    # Get fee status
    fee_status = StudentFeeStatus.query.filter_by(student_id=student.id).first()
    
    # Get recent payments (last 5)
    recent_payments = Payment.query.filter_by(
        student_id=student.id
    ).order_by(Payment.payment_date.desc()).limit(5).all()
    
    # Get recent assignments
    recent_assignments = []
    if student.class_id:
        recent_assignments = Assignment.query.filter_by(
            class_id=student.class_id,
            status=AssignmentStatus.PUBLISHED
        ).order_by(Assignment.created_at.desc()).limit(5).all()
    
    # Get recent notifications
    recent_notifications = Notification.query.filter_by(
        student_id=student.id
    ).order_by(Notification.created_at.desc()).limit(5).all()
    
    return render_template('student/dashboard.html',
                         user=user,
                         student=student,
                         attendance_summary=attendance_summary,
                         fee_status=fee_status,
                         recent_payments=recent_payments,
                         recent_assignments=recent_assignments,
                         recent_notifications=recent_notifications,
                         today=date.today())


@student_bp.route('/profile')
@role_required('student')
def profile():
    """Student profile page"""
    user = User.query.get(session['user_id'])
    student = Student.query.filter_by(school_id=user.school_id).first()
    
    if not student:
        flash('Student profile not found. Please contact administrator.', 'error')
        return redirect(url_for('auth.logout'))
    
    return render_template('student/profile.html', user=user, student=student)


@student_bp.route('/attendance')
@role_required('student')
def attendance():
    """Student attendance page"""
    user = User.query.get(session['user_id'])
    student = Student.query.filter_by(school_id=user.school_id).first()
    
    if not student:
        flash('Student profile not found. Please contact administrator.', 'error')
        return redirect(url_for('auth.logout'))
    
    # Get query parameters
    month = request.args.get('month', type=int) or date.today().month
    year = request.args.get('year', type=int) or date.today().year
    
    # Get attendance records for the month
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    attendance_records = Attendance.query.filter(
        Attendance.student_id == student.id,
        Attendance.date >= start_date,
        Attendance.date <= end_date
    ).order_by(Attendance.date.desc()).all()
    
    # Calculate monthly statistics
    total_days = len(attendance_records)
    present_days = len([a for a in attendance_records if a.status == AttendanceStatus.PRESENT])
    absent_days = len([a for a in attendance_records if a.status == AttendanceStatus.ABSENT])
    leave_days = len([a for a in attendance_records if a.status == AttendanceStatus.LEAVE])
    
    monthly_stats = {
        'total_days': total_days,
        'present_days': present_days,
        'absent_days': absent_days,
        'leave_days': leave_days,
        'percentage': round((present_days / total_days * 100), 2) if total_days > 0 else 0
    }
    
    # Create calendar data
    calendar_data = {}
    for record in attendance_records:
        calendar_data[record.date.day] = {
            'status': record.status.value,
            'remarks': record.remarks
        }
    
    return render_template('student/attendance.html',
                         user=user,
                         student=student,
                         attendance_records=attendance_records,
                         monthly_stats=monthly_stats,
                         calendar_data=calendar_data,
                         current_month=month,
                         current_year=year)


@student_bp.route('/fees')
@role_required('student')
def fees():
    """Student fees page"""
    user = User.query.get(session['user_id'])
    student = Student.query.filter_by(school_id=user.school_id).first()
    
    if not student:
        flash('Student profile not found. Please contact administrator.', 'error')
        return redirect(url_for('auth.logout'))
    
    # Get fee status
    fee_status = StudentFeeStatus.query.filter_by(student_id=student.id).first()
    
    # Get fee structure
    fee_structure = None
    if student.class_id:
        fee_structure = FeeStructure.query.filter_by(
            school_id=student.school_id,
            class_id=student.class_id,
            is_active=True
        ).first()
    
    # Get payment history
    payments = Payment.query.filter_by(
        student_id=student.id
    ).order_by(Payment.payment_date.desc()).all()
    
    # Calculate payment statistics
    total_paid = sum(payment.amount for payment in payments)
    payment_count = len(payments)
    
    return render_template('student/fees.html',
                         user=user,
                         student=student,
                         fee_status=fee_status,
                         fee_structure=fee_structure,
                         payments=payments,
                         total_paid=total_paid,
                         payment_count=payment_count)


@student_bp.route('/assignments')
@role_required('student')
def assignments():
    """Student assignments page"""
    user = User.query.get(session['user_id'])
    student = Student.query.filter_by(school_id=user.school_id).first_or_404()
    
    from services.assignment_service import AssignmentService
    
    assignment_service = AssignmentService(student.school_id)
    
    # Get assignments for student's class
    assignments = assignment_service.get_student_assignments(student.id, student.class_id)
    
    # Calculate assignment statistics
    assignment_stats = {
        'total': len(assignments),
        'pending': len([a for a in assignments if not a.submission or a.submission.status == SubmissionStatus.NOT_SUBMITTED]),
        'submitted': len([a for a in assignments if a.submission and a.submission.status in [SubmissionStatus.SUBMITTED, SubmissionStatus.LATE_SUBMITTED, SubmissionStatus.GRADED]]),
        'overdue': len([a for a in assignments if a.is_overdue() and (not a.submission or a.submission.status == SubmissionStatus.NOT_SUBMITTED)])
    }
    
    return render_template('student/assignments.html',
                         user=user,
                         student=student,
                         assignments=assignments,
                         assignment_stats=assignment_stats)


@student_bp.route('/assignments/<int:assignment_id>')
@role_required('student')
def view_assignment(assignment_id):
    """View assignment details"""
    user = User.query.get(session['user_id'])
    student = Student.query.filter_by(school_id=user.school_id).first_or_404()
    
    assignment = Assignment.query.filter_by(
        id=assignment_id,
        class_id=student.class_id,
        school_id=student.school_id,
        status=AssignmentStatus.PUBLISHED
    ).first_or_404()
    
    # Get student's submission
    submission = AssignmentSubmission.query.filter_by(
        assignment_id=assignment_id,
        student_id=student.id
    ).first()
    
    return render_template('student/view_assignment.html',
                         user=user,
                         student=student,
                         assignment=assignment,
                         submission=submission)


@student_bp.route('/assignments/submit', methods=['POST'])
@role_required('student')
def submit_assignment():
    """Submit assignment"""
    user = User.query.get(session['user_id'])
    student = Student.query.filter_by(school_id=user.school_id).first_or_404()
    
    from services.assignment_service import AssignmentService
    
    try:
        assignment_service = AssignmentService(student.school_id)
        
        assignment_id = int(request.form.get('assignment_id'))
        submission_text = request.form.get('submission_text')
        files = request.files.getlist('files')
        
        # Verify student has access to this assignment
        assignment = Assignment.query.filter_by(
            id=assignment_id,
            class_id=student.class_id,
            school_id=student.school_id,
            status=AssignmentStatus.PUBLISHED
        ).first()
        
        if not assignment:
            return jsonify({'success': False, 'message': 'Assignment not found or access denied.'})
        
        # Submit assignment
        result = assignment_service.submit_assignment(assignment_id, student.id, submission_text, files)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@student_bp.route('/study_materials')
@role_required('student')
def study_materials():
    """Student study materials page"""
    user = User.query.get(session['user_id'])
    student = Student.query.filter_by(school_id=user.school_id).first_or_404()
    
    from services.assignment_service import AssignmentService
    
    assignment_service = AssignmentService(student.school_id)
    
    # Get study materials for student's class
    materials = assignment_service.get_study_materials(class_id=student.class_id)
    
    # Also get public materials
    public_materials = assignment_service.get_study_materials()
    public_materials = [m for m in public_materials if m.is_public and m not in materials]
    
    return render_template('student/study_materials.html',
                         user=user,
                         student=student,
                         materials=materials,
                         public_materials=public_materials)


@student_bp.route('/download_file/<file_type>/<int:file_id>')
@role_required('student')
def download_file(file_type, file_id):
    """Download assignment or study material file"""
    user = User.query.get(session['user_id'])
    student = Student.query.filter_by(school_id=user.school_id).first_or_404()
    
    try:
        if file_type == 'assignment':
            from models.assignment import AssignmentAttachment
            attachment = AssignmentAttachment.query.get_or_404(file_id)
            
            # Verify student has access to this assignment
            if attachment.assignment.class_id != student.class_id or attachment.assignment.school_id != student.school_id:
                flash('Access denied.', 'error')
                return redirect(url_for('student.assignments'))
            
        elif file_type == 'study_material':
            from models.assignment import StudyMaterialAttachment
            attachment = StudyMaterialAttachment.query.get_or_404(file_id)
            
            # Verify student has access to this study material
            material = attachment.study_material
            if not material.is_public and material.class_id != student.class_id:
                flash('Access denied.', 'error')
                return redirect(url_for('student.study_materials'))
            
            if not material.is_downloadable:
                flash('This file is not available for download.', 'error')
                return redirect(url_for('student.study_materials'))
        
        else:
            flash('Invalid file type.', 'error')
            return redirect(url_for('student.dashboard'))
        
        # Send file
        return send_file(
            attachment.file_path,
            as_attachment=True,
            download_name=attachment.original_filename
        )
        
    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'error')
        return redirect(url_for('student.dashboard'))


@student_bp.route('/notifications')
@role_required('student')
def notifications():
    """Student notifications page"""
    user = User.query.get(session['user_id'])
    student = Student.query.filter_by(school_id=user.school_id).first()
    
    if not student:
        flash('Student profile not found. Please contact administrator.', 'error')
        return redirect(url_for('auth.logout'))
    
    # Get notifications with pagination
    page = request.args.get('page', 1, type=int)
    notifications = Notification.query.filter_by(
        student_id=student.id
    ).order_by(Notification.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('student/notifications.html',
                         user=user,
                         student=student,
                         notifications=notifications)


@student_bp.route('/reports')
@role_required('student')
def reports():
    """Student reports page"""
    user = User.query.get(session['user_id'])
    student = Student.query.filter_by(school_id=user.school_id).first()
    
    if not student:
        flash('Student profile not found. Please contact administrator.', 'error')
        return redirect(url_for('auth.logout'))
    
    # Generate attendance report for current academic year
    current_year = date.today().year
    academic_start = date(current_year, 4, 1) if date.today().month >= 4 else date(current_year - 1, 4, 1)
    academic_end = date(current_year + 1, 3, 31) if date.today().month >= 4 else date(current_year, 3, 31)
    
    attendance_records = Attendance.query.filter(
        Attendance.student_id == student.id,
        Attendance.date >= academic_start,
        Attendance.date <= academic_end
    ).all()
    
    # Monthly breakdown
    monthly_breakdown = {}
    for record in attendance_records:
        month_key = f"{record.date.year}-{record.date.month:02d}"
        if month_key not in monthly_breakdown:
            monthly_breakdown[month_key] = {'present': 0, 'absent': 0, 'leave': 0, 'total': 0}
        
        monthly_breakdown[month_key]['total'] += 1
        if record.status == AttendanceStatus.PRESENT:
            monthly_breakdown[month_key]['present'] += 1
        elif record.status == AttendanceStatus.ABSENT:
            monthly_breakdown[month_key]['absent'] += 1
        elif record.status == AttendanceStatus.LEAVE:
            monthly_breakdown[month_key]['leave'] += 1
    
    # Calculate percentages
    for month_data in monthly_breakdown.values():
        if month_data['total'] > 0:
            month_data['percentage'] = round((month_data['present'] / month_data['total']) * 100, 2)
        else:
            month_data['percentage'] = 0
    
    return render_template('student/reports.html',
                         user=user,
                         student=student,
                         monthly_breakdown=monthly_breakdown,
                         academic_year=f"{academic_start.year}-{academic_end.year}",
                         today=date.today())


@student_bp.route('/pay_fees')
@role_required('student')
def pay_fees():
    """Online fee payment page"""
    user = User.query.get(session['user_id'])
    student = Student.query.filter_by(school_id=user.school_id).first()
    
    if not student:
        flash('Student profile not found. Please contact administrator.', 'error')
        return redirect(url_for('auth.logout'))
    
    # Get fee status
    fee_status = StudentFeeStatus.query.filter_by(student_id=student.id).first()
    
    if not fee_status or fee_status.is_fully_paid:
        flash('No pending fees found.', 'info')
        return redirect(url_for('student.fees'))
    
    # Get fee structure for installment options
    fee_structure = FeeStructure.query.filter_by(
        school_id=student.school_id,
        class_id=student.class_id,
        is_active=True
    ).first()
    
    # Calculate installment amounts
    installment_options = []
    if fee_structure and fee_structure.installments > 1:
        remaining_amount = fee_status.remaining_amount
        installment_amount = remaining_amount / fee_structure.installments
        
        for i in range(1, min(fee_structure.installments + 1, 5)):  # Max 4 installment options
            installment_options.append({
                'installments': i,
                'amount_per_installment': round(installment_amount * i, 2),
                'total_amount': round(installment_amount * i, 2)
            })
    
    return render_template('student/pay_fees.html',
                         user=user,
                         student=student,
                         fee_status=fee_status,
                         fee_structure=fee_structure,
                         installment_options=installment_options)


@student_bp.route('/api/create_payment_order', methods=['POST'])
@role_required('student')
def create_payment_order():
    """Create payment order for online payment"""
    user = User.query.get(session['user_id'])
    student = Student.query.filter_by(school_id=user.school_id).first()
    
    if not student:
        return jsonify({'error': 'Student profile not found'}), 404
    
    data = request.get_json()
    amount = data.get('amount')
    payment_method = data.get('payment_method', 'razorpay')
    
    if not amount or float(amount) <= 0:
        return jsonify({'error': 'Invalid amount'}), 400
    
    try:
        from services.payment_gateway import PaymentGatewayService
        gateway_service = PaymentGatewayService()
        
        if payment_method == 'razorpay':
            success, order = gateway_service.create_razorpay_order(
                amount=float(amount),
                receipt=f"fee_payment_{student.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                notes={
                    'student_id': student.id,
                    'student_name': student.name,
                    'school_id': student.school_id
                }
            )
        else:
            return jsonify({'error': 'Unsupported payment method'}), 400
        
        if success:
            return jsonify({
                'success': True,
                'order': order,
                'student_info': {
                    'name': student.name,
                    'class': student.class_info.get_display_name() if student.class_info else 'N/A',
                    'admission_no': student.admission_no
                }
            })
        else:
            return jsonify({'error': order}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@student_bp.route('/api/verify_payment', methods=['POST'])
@role_required('student')
def verify_payment():
    """Verify and process payment"""
    user = User.query.get(session['user_id'])
    student = Student.query.filter_by(school_id=user.school_id).first()
    
    if not student:
        return jsonify({'error': 'Student profile not found'}), 404
    
    data = request.get_json()
    
    try:
        from services.payment_gateway import PaymentGatewayService
        gateway_service = PaymentGatewayService()
        
        success, result = gateway_service.process_fee_payment(
            student_id=student.id,
            amount=data.get('amount'),
            payment_method=data.get('payment_method', 'razorpay'),
            gateway_payment_id=data.get('payment_id'),
            gateway_order_id=data.get('order_id'),
            gateway_signature=data.get('signature')
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Payment processed successfully!',
                'payment_details': result
            })
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500