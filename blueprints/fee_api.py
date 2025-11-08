"""Fee Management API Blueprint.

Provides API endpoints for managing all aspects of fees, including recording
payments, managing fee structures, generating receipts, sending reminders,
and retrieving analytics. All routes in this blueprint are intended for
school admins.
"""
from flask import Blueprint, request, jsonify, session, send_file
from extensions import db
from models.user import User
from models.fee import FeeStructure, Payment, StudentFeeStatus
from models.student import Student
from services.fee_service import FeeService
from utils.auth import login_required, role_required
from utils.pdf_generator import PDFGenerator
import os
from datetime import datetime

fee_api_bp = Blueprint('fee_api', __name__)


@fee_api_bp.route('/api/fees/record_payment', methods=['POST'])
@role_required('school_admin')
def record_payment():
    """Records a new fee payment for a student.

    Expects a JSON payload with student ID, amount, and payment details.
    It uses the `FeeService` to handle the business logic of recording the
    payment and updating the student's fee status.

    Returns:
        dict: A success or error message.
    """
    user = User.query.get(session['user_id'])
    
    try:
        data = request.get_json()
        
        # Get student and fee structure
        student = Student.query.filter_by(
            id=data['student_id'],
            school_id=user.school_id
        ).first()
        
        if not student:
            return jsonify({'success': False, 'message': 'Student not found'}), 404
        
        # Get active fee structure for student's class
        fee_structure = FeeStructure.query.filter_by(
            school_id=user.school_id,
            class_id=student.class_id,
            is_active=True
        ).first()
        
        if not fee_structure:
            return jsonify({'success': False, 'message': 'No active fee structure found for student class'}), 404
        
        # Prepare payment data
        payment_data = {
            'student_id': student.id,
            'fee_structure_id': fee_structure.id,
            'amount': data['amount'],
            'payment_date': data['payment_date'],
            'payment_mode': data['payment_mode'],
            'transaction_id': data.get('transaction_id'),
            'cheque_no': data.get('cheque_no'),
            'bank_name': data.get('bank_name'),
            'remarks': data.get('remarks'),
            'collected_by': user.id
        }
        
        # Record payment
        fee_service = FeeService(user.school_id)
        result = fee_service.record_payment(payment_data)
        
        # Send payment confirmation if payment was successful
        if result['success']:
            try:
                fee_service.send_payment_confirmation(result['payment_id'])
            except Exception as e:
                print(f"Failed to send payment confirmation: {e}")
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@fee_api_bp.route('/api/fees/create_structure', methods=['POST'])
@role_required('school_admin')
def create_fee_structure():
    """Creates a new fee structure.

    Expects a JSON payload with the details of the fee structure.
    Delegates the creation logic to the `FeeService`.

    Returns:
        dict: The result of the creation operation.
    """
    user = User.query.get(session['user_id'])
    
    try:
        data = request.get_json()
        data['school_id'] = user.school_id
        
        fee_service = FeeService(user.school_id)
        result = fee_service.create_fee_structure(data)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@fee_api_bp.route('/api/fees/update_structure/<int:structure_id>', methods=['POST'])
@role_required('school_admin')
def update_fee_structure(structure_id):
    """Updates an existing fee structure.

    Args:
        structure_id (int): The ID of the fee structure to update.

    Returns:
        dict: The result of the update operation.
    """
    user = User.query.get(session['user_id'])
    
    try:
        data = request.get_json()
        
        fee_service = FeeService(user.school_id)
        result = fee_service.update_fee_structure(structure_id, data)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@fee_api_bp.route('/api/fees/delete_structure', methods=['POST'])
@role_required('school_admin')
def delete_fee_structure():
    """Deletes a fee structure.

    A fee structure can only be deleted if there are no payments associated
    with it.

    Returns:
        dict: A success or error message.
    """
    user = User.query.get(session['user_id'])
    
    try:
        data = request.get_json()
        structure_id = data.get('structure_id')
        
        # Check if structure exists and belongs to school
        structure = FeeStructure.query.filter_by(
            id=structure_id,
            school_id=user.school_id
        ).first()
        
        if not structure:
            return jsonify({'success': False, 'message': 'Fee structure not found'}), 404
        
        # Check if there are any payments against this structure
        payments_count = Payment.query.filter_by(fee_structure_id=structure_id).count()
        if payments_count > 0:
            return jsonify({'success': False, 'message': 'Cannot delete fee structure with existing payments'}), 400
        
        # Delete the structure
        db.session.delete(structure)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Fee structure deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@fee_api_bp.route('/api/fees/receipt/<int:payment_id>')
@role_required('school_admin')
def view_receipt(payment_id):
    """Generates and displays a payment receipt as a PDF.

    Args:
        payment_id (int): The ID of the payment.

    Returns:
        File: The generated PDF receipt, or an error message.
    """
    user = User.query.get(session['user_id'])
    
    try:
        payment = Payment.query.filter_by(
            id=payment_id,
            school_id=user.school_id
        ).first()
        
        if not payment:
            return jsonify({'error': 'Payment not found'}), 404
        
        fee_service = FeeService(user.school_id)
        result = fee_service.generate_receipt(payment_id)
        
        if result['success']:
            return send_file(result['pdf_path'], as_attachment=False)
        else:
            return jsonify({'error': result['message']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@fee_api_bp.route('/api/fees/receipt/<int:payment_id>/download')
@role_required('school_admin')
def download_receipt(payment_id):
    """Generates and serves a payment receipt as a downloadable PDF.

    Args:
        payment_id (int): The ID of the payment.

    Returns:
        File: The generated PDF receipt as a downloadable attachment.
    """
    user = User.query.get(session['user_id'])
    
    try:
        payment = Payment.query.filter_by(
            id=payment_id,
            school_id=user.school_id
        ).first()
        
        if not payment:
            return jsonify({'error': 'Payment not found'}), 404
        
        fee_service = FeeService(user.school_id)
        result = fee_service.generate_receipt(payment_id)
        
        if result['success']:
            return send_file(result['pdf_path'], 
                           as_attachment=True, 
                           download_name=f"receipt_{result['receipt_no']}.pdf")
        else:
            return jsonify({'error': result['message']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@fee_api_bp.route('/api/fees/send_reminder', methods=['POST'])
@role_required('school_admin')
def send_fee_reminder():
    """Sends fee reminders to a specific list of students.

    Expects a JSON payload with a list of student IDs.

    Returns:
        dict: The result of the reminder sending operation.
    """
    user = User.query.get(session['user_id'])
    
    try:
        data = request.get_json()
        student_ids = data.get('student_ids', [])
        
        fee_service = FeeService(user.school_id)
        result = fee_service.send_fee_reminders(student_ids)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@fee_api_bp.route('/api/fees/send_bulk_reminders', methods=['POST'])
@role_required('school_admin')
def send_bulk_reminders():
    """Sends fee reminders to all students with overdue fees.

    Returns:
        dict: The result of the bulk reminder operation.
    """
    user = User.query.get(session['user_id'])
    
    try:
        fee_service = FeeService(user.school_id)
        result = fee_service.send_fee_reminders()  # No student_ids = all overdue students
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@fee_api_bp.route('/api/fees/analytics')
@role_required('school_admin')
def get_fee_analytics():
    """Retrieves comprehensive fee analytics for the school.

    Returns:
        dict: A dictionary containing fee analytics data.
    """
    user = User.query.get(session['user_id'])
    
    try:
        fee_service = FeeService(user.school_id)
        result = fee_service.get_fee_analytics()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@fee_api_bp.route('/api/fees/defaulters')
@role_required('school_admin')
def get_defaulters():
    """Retrieves a list of students with overdue fees.

    Returns:
        dict: A list of fee defaulters.
    """
    user = User.query.get(session['user_id'])
    
    try:
        fee_service = FeeService(user.school_id)
        result = fee_service.get_defaulter_list()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@fee_api_bp.route('/api/fees/export/payments')
@role_required('school_admin')
def export_payments():
    """Exports all payment records to a CSV file.

    Returns:
        Response: A CSV file containing payment data.
    """
    user = User.query.get(session['user_id'])
    
    try:
        # Get payments
        payments = Payment.query.filter_by(school_id=user.school_id).all()
        
        # Create CSV content
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Receipt No', 'Student Name', 'Admission No', 'Class', 
            'Amount', 'Payment Mode', 'Payment Date', 'Status', 'Transaction ID'
        ])
        
        # Write data
        for payment in payments:
            writer.writerow([
                payment.receipt_no,
                payment.student.name,
                payment.student.admission_no,
                payment.student.class_info.get_display_name() if payment.student.class_info else 'N/A',
                float(payment.amount),
                payment.payment_mode.value,
                payment.payment_date.strftime('%Y-%m-%d'),
                payment.status.value,
                payment.transaction_id or ''
            ])
        
        # Create response
        from flask import Response
        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=payments_{datetime.now().strftime("%Y%m%d")}.csv'}
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@fee_api_bp.route('/api/fees/export/outstanding')
@role_required('school_admin')
def export_outstanding():
    """Exports a list of students with outstanding fees to a CSV file.

    Returns:
        Response: A CSV file containing outstanding fee data.
    """
    user = User.query.get(session['user_id'])
    
    try:
        # Get outstanding fees
        outstanding = StudentFeeStatus.query.filter(
            StudentFeeStatus.school_id == user.school_id,
            StudentFeeStatus.remaining_amount > 0
        ).all()
        
        # Create CSV content
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Student Name', 'Admission No', 'Class', 'Total Fee', 
            'Paid Amount', 'Outstanding Amount', 'Payment %', 'Due Date', 'Status'
        ])
        
        # Write data
        for status in outstanding:
            writer.writerow([
                status.student.name,
                status.student.admission_no,
                status.student.class_info.get_display_name() if status.student.class_info else 'N/A',
                float(status.total_fee),
                float(status.paid_amount),
                float(status.remaining_amount),
                round(status.payment_percentage, 2),
                status.next_due_date.strftime('%Y-%m-%d') if status.next_due_date else '',
                'Overdue' if status.is_overdue else 'Pending'
            ])
        
        # Create response
        from flask import Response
        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=outstanding_fees_{datetime.now().strftime("%Y%m%d")}.csv'}
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@fee_api_bp.route('/api/fees/export/defaulters')
@role_required('school_admin')
def export_defaulters():
    """Exports the fee defaulters list to a CSV file.

    Returns:
        Response: A CSV file containing the fee defaulters list.
    """
    user = User.query.get(session['user_id'])
    
    try:
        fee_service = FeeService(user.school_id)
        result = fee_service.get_defaulter_list()
        
        if not result['success']:
            return jsonify({'error': result['message']}), 500
        
        defaulters = result['defaulters']
        
        # Create CSV content
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Student Name', 'Admission No', 'Class', 'Amount Due', 
            'Days Overdue', 'Due Date', 'Last Payment', 'Phone'
        ])
        
        # Write data
        for defaulter in defaulters:
            writer.writerow([
                defaulter['name'],
                defaulter['admission_no'],
                defaulter['class'],
                defaulter['amount_due'],
                defaulter['days_overdue'],
                defaulter['due_date'] or '',
                defaulter['last_payment'] or '',
                defaulter['phone'] or ''
            ])
        
        # Create response
        from flask import Response
        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=defaulters_{datetime.now().strftime("%Y%m%d")}.csv'}
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@fee_api_bp.route('/api/fees/student/<int:student_id>/status')
@role_required('school_admin')
def get_student_fee_status(student_id):
    """Retrieves the fee status and payment history for a specific student.

    Args:
        student_id (int): The ID of the student.

    Returns:
        dict: A dictionary containing the student's fee status and payments.
    """
    user = User.query.get(session['user_id'])
    
    try:
        student = Student.query.filter_by(
            id=student_id,
            school_id=user.school_id
        ).first()
        
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        # Get fee status
        fee_status = StudentFeeStatus.query.filter_by(
            student_id=student_id,
            school_id=user.school_id
        ).first()
        
        if not fee_status:
            return jsonify({'error': 'Fee status not found'}), 404
        
        # Get payment history
        payments = Payment.query.filter_by(
            student_id=student_id,
            school_id=user.school_id
        ).order_by(Payment.payment_date.desc()).all()
        
        return jsonify({
            'success': True,
            'student': {
                'id': student.id,
                'name': student.name,
                'admission_no': student.admission_no,
                'class': student.class_info.get_display_name() if student.class_info else 'N/A'
            },
            'fee_status': fee_status.to_dict(),
            'payments': [payment.to_dict() for payment in payments]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Error handlers
@fee_api_bp.errorhandler(403)
def forbidden(error):
    """Handles 403 Forbidden errors for the blueprint."""
    return jsonify({'error': 'Access denied'}), 403

@fee_api_bp.errorhandler(404)
def not_found(error):
    """Handles 404 Not Found errors for the blueprint."""
    return jsonify({'error': 'Resource not found'}), 404

@fee_api_bp.errorhandler(500)
def internal_error(error):
    """Handles 500 Internal Server errors for the blueprint."""
    return jsonify({'error': 'Internal server error'}), 500