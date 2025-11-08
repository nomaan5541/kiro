"""
Fee and Payment models for managing school fees
"""
from extensions import db
from datetime import datetime, date
from enum import Enum
from decimal import Decimal
from sqlalchemy import Numeric


class PaymentMode(Enum):
    CASH = 'cash'
    ONLINE = 'online'
    CHEQUE = 'cheque'
    BANK_TRANSFER = 'bank_transfer'


class PaymentStatus(Enum):
    PENDING = 'pending'
    COMPLETED = 'completed'
    FAILED = 'failed'
    REFUNDED = 'refunded'


class FeeStructure(db.Model):
    """Fee structure model for defining class-wise fees"""
    __tablename__ = 'fee_structures'
    
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    
    # Fee information
    academic_year = db.Column(db.String(20), nullable=False)  # e.g., "2024-25"
    total_fee = db.Column(Numeric(10, 2), nullable=False)
    
    # Fee breakdown (optional)
    tuition_fee = db.Column(Numeric(10, 2), default=0.00)
    admission_fee = db.Column(Numeric(10, 2), default=0.00)
    development_fee = db.Column(Numeric(10, 2), default=0.00)
    transport_fee = db.Column(Numeric(10, 2), default=0.00)
    library_fee = db.Column(Numeric(10, 2), default=0.00)
    lab_fee = db.Column(Numeric(10, 2), default=0.00)
    sports_fee = db.Column(Numeric(10, 2), default=0.00)
    other_fee = db.Column(Numeric(10, 2), default=0.00)
    
    # Payment schedule
    installments = db.Column(db.Integer, default=1)  # Number of installments
    due_dates = db.Column(db.Text, nullable=True)  # JSON string of due dates
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    school = db.relationship('School', backref='fee_structures', lazy=True)
    class_info = db.relationship('Class', backref='fee_structures', lazy=True)
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('school_id', 'class_id', 'academic_year', name='unique_school_class_year_fee'),
    )
    
    def __repr__(self):
        return f'<FeeStructure {self.class_info.get_display_name() if self.class_info else "Unknown"} - {self.academic_year}>'
    
    def to_dict(self):
        """Convert fee structure to dictionary"""
        return {
            'id': self.id,
            'school_id': self.school_id,
            'class_id': self.class_id,
            'academic_year': self.academic_year,
            'total_fee': float(self.total_fee),
            'tuition_fee': float(self.tuition_fee),
            'admission_fee': float(self.admission_fee),
            'development_fee': float(self.development_fee),
            'transport_fee': float(self.transport_fee),
            'library_fee': float(self.library_fee),
            'lab_fee': float(self.lab_fee),
            'sports_fee': float(self.sports_fee),
            'other_fee': float(self.other_fee),
            'installments': self.installments,
            'due_dates': self.due_dates,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Payment(db.Model):
    """Payment model for tracking fee payments"""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    fee_structure_id = db.Column(db.Integer, db.ForeignKey('fee_structures.id'), nullable=False)
    
    # Payment information
    receipt_no = db.Column(db.String(50), nullable=False, unique=True)
    amount = db.Column(Numeric(10, 2), nullable=False)
    payment_date = db.Column(db.Date, nullable=False, default=date.today)
    payment_mode = db.Column(db.Enum(PaymentMode), nullable=False)
    status = db.Column(db.Enum(PaymentStatus), default=PaymentStatus.COMPLETED)
    
    # Payment details
    transaction_id = db.Column(db.String(100), nullable=True)  # For online payments
    cheque_no = db.Column(db.String(50), nullable=True)  # For cheque payments
    bank_name = db.Column(db.String(100), nullable=True)  # For cheque/bank transfer
    remarks = db.Column(db.Text, nullable=True)
    
    # Tracking information
    collected_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    school = db.relationship('School', backref='payments', lazy=True)
    student = db.relationship('Student', backref='payments', lazy=True)
    fee_structure = db.relationship('FeeStructure', backref='payments', lazy=True)
    collector = db.relationship('User', backref='collected_payments', lazy=True)
    
    def __repr__(self):
        return f'<Payment {self.receipt_no} - {self.student.name if self.student else "Unknown"} - ₹{self.amount}>'
    
    def to_dict(self):
        """Convert payment to dictionary"""
        return {
            'id': self.id,
            'school_id': self.school_id,
            'student_id': self.student_id,
            'fee_structure_id': self.fee_structure_id,
            'receipt_no': self.receipt_no,
            'amount': float(self.amount),
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'payment_mode': self.payment_mode.value,
            'status': self.status.value,
            'transaction_id': self.transaction_id,
            'cheque_no': self.cheque_no,
            'bank_name': self.bank_name,
            'remarks': self.remarks,
            'collected_by': self.collected_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class PaymentHistory(db.Model):
    """Payment history model for tracking payment changes"""
    __tablename__ = 'payment_history'
    
    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=False)
    
    # Change information
    action = db.Column(db.String(50), nullable=False)  # 'created', 'updated', 'refunded'
    old_status = db.Column(db.String(20), nullable=True)
    new_status = db.Column(db.String(20), nullable=True)
    amount_changed = db.Column(Numeric(10, 2), nullable=True)
    remarks = db.Column(db.Text, nullable=True)
    
    # Tracking information
    changed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    payment = db.relationship('Payment', backref='history', lazy=True)
    changed_by_user = db.relationship('User', backref='payment_changes', lazy=True)
    
    def __repr__(self):
        return f'<PaymentHistory {self.payment.receipt_no if self.payment else "Unknown"} - {self.action}>'
    
    def to_dict(self):
        """Convert payment history to dictionary"""
        return {
            'id': self.id,
            'payment_id': self.payment_id,
            'action': self.action,
            'old_status': self.old_status,
            'new_status': self.new_status,
            'amount_changed': float(self.amount_changed) if self.amount_changed else None,
            'remarks': self.remarks,
            'changed_by': self.changed_by,
            'changed_at': self.changed_at.isoformat() if self.changed_at else None
        }


class StudentFeeStatus(db.Model):
    """Student fee status model for tracking overall fee payment status"""
    __tablename__ = 'student_fee_status'
    
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    fee_structure_id = db.Column(db.Integer, db.ForeignKey('fee_structures.id'), nullable=False)
    
    # Fee status
    total_fee = db.Column(Numeric(10, 2), nullable=False)
    paid_amount = db.Column(Numeric(10, 2), default=0.00)
    remaining_amount = db.Column(Numeric(10, 2), nullable=False)
    
    # Payment progress
    payment_percentage = db.Column(db.Float, default=0.0)
    is_fully_paid = db.Column(db.Boolean, default=False)
    is_overdue = db.Column(db.Boolean, default=False)
    
    # Due date tracking
    next_due_date = db.Column(db.Date, nullable=True)
    last_payment_date = db.Column(db.Date, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    school = db.relationship('School', backref='student_fee_statuses', lazy=True)
    student = db.relationship('Student', backref='fee_statuses', lazy=True)
    fee_structure = db.relationship('FeeStructure', backref='student_statuses', lazy=True)
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('student_id', 'fee_structure_id', name='unique_student_fee_structure'),
    )
    
    def __repr__(self):
        return f'<StudentFeeStatus {self.student.name if self.student else "Unknown"} - {self.payment_percentage}%>'
    
    def calculate_status(self):
        """Calculate payment status and percentage"""
        if self.total_fee > 0:
            self.payment_percentage = (float(self.paid_amount) / float(self.total_fee)) * 100
            self.remaining_amount = self.total_fee - self.paid_amount
            self.is_fully_paid = self.remaining_amount <= 0
        else:
            self.payment_percentage = 0.0
            self.remaining_amount = 0.00
            self.is_fully_paid = True
        
        # Check if overdue
        if self.next_due_date and self.next_due_date < date.today() and not self.is_fully_paid:
            self.is_overdue = True
        else:
            self.is_overdue = False
    
    def to_dict(self):
        """Convert student fee status to dictionary"""
        return {
            'id': self.id,
            'school_id': self.school_id,
            'student_id': self.student_id,
            'fee_structure_id': self.fee_structure_id,
            'total_fee': float(self.total_fee),
            'paid_amount': float(self.paid_amount),
            'remaining_amount': float(self.remaining_amount),
            'payment_percentage': self.payment_percentage,
            'is_fully_paid': self.is_fully_paid,
            'is_overdue': self.is_overdue,
            'next_due_date': self.next_due_date.isoformat() if self.next_due_date else None,
            'last_payment_date': self.last_payment_date.isoformat() if self.last_payment_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }