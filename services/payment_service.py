"""
Payment Service - Handles payment processing and fee management
"""
from extensions import db
from models.fee import Payment, PaymentHistory, StudentFeeStatus, FeeStructure, PaymentMode, PaymentStatus
from models.student import Student
from models.activity import ActivityLog, ActivityType
from utils.helpers import generate_receipt_number
from decimal import Decimal
from datetime import datetime, date
import json


class PaymentService:
    """Service class for handling payments and fee management"""
    
    @staticmethod
    def record_payment(student_id, amount, payment_mode, collected_by_id, 
                      remarks=None, transaction_id=None, cheque_no=None, bank_name=None):
        """Record a new payment for a student"""
        try:
            # Get student and fee structure
            student = Student.query.get(student_id)
            if not student:
                return False, "Student not found"
            
            fee_structure = FeeStructure.query.filter_by(
                school_id=student.school_id,
                class_id=student.class_id,
                is_active=True
            ).first()
            
            if not fee_structure:
                return False, "No active fee structure found for this student"
            
            # Create payment record
            payment = Payment(
                school_id=student.school_id,
                student_id=student_id,
                fee_structure_id=fee_structure.id,
                receipt_no=generate_receipt_number(student.school_id),
                amount=Decimal(str(amount)),
                payment_date=date.today(),
                payment_mode=PaymentMode(payment_mode),
                status=PaymentStatus.COMPLETED,
                transaction_id=transaction_id,
                cheque_no=cheque_no,
                bank_name=bank_name,
                remarks=remarks,
                collected_by=collected_by_id
            )
            
            db.session.add(payment)
            db.session.flush()  # Get payment ID
            
            # Update or create student fee status
            fee_status = StudentFeeStatus.query.filter_by(
                student_id=student_id,
                fee_structure_id=fee_structure.id
            ).first()
            
            if fee_status:
                fee_status.paid_amount += payment.amount
                fee_status.last_payment_date = date.today()
            else:
                fee_status = StudentFeeStatus(
                    school_id=student.school_id,
                    student_id=student_id,
                    fee_structure_id=fee_structure.id,
                    total_fee=fee_structure.total_fee,
                    paid_amount=payment.amount,
                    remaining_amount=fee_structure.total_fee - payment.amount,
                    last_payment_date=date.today()
                )
                db.session.add(fee_status)
            
            # Recalculate fee status
            fee_status.calculate_status()
            
            # Create payment history record
            payment_history = PaymentHistory(
                payment_id=payment.id,
                action='created',
                new_status=payment.status.value,
                amount_changed=payment.amount,
                remarks=f"Payment recorded by user {collected_by_id}",
                changed_by=collected_by_id
            )
            db.session.add(payment_history)
            
            # Log activity
            ActivityLog.log_activity(
                ActivityType.PAYMENT_RECEIVED,
                f"Payment of ₹{amount} received for {student.name} (Receipt: {payment.receipt_no})",
                school_id=student.school_id,
                user_id=collected_by_id,
                entity_type='payment',
                entity_id=payment.id,
                extra_data=json.dumps({
                    'student_id': student_id,
                    'amount': str(amount),
                    'payment_mode': payment_mode,
                    'receipt_no': payment.receipt_no
                })
            )
            
            db.session.commit()
            
            return True, {
                'payment_id': payment.id,
                'receipt_no': payment.receipt_no,
                'amount': float(payment.amount),
                'remaining_balance': float(fee_status.remaining_amount)
            }
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error recording payment: {str(e)}"
    
    @staticmethod
    def get_student_fee_status(student_id):
        """Get comprehensive fee status for a student"""
        try:
            student = Student.query.get(student_id)
            if not student:
                return None, "Student not found"
            
            fee_structure = FeeStructure.query.filter_by(
                school_id=student.school_id,
                class_id=student.class_id,
                is_active=True
            ).first()
            
            if not fee_structure:
                return None, "No fee structure found"
            
            fee_status = StudentFeeStatus.query.filter_by(
                student_id=student_id,
                fee_structure_id=fee_structure.id
            ).first()
            
            if not fee_status:
                # Create default fee status
                fee_status = StudentFeeStatus(
                    school_id=student.school_id,
                    student_id=student_id,
                    fee_structure_id=fee_structure.id,
                    total_fee=fee_structure.total_fee,
                    paid_amount=Decimal('0.00'),
                    remaining_amount=fee_structure.total_fee,
                    payment_percentage=0.0
                )
                db.session.add(fee_status)
                db.session.commit()
            
            # Get payment history
            payments = Payment.query.filter_by(
                student_id=student_id,
                fee_structure_id=fee_structure.id
            ).order_by(Payment.payment_date.desc()).all()
            
            return {
                'fee_structure': fee_structure,
                'fee_status': fee_status,
                'payments': payments,
                'student': student
            }, None
            
        except Exception as e:
            return None, f"Error getting fee status: {str(e)}"
    
    @staticmethod
    def get_payment_summary(school_id, start_date=None, end_date=None):
        """Get payment summary for a school"""
        try:
            query = Payment.query.filter_by(school_id=school_id)
            
            if start_date:
                query = query.filter(Payment.payment_date >= start_date)
            if end_date:
                query = query.filter(Payment.payment_date <= end_date)
            
            payments = query.all()
            
            total_collected = sum(payment.amount for payment in payments)
            total_transactions = len(payments)
            
            # Payment mode breakdown
            mode_breakdown = {}
            for payment in payments:
                mode = payment.payment_mode.value
                mode_breakdown[mode] = mode_breakdown.get(mode, 0) + float(payment.amount)
            
            # Monthly breakdown
            monthly_breakdown = {}
            for payment in payments:
                month_key = payment.payment_date.strftime('%Y-%m')
                monthly_breakdown[month_key] = monthly_breakdown.get(month_key, 0) + float(payment.amount)
            
            return {
                'total_collected': float(total_collected),
                'total_transactions': total_transactions,
                'mode_breakdown': mode_breakdown,
                'monthly_breakdown': monthly_breakdown,
                'average_payment': float(total_collected / total_transactions) if total_transactions > 0 else 0
            }, None
            
        except Exception as e:
            return None, f"Error getting payment summary: {str(e)}"
    
    @staticmethod
    def get_overdue_payments(school_id):
        """Get list of overdue payments"""
        try:
            overdue_statuses = StudentFeeStatus.query.filter_by(
                school_id=school_id,
                is_overdue=True
            ).all()
            
            overdue_list = []
            for status in overdue_statuses:
                overdue_list.append({
                    'student': status.student,
                    'fee_status': status,
                    'days_overdue': (date.today() - status.next_due_date).days if status.next_due_date else 0
                })
            
            return overdue_list, None
            
        except Exception as e:
            return None, f"Error getting overdue payments: {str(e)}"
    
    @staticmethod
    def refund_payment(payment_id, refund_amount, refunded_by_id, reason=None):
        """Process a payment refund"""
        try:
            payment = Payment.query.get(payment_id)
            if not payment:
                return False, "Payment not found"
            
            if payment.status == PaymentStatus.REFUNDED:
                return False, "Payment already refunded"
            
            refund_amount = Decimal(str(refund_amount))
            if refund_amount > payment.amount:
                return False, "Refund amount cannot exceed payment amount"
            
            # Update payment status
            old_status = payment.status.value
            payment.status = PaymentStatus.REFUNDED
            
            # Update student fee status
            fee_status = StudentFeeStatus.query.filter_by(
                student_id=payment.student_id,
                fee_structure_id=payment.fee_structure_id
            ).first()
            
            if fee_status:
                fee_status.paid_amount -= refund_amount
                fee_status.calculate_status()
            
            # Create payment history record
            payment_history = PaymentHistory(
                payment_id=payment.id,
                action='refunded',
                old_status=old_status,
                new_status=payment.status.value,
                amount_changed=-refund_amount,
                remarks=reason or f"Refund processed by user {refunded_by_id}",
                changed_by=refunded_by_id
            )
            db.session.add(payment_history)
            
            # Log activity
            ActivityLog.log_activity(
                ActivityType.PAYMENT_REFUNDED,
                f"Payment refund of ₹{refund_amount} processed for {payment.student.name} (Receipt: {payment.receipt_no})",
                school_id=payment.school_id,
                user_id=refunded_by_id,
                entity_type='payment',
                entity_id=payment.id,
                extra_data=json.dumps({
                    'refund_amount': str(refund_amount),
                    'reason': reason,
                    'original_amount': str(payment.amount)
                })
            )
            
            db.session.commit()
            
            return True, {
                'payment_id': payment.id,
                'refund_amount': float(refund_amount),
                'new_status': payment.status.value
            }
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error processing refund: {str(e)}"
    
    @staticmethod
    def generate_receipt_data(payment_id):
        """Generate receipt data for printing"""
        try:
            payment = Payment.query.get(payment_id)
            if not payment:
                return None, "Payment not found"
            
            receipt_data = {
                'payment': payment,
                'student': payment.student,
                'school': payment.school,
                'fee_structure': payment.fee_structure,
                'generated_at': datetime.now(),
                'qr_code_data': f"RECEIPT:{payment.receipt_no}:AMOUNT:{payment.amount}:DATE:{payment.payment_date}"
            }
            
            return receipt_data, None
            
        except Exception as e:
            return None, f"Error generating receipt: {str(e)}"