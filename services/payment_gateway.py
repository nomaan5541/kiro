"""
Payment Gateway Service for handling online payments
"""
try:
    import razorpay
except ImportError:
    razorpay = None

try:
    import stripe
except ImportError:
    stripe = None

import json
import hashlib
import hmac
from decimal import Decimal
from datetime import datetime
from flask import current_app
from extensions import db


class RazorpayService:
    """Razorpay payment gateway service"""
    
    def __init__(self):
        self.client = None
        self.key_id = current_app.config.get('RAZORPAY_KEY_ID', 'rzp_test_dummy')
        self.key_secret = current_app.config.get('RAZORPAY_KEY_SECRET', 'dummy_secret')
        
        if razorpay and self.key_id and self.key_secret:
            try:
                self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
            except Exception as e:
                print(f"Razorpay initialization error: {e}")
    
    def create_order(self, amount, currency='INR', receipt=None, notes=None):
        """Create Razorpay order"""
        if not self.client:
            # Return mock order for development
            return {
                'id': f"order_mock_{int(datetime.now().timestamp())}",
                'amount': int(amount * 100),
                'currency': currency,
                'receipt': receipt or f"receipt_{int(datetime.now().timestamp())}",
                'status': 'created'
            }
        
        order_data = {
            'amount': int(amount * 100),  # Amount in paise
            'currency': currency,
            'receipt': receipt or f"order_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'notes': notes or {}
        }
        
        try:
            order = self.client.order.create(data=order_data)
            return order
        except Exception as e:
            raise Exception(f"Failed to create Razorpay order: {str(e)}")
    
    def verify_payment_signature(self, payment_data):
        """Verify Razorpay payment signature"""
        if not self.client:
            # Mock verification for development
            return True
        
        try:
            razorpay_order_id = payment_data.get('razorpay_order_id')
            razorpay_payment_id = payment_data.get('razorpay_payment_id')
            razorpay_signature = payment_data.get('razorpay_signature')
            
            # Create signature
            message = f"{razorpay_order_id}|{razorpay_payment_id}"
            expected_signature = hmac.new(
                self.key_secret.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, razorpay_signature)
        except Exception as e:
            print(f"Razorpay signature verification error: {e}")
            return False
    
    def get_payment_details(self, payment_id):
        """Get payment details from Razorpay"""
        if not self.client:
            # Return mock payment details
            return {
                'id': payment_id,
                'amount': 100000,  # 1000 INR in paise
                'currency': 'INR',
                'status': 'captured',
                'method': 'card'
            }
        
        try:
            payment = self.client.payment.fetch(payment_id)
            return payment
        except Exception as e:
            raise Exception(f"Failed to get payment details: {str(e)}")


class StripeService:
    """Stripe payment gateway service"""
    
    def __init__(self):
        self.secret_key = current_app.config.get('STRIPE_SECRET_KEY', 'sk_test_dummy')
        self.publishable_key = current_app.config.get('STRIPE_PUBLISHABLE_KEY', 'pk_test_dummy')
        
        if stripe and self.secret_key:
            stripe.api_key = self.secret_key
    
    def create_payment_intent(self, amount, currency='inr', metadata=None):
        """Create Stripe payment intent"""
        if not stripe:
            # Return mock payment intent
            return {
                'id': f"pi_mock_{int(datetime.now().timestamp())}",
                'client_secret': f"pi_mock_{int(datetime.now().timestamp())}_secret_dummy",
                'amount': int(amount * 100),
                'currency': currency,
                'status': 'requires_payment_method'
            }
        
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Amount in smallest currency unit
                currency=currency,
                metadata=metadata or {},
                automatic_payment_methods={'enabled': True}
            )
            return intent
        except Exception as e:
            raise Exception(f"Failed to create Stripe payment intent: {str(e)}")
    
    def confirm_payment_intent(self, payment_intent_id):
        """Confirm Stripe payment intent"""
        if not stripe:
            # Return mock confirmation
            return {
                'id': payment_intent_id,
                'status': 'succeeded',
                'amount': 100000,
                'currency': 'inr'
            }
        
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return intent
        except Exception as e:
            raise Exception(f"Failed to confirm payment intent: {str(e)}")


class PaymentGatewayService:
    """Service for handling payment gateway operations"""
    
    def __init__(self):
        self.razorpay_client = None
        self.stripe_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize payment gateway clients"""
        # Initialize Razorpay
        razorpay_key_id = current_app.config.get('RAZORPAY_KEY_ID')
        razorpay_key_secret = current_app.config.get('RAZORPAY_KEY_SECRET')
        
        if razorpay_key_id and razorpay_key_secret:
            self.razorpay_client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))
        
        # Initialize Stripe
        stripe_secret_key = current_app.config.get('STRIPE_SECRET_KEY')
        if stripe_secret_key:
            stripe.api_key = stripe_secret_key
            self.stripe_client = stripe
    
    def create_razorpay_order(self, amount, currency='INR', receipt=None, notes=None):
        """Create Razorpay order"""
        if not self.razorpay_client:
            raise Exception("Razorpay not configured")
        
        order_data = {
            'amount': int(amount * 100),  # Amount in paise
            'currency': currency,
            'receipt': receipt or f"order_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'notes': notes or {}
        }
        
        try:
            order = self.razorpay_client.order.create(data=order_data)
            return True, order
        except Exception as e:
            return False, str(e)
    
    def verify_razorpay_payment(self, razorpay_order_id, razorpay_payment_id, razorpay_signature):
        """Verify Razorpay payment signature"""
        if not self.razorpay_client:
            raise Exception("Razorpay not configured")
        
        try:
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            
            self.razorpay_client.utility.verify_payment_signature(params_dict)
            return True, "Payment verified successfully"
        except Exception as e:
            return False, str(e)
    
    def get_razorpay_payment_details(self, payment_id):
        """Get Razorpay payment details"""
        if not self.razorpay_client:
            raise Exception("Razorpay not configured")
        
        try:
            payment = self.razorpay_client.payment.fetch(payment_id)
            return True, payment
        except Exception as e:
            return False, str(e)
    
    def create_stripe_payment_intent(self, amount, currency='inr', metadata=None):
        """Create Stripe payment intent"""
        if not self.stripe_client:
            raise Exception("Stripe not configured")
        
        try:
            intent = self.stripe_client.PaymentIntent.create(
                amount=int(amount * 100),  # Amount in smallest currency unit
                currency=currency,
                metadata=metadata or {},
                automatic_payment_methods={'enabled': True}
            )
            return True, intent
        except Exception as e:
            return False, str(e)
    
    def confirm_stripe_payment(self, payment_intent_id):
        """Confirm Stripe payment"""
        if not self.stripe_client:
            raise Exception("Stripe not configured")
        
        try:
            intent = self.stripe_client.PaymentIntent.retrieve(payment_intent_id)
            return True, intent
        except Exception as e:
            return False, str(e)
    
    def process_fee_payment(self, student_id, amount, payment_method='razorpay', 
                          gateway_payment_id=None, gateway_order_id=None, 
                          gateway_signature=None, metadata=None):
        """Process fee payment through gateway"""
        
        try:
            # Get student and fee structure
            student = Student.query.get(student_id)
            if not student:
                return False, "Student not found"
            
            from models.fee import FeeStructure, StudentFeeStatus
            fee_structure = FeeStructure.query.filter_by(
                school_id=student.school_id,
                class_id=student.class_id,
                is_active=True
            ).first()
            
            if not fee_structure:
                return False, "No active fee structure found"
            
            # Verify payment based on method
            if payment_method == 'razorpay':
                if not all([gateway_payment_id, gateway_order_id, gateway_signature]):
                    return False, "Missing Razorpay payment details"
                
                verified, message = self.verify_razorpay_payment(
                    gateway_order_id, gateway_payment_id, gateway_signature
                )
                
                if not verified:
                    return False, f"Payment verification failed: {message}"
                
                # Get payment details
                success, payment_details = self.get_razorpay_payment_details(gateway_payment_id)
                if not success:
                    return False, f"Failed to get payment details: {payment_details}"
                
            elif payment_method == 'stripe':
                if not gateway_payment_id:
                    return False, "Missing Stripe payment intent ID"
                
                success, payment_details = self.confirm_stripe_payment(gateway_payment_id)
                if not success:
                    return False, f"Payment confirmation failed: {payment_details}"
                
                if payment_details.status != 'succeeded':
                    return False, f"Payment not successful: {payment_details.status}"
            
            else:
                return False, "Unsupported payment method"
            
            # Create payment record
            from utils.helpers import generate_receipt_number
            payment = Payment(
                school_id=student.school_id,
                student_id=student_id,
                fee_structure_id=fee_structure.id,
                receipt_no=generate_receipt_number(student.school_id),
                amount=Decimal(str(amount)),
                payment_date=datetime.now().date(),
                payment_mode=PaymentMode.ONLINE,
                status=PaymentStatus.COMPLETED,
                transaction_id=gateway_payment_id,
                remarks=f"Online payment via {payment_method.title()}"
            )
            db.session.add(payment)
            
            # Update student fee status
            fee_status = StudentFeeStatus.query.filter_by(
                student_id=student_id,
                fee_structure_id=fee_structure.id
            ).first()
            
            if fee_status:
                fee_status.paid_amount += Decimal(str(amount))
                fee_status.last_payment_date = datetime.now().date()
                fee_status.calculate_status()
            else:
                # Create new fee status
                fee_status = StudentFeeStatus(
                    school_id=student.school_id,
                    student_id=student_id,
                    fee_structure_id=fee_structure.id,
                    total_fee=fee_structure.total_fee,
                    paid_amount=Decimal(str(amount)),
                    remaining_amount=fee_structure.total_fee - Decimal(str(amount)),
                    last_payment_date=datetime.now().date()
                )
                fee_status.calculate_status()
                db.session.add(fee_status)
            
            db.session.commit()
            
            # Send payment confirmation
            try:
                from utils.notification_service import NotificationService
                notification_service = NotificationService(student.school_id)
                notification_service.send_payment_confirmation(student, payment)
            except Exception as e:
                print(f"Notification error: {e}")
            
            return True, {
                'payment_id': payment.id,
                'receipt_no': payment.receipt_no,
                'amount': float(payment.amount),
                'student_name': student.name,
                'remaining_amount': float(fee_status.remaining_amount)
            }
            
        except Exception as e:
            db.session.rollback()
            return False, str(e)
    
    def get_payment_history(self, student_id, limit=10):
        """Get payment history for a student"""
        payments = Payment.query.filter_by(
            student_id=student_id,
            status=PaymentStatus.COMPLETED
        ).order_by(Payment.payment_date.desc()).limit(limit).all()
        
        return [payment.to_dict() for payment in payments]
    
    def generate_payment_receipt(self, payment_id):
        """Generate payment receipt PDF"""
        payment = Payment.query.get(payment_id)
        if not payment:
            return None
        
        # Use PDF generator service
        from utils.pdf_generator import PDFGenerator
        pdf_generator = PDFGenerator()
        
        receipt_data = {
            'payment': payment,
            'student': payment.student,
            'school': payment.school,
            'fee_structure': payment.fee_structure
        }
        
        return pdf_generator.generate_payment_receipt(receipt_data)
    
    def refund_payment(self, payment_id, amount=None, reason=None):
        """Process payment refund"""
        payment = Payment.query.get(payment_id)
        if not payment:
            return False, "Payment not found"
        
        if payment.status != PaymentStatus.COMPLETED:
            return False, "Payment is not in completed status"
        
        refund_amount = amount or payment.amount
        
        try:
            # Process refund based on original payment method
            if payment.payment_mode == PaymentMode.ONLINE:
                if 'rzp_' in payment.transaction_id:  # Razorpay payment
                    if not self.razorpay_client:
                        return False, "Razorpay not configured"
                    
                    refund = self.razorpay_client.payment.refund(
                        payment.transaction_id,
                        {
                            'amount': int(refund_amount * 100),
                            'notes': {'reason': reason or 'Refund requested'}
                        }
                    )
                    
                elif 'pi_' in payment.transaction_id:  # Stripe payment
                    if not self.stripe_client:
                        return False, "Stripe not configured"
                    
                    refund = self.stripe_client.Refund.create(
                        payment_intent=payment.transaction_id,
                        amount=int(refund_amount * 100),
                        reason='requested_by_customer'
                    )
                
                # Update payment status
                payment.status = PaymentStatus.REFUNDED
                payment.remarks = f"{payment.remarks or ''} | Refunded: ₹{refund_amount} - {reason or 'No reason provided'}"
                
                # Update student fee status
                from models.fee import StudentFeeStatus
                fee_status = StudentFeeStatus.query.filter_by(
                    student_id=payment.student_id,
                    fee_structure_id=payment.fee_structure_id
                ).first()
                
                if fee_status:
                    fee_status.paid_amount -= Decimal(str(refund_amount))
                    fee_status.calculate_status()
                
                db.session.commit()
                
                return True, f"Refund of ₹{refund_amount} processed successfully"
            
            else:
                return False, "Refund not supported for this payment method"
                
        except Exception as e:
            db.session.rollback()
            return False, str(e)