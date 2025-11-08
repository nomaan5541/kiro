"""
Fee Management Service for handling fee structures, payments, and receipts
"""
import os
import qrcode
from io import BytesIO
from datetime import datetime, date, timedelta
from decimal import Decimal
from flask import current_app
from extensions import db
from models.fee import FeeStructure, Payment, PaymentHistory, StudentFeeStatus, PaymentMode, PaymentStatus
from models.student import Student
from models.classes import Class
from models.school import School
from utils.pdf_generator import PDFGenerator
import json


class FeeService:
    """Service for managing fees, payments, and receipts"""
    
    def __init__(self, school_id):
        self.school_id = school_id
    
    def create_fee_structure(self, fee_data):
        """Create a new fee structure for a class"""
        try:
            # Check if fee structure already exists for this class and year
            existing = FeeStructure.query.filter_by(
                school_id=self.school_id,
                class_id=fee_data['class_id'],
                academic_year=fee_data['academic_year']
            ).first()
            
            if existing:
                return {'success': False, 'message': 'Fee structure already exists for this class and academic year'}
            
            # Create fee structure
            fee_structure = FeeStructure(
                school_id=self.school_id,
                class_id=fee_data['class_id'],
                academic_year=fee_data['academic_year'],
                total_fee=Decimal(str(fee_data['total_fee'])),
                tuition_fee=Decimal(str(fee_data.get('tuition_fee', 0))),
                admission_fee=Decimal(str(fee_data.get('admission_fee', 0))),
                development_fee=Decimal(str(fee_data.get('development_fee', 0))),
                transport_fee=Decimal(str(fee_data.get('transport_fee', 0))),
                library_fee=Decimal(str(fee_data.get('library_fee', 0))),
                lab_fee=Decimal(str(fee_data.get('lab_fee', 0))),
                sports_fee=Decimal(str(fee_data.get('sports_fee', 0))),
                other_fee=Decimal(str(fee_data.get('other_fee', 0))),
                installments=fee_data.get('installments', 1),
                due_dates=json.dumps(fee_data.get('due_dates', [])) if fee_data.get('due_dates') else None
            )
            
            db.session.add(fee_structure)
            db.session.flush()
            
            # Create fee status records for all students in this class
            students = Student.query.filter_by(class_id=fee_data['class_id'], status='active').all()
            for student in students:
                self._create_student_fee_status(student.id, fee_structure.id)
            
            db.session.commit()
            
            return {'success': True, 'fee_structure_id': fee_structure.id}
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': str(e)}
    
    def update_fee_structure(self, fee_structure_id, fee_data):
        """Update an existing fee structure"""
        try:
            fee_structure = FeeStructure.query.filter_by(
                id=fee_structure_id,
                school_id=self.school_id
            ).first()
            
            if not fee_structure:
                return {'success': False, 'message': 'Fee structure not found'}
            
            # Update fee structure
            fee_structure.total_fee = Decimal(str(fee_data['total_fee']))
            fee_structure.tuition_fee = Decimal(str(fee_data.get('tuition_fee', 0)))
            fee_structure.admission_fee = Decimal(str(fee_data.get('admission_fee', 0)))
            fee_structure.development_fee = Decimal(str(fee_data.get('development_fee', 0)))
            fee_structure.transport_fee = Decimal(str(fee_data.get('transport_fee', 0)))
            fee_structure.library_fee = Decimal(str(fee_data.get('library_fee', 0)))
            fee_structure.lab_fee = Decimal(str(fee_data.get('lab_fee', 0)))
            fee_structure.sports_fee = Decimal(str(fee_data.get('sports_fee', 0)))
            fee_structure.other_fee = Decimal(str(fee_data.get('other_fee', 0)))
            fee_structure.installments = fee_data.get('installments', 1)
            fee_structure.due_dates = json.dumps(fee_data.get('due_dates', [])) if fee_data.get('due_dates') else None
            
            # Update student fee statuses
            for status in fee_structure.student_statuses:
                status.total_fee = fee_structure.total_fee
                status.calculate_status()
            
            db.session.commit()
            
            return {'success': True}
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': str(e)}
    
    def record_payment(self, payment_data):
        """Record a new fee payment"""
        try:
            # Generate receipt number
            receipt_no = self._generate_receipt_number()
            
            # Create payment record
            payment = Payment(
                school_id=self.school_id,
                student_id=payment_data['student_id'],
                fee_structure_id=payment_data['fee_structure_id'],
                receipt_no=receipt_no,
                amount=Decimal(str(payment_data['amount'])),
                payment_date=datetime.strptime(payment_data['payment_date'], '%Y-%m-%d').date() if isinstance(payment_data['payment_date'], str) else payment_data['payment_date'],
                payment_mode=PaymentMode(payment_data['payment_mode']),
                status=PaymentStatus(payment_data.get('status', 'completed')),
                transaction_id=payment_data.get('transaction_id'),
                cheque_no=payment_data.get('cheque_no'),
                bank_name=payment_data.get('bank_name'),
                remarks=payment_data.get('remarks'),
                collected_by=payment_data.get('collected_by')
            )
            
            db.session.add(payment)
            db.session.flush()
            
            # Update student fee status
            self._update_student_fee_status(payment_data['student_id'], payment_data['fee_structure_id'])
            
            # Create payment history record
            history = PaymentHistory(
                payment_id=payment.id,
                action='created',
                new_status=payment.status.value,
                amount_changed=payment.amount,
                remarks=f'Payment recorded: {payment.payment_mode.value}',
                changed_by=payment_data.get('collected_by')
            )
            db.session.add(history)
            
            db.session.commit()
            
            return {'success': True, 'payment_id': payment.id, 'receipt_no': receipt_no}
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': str(e)}
    
    def generate_receipt(self, payment_id):
        """Generate a digital receipt with QR code"""
        try:
            payment = Payment.query.filter_by(
                id=payment_id,
                school_id=self.school_id
            ).first()
            
            if not payment:
                return {'success': False, 'message': 'Payment not found'}
            
            # Generate QR code for receipt verification
            qr_data = f"Receipt:{payment.receipt_no}|School:{self.school_id}|Amount:{payment.amount}|Date:{payment.payment_date}"
            qr_code = self._generate_qr_code(qr_data)
            
            # Prepare receipt data
            receipt_data = {
                'school': payment.school,
                'student': payment.student,
                'payment': payment,
                'fee_structure': payment.fee_structure,
                'qr_code': qr_code,
                'generated_at': datetime.now()
            }
            
            # Generate PDF receipt
            pdf_service = PDFGenerator()
            pdf_path = pdf_service.generate_fee_receipt(receipt_data)
            
            return {'success': True, 'pdf_path': pdf_path, 'receipt_no': payment.receipt_no}
            
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def get_fee_analytics(self, start_date=None, end_date=None):
        """Get comprehensive fee analytics with enhanced metrics"""
        try:
            if not start_date:
                start_date = date.today().replace(month=1, day=1)  # Start of current year
            if not end_date:
                end_date = date.today()
            
            # Total collections for the period
            total_collected = db.session.query(db.func.sum(Payment.amount)).filter(
                Payment.school_id == self.school_id,
                Payment.payment_date >= start_date,
                Payment.payment_date <= end_date,
                Payment.status == PaymentStatus.COMPLETED
            ).scalar() or 0
            
            # Total transactions count
            total_transactions = Payment.query.filter(
                Payment.school_id == self.school_id,
                Payment.payment_date >= start_date,
                Payment.payment_date <= end_date,
                Payment.status == PaymentStatus.COMPLETED
            ).count()
            
            # Outstanding dues (current)
            total_outstanding = db.session.query(db.func.sum(StudentFeeStatus.remaining_amount)).filter(
                StudentFeeStatus.school_id == self.school_id,
                StudentFeeStatus.remaining_amount > 0
            ).scalar() or 0
            
            # Total expected fees (current academic year)
            total_fee_expected = db.session.query(db.func.sum(StudentFeeStatus.total_fee)).filter(
                StudentFeeStatus.school_id == self.school_id
            ).scalar() or 0
            
            # Current collection rate (all time)
            current_collected = db.session.query(db.func.sum(StudentFeeStatus.paid_amount)).filter(
                StudentFeeStatus.school_id == self.school_id
            ).scalar() or 0
            
            collection_rate = (float(current_collected) / float(total_fee_expected) * 100) if total_fee_expected > 0 else 0
            
            # Average payment amount
            average_payment = (float(total_collected) / total_transactions) if total_transactions > 0 else 0
            
            # Payment mode breakdown
            payment_modes = db.session.query(
                Payment.payment_mode,
                db.func.sum(Payment.amount),
                db.func.count(Payment.id)
            ).filter(
                Payment.school_id == self.school_id,
                Payment.payment_date >= start_date,
                Payment.payment_date <= end_date,
                Payment.status == PaymentStatus.COMPLETED
            ).group_by(Payment.payment_mode).all()
            
            # Monthly collection trend
            monthly_collections = db.session.query(
                db.func.extract('month', Payment.payment_date).label('month'),
                db.func.extract('year', Payment.payment_date).label('year'),
                db.func.sum(Payment.amount).label('total')
            ).filter(
                Payment.school_id == self.school_id,
                Payment.payment_date >= start_date,
                Payment.payment_date <= end_date,
                Payment.status == PaymentStatus.COMPLETED
            ).group_by(
                db.func.extract('year', Payment.payment_date),
                db.func.extract('month', Payment.payment_date)
            ).order_by('year', 'month').all()
            
            # Class-wise collection status
            class_collections = db.session.query(
                Class.name,
                Class.section,
                db.func.sum(StudentFeeStatus.total_fee).label('total_expected'),
                db.func.sum(StudentFeeStatus.paid_amount).label('total_collected'),
                db.func.count(StudentFeeStatus.id).label('student_count')
            ).join(
                FeeStructure, StudentFeeStatus.fee_structure_id == FeeStructure.id
            ).join(
                Class, FeeStructure.class_id == Class.id
            ).filter(
                StudentFeeStatus.school_id == self.school_id
            ).group_by(Class.id, Class.name, Class.section).all()
            
            # Overdue students
            overdue_count = StudentFeeStatus.query.filter(
                StudentFeeStatus.school_id == self.school_id,
                StudentFeeStatus.is_overdue == True
            ).count()
            
            # Growth calculations (compare with previous period)
            prev_start = date(start_date.year - 1, start_date.month, start_date.day)
            prev_end = date(end_date.year - 1, end_date.month, end_date.day)
            
            prev_collected = db.session.query(db.func.sum(Payment.amount)).filter(
                Payment.school_id == self.school_id,
                Payment.payment_date >= prev_start,
                Payment.payment_date <= prev_end,
                Payment.status == PaymentStatus.COMPLETED
            ).scalar() or 0
            
            collection_growth = ((float(total_collected) - float(prev_collected)) / float(prev_collected) * 100) if prev_collected > 0 else 0
            
            return {
                'success': True,
                'analytics': {
                    'total_collected': float(total_collected),
                    'total_outstanding': float(total_outstanding),
                    'collection_rate': round(collection_rate, 2),
                    'overdue_students': overdue_count,
                    'total_transactions': total_transactions,
                    'average_payment': round(average_payment, 2),
                    'collection_growth': round(collection_growth, 2),
                    'total_expected': float(total_fee_expected),
                    'payment_modes': [
                        {
                            'mode': mode.value,
                            'amount': float(amount),
                            'count': count,
                            'percentage': round((float(amount) / float(total_collected) * 100), 2) if total_collected > 0 else 0
                        } for mode, amount, count in payment_modes
                    ],
                    'monthly_trend': [
                        {
                            'month': int(month),
                            'year': int(year),
                            'amount': float(total)
                        } for month, year, total in monthly_collections
                    ],
                    'class_wise': [
                        {
                            'class_name': f"{name} {section}" if section else name,
                            'total_expected': float(total_expected or 0),
                            'total_collected': float(total_collected or 0),
                            'student_count': student_count,
                            'collection_rate': round((float(total_collected or 0) / float(total_expected or 1)) * 100, 2)
                        } for name, section, total_expected, total_collected, student_count in class_collections
                    ]
                }
            }
            
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def get_defaulter_list(self):
        """Get list of students with overdue payments"""
        try:
            defaulters = db.session.query(
                Student.id,
                Student.name,
                Student.admission_no,
                Student.phone,
                Class.name.label('class_name'),
                Class.section,
                StudentFeeStatus.remaining_amount,
                StudentFeeStatus.next_due_date,
                StudentFeeStatus.last_payment_date
            ).join(
                StudentFeeStatus, Student.id == StudentFeeStatus.student_id
            ).join(
                FeeStructure, StudentFeeStatus.fee_structure_id == FeeStructure.id
            ).join(
                Class, FeeStructure.class_id == Class.id
            ).filter(
                StudentFeeStatus.school_id == self.school_id,
                StudentFeeStatus.is_overdue == True,
                StudentFeeStatus.remaining_amount > 0
            ).order_by(StudentFeeStatus.next_due_date.asc()).all()
            
            defaulter_list = []
            for defaulter in defaulters:
                days_overdue = (date.today() - defaulter.next_due_date).days if defaulter.next_due_date else 0
                defaulter_list.append({
                    'student_id': defaulter.id,
                    'name': defaulter.name,
                    'admission_no': defaulter.admission_no,
                    'phone': defaulter.phone,
                    'class': f"{defaulter.class_name} {defaulter.section}" if defaulter.section else defaulter.class_name,
                    'amount_due': float(defaulter.remaining_amount),
                    'due_date': defaulter.next_due_date.isoformat() if defaulter.next_due_date else None,
                    'days_overdue': days_overdue,
                    'last_payment': defaulter.last_payment_date.isoformat() if defaulter.last_payment_date else None
                })
            
            return {'success': True, 'defaulters': defaulter_list}
            
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def send_fee_reminders(self, student_ids=None):
        """Send fee reminder notifications with enhanced messaging"""
        try:
            # Get students with overdue fees
            query = StudentFeeStatus.query.filter(
                StudentFeeStatus.school_id == self.school_id,
                StudentFeeStatus.is_overdue == True,
                StudentFeeStatus.remaining_amount > 0
            )
            
            if student_ids:
                query = query.filter(StudentFeeStatus.student_id.in_(student_ids))
            
            overdue_statuses = query.all()
            
            # Send notifications (integrate with notification service)
            from services.notification_service import NotificationService
            notification_service = NotificationService(self.school_id)
            
            sent_count = 0
            failed_count = 0
            
            for status in overdue_statuses:
                try:
                    # Enhanced reminder with payment details
                    reminder_data = {
                        'student_name': status.student.name,
                        'class_name': status.student.class_info.get_display_name() if status.student.class_info else 'N/A',
                        'outstanding_amount': float(status.remaining_amount),
                        'due_date': status.next_due_date.strftime('%d/%m/%Y') if status.next_due_date else 'Overdue',
                        'days_overdue': (date.today() - status.next_due_date).days if status.next_due_date else 0,
                        'school_name': status.student.school.name,
                        'payment_link': f"https://school.edu/pay/{status.student.id}"  # Optional payment link
                    }
                    
                    # Send via multiple channels
                    notification_service.send_fee_reminder(status.student, reminder_data)
                    sent_count += 1
                    
                except Exception as e:
                    print(f"Failed to send reminder to {status.student.name}: {e}")
                    failed_count += 1
            
            return {
                'success': True, 
                'sent_count': sent_count,
                'failed_count': failed_count,
                'total_processed': len(overdue_statuses)
            }
            
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def send_payment_confirmation(self, payment_id):
        """Send payment confirmation notification"""
        try:
            payment = Payment.query.filter_by(
                id=payment_id,
                school_id=self.school_id
            ).first()
            
            if not payment:
                return {'success': False, 'message': 'Payment not found'}
            
            from services.notification_service import NotificationService
            notification_service = NotificationService(self.school_id)
            
            # Prepare confirmation data
            confirmation_data = {
                'student_name': payment.student.name,
                'receipt_no': payment.receipt_no,
                'amount': float(payment.amount),
                'payment_date': payment.payment_date.strftime('%d/%m/%Y'),
                'payment_mode': payment.payment_mode.value.title(),
                'school_name': payment.school.name,
                'balance_amount': float(payment.student.fee_status.remaining_amount) if hasattr(payment.student, 'fee_status') else 0
            }
            
            # Send confirmation
            result = notification_service.send_payment_confirmation(payment.student, confirmation_data)
            
            return result
            
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def _create_student_fee_status(self, student_id, fee_structure_id):
        """Create fee status record for a student"""
        fee_structure = FeeStructure.query.get(fee_structure_id)
        if not fee_structure:
            return
        
        # Check if status already exists
        existing = StudentFeeStatus.query.filter_by(
            student_id=student_id,
            fee_structure_id=fee_structure_id
        ).first()
        
        if existing:
            return existing
        
        # Create new status
        status = StudentFeeStatus(
            school_id=self.school_id,
            student_id=student_id,
            fee_structure_id=fee_structure_id,
            total_fee=fee_structure.total_fee,
            paid_amount=Decimal('0.00'),
            remaining_amount=fee_structure.total_fee
        )
        
        # Set next due date
        if fee_structure.due_dates:
            try:
                due_dates = json.loads(fee_structure.due_dates)
                if due_dates:
                    status.next_due_date = datetime.strptime(due_dates[0], '%Y-%m-%d').date()
            except:
                pass
        
        status.calculate_status()
        db.session.add(status)
        return status
    
    def _update_student_fee_status(self, student_id, fee_structure_id):
        """Update student fee status after payment"""
        status = StudentFeeStatus.query.filter_by(
            student_id=student_id,
            fee_structure_id=fee_structure_id
        ).first()
        
        if not status:
            status = self._create_student_fee_status(student_id, fee_structure_id)
        
        # Calculate total paid amount
        total_paid = db.session.query(db.func.sum(Payment.amount)).filter(
            Payment.student_id == student_id,
            Payment.fee_structure_id == fee_structure_id,
            Payment.status == PaymentStatus.COMPLETED
        ).scalar() or Decimal('0.00')
        
        status.paid_amount = total_paid
        status.last_payment_date = date.today()
        status.calculate_status()
        
        # Update next due date if fully paid or based on installments
        if status.is_fully_paid:
            status.next_due_date = None
        
        return status
    
    def _generate_receipt_number(self):
        """Generate unique receipt number"""
        today = date.today()
        prefix = f"RCP{self.school_id}{today.strftime('%Y%m%d')}"
        
        # Get last receipt number for today
        last_payment = Payment.query.filter(
            Payment.school_id == self.school_id,
            Payment.receipt_no.like(f"{prefix}%")
        ).order_by(Payment.receipt_no.desc()).first()
        
        if last_payment:
            try:
                last_number = int(last_payment.receipt_no[-4:])
                new_number = last_number + 1
            except:
                new_number = 1
        else:
            new_number = 1
        
        return f"{prefix}{new_number:04d}"
    
    def _generate_qr_code(self, data):
        """Generate QR code for receipt verification"""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64 for embedding in PDF
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            import base64
            qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return qr_code_base64
            
        except Exception as e:
            print(f"Error generating QR code: {e}")
            return None