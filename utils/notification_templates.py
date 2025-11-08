"""
Default Notification Templates for School Management System
"""
from models.notification import NotificationTemplate, NotificationType, NotificationChannel
from extensions import db


def create_default_templates(school_id):
    """Create default notification templates for a school"""
    
    templates = [
        # Attendance Alert Templates
        {
            'name': 'Attendance Alert - SMS',
            'type': NotificationType.ATTENDANCE_ALERT,
            'channel': NotificationChannel.SMS,
            'subject': None,
            'message_template': 'Dear Parent, {student_name} from {class_name} was absent today ({date}). Please contact school if this is an error. - {school_name}',
            'is_default': True
        },
        {
            'name': 'Attendance Alert - WhatsApp',
            'type': NotificationType.ATTENDANCE_ALERT,
            'channel': NotificationChannel.WHATSAPP,
            'subject': None,
            'message_template': 'Dear Parent,\n\nYour child {student_name} from {class_name} was marked absent today ({date}).\n\nIf this is an error, please contact the school immediately.\n\nRegards,\n{school_name}',
            'is_default': True
        },
        {
            'name': 'Attendance Alert - Email',
            'type': NotificationType.ATTENDANCE_ALERT,
            'channel': NotificationChannel.EMAIL,
            'subject': 'Attendance Alert - {student_name}',
            'message_template': '''Dear Parent,

This is to inform you that your child {student_name} from {class_name} was marked absent today ({date}).

If your child was present in school today, please contact us immediately to correct the attendance record.

If your child was indeed absent, please ensure to send a leave application for future absences.

Best regards,
{school_name}
Phone: {school_phone}''',
            'is_default': True
        },
        
        # Fee Reminder Templates
        {
            'name': 'Fee Reminder - SMS',
            'type': NotificationType.FEE_REMINDER,
            'channel': NotificationChannel.SMS,
            'subject': None,
            'message_template': 'URGENT: Fee payment of Rs.{outstanding_amount} for {student_name} ({class_name}) is overdue by {days_overdue} days. Due: {due_date}. Pay now to avoid late fees. - {school_name}',
            'is_default': True
        },
        {
            'name': 'Fee Reminder - WhatsApp',
            'type': NotificationType.FEE_REMINDER,
            'channel': NotificationChannel.WHATSAPP,
            'subject': None,
            'message_template': '''🏫 *{school_name}*

📢 *URGENT: Fee Payment Reminder*

Dear Parent,

Your ward's fee payment is overdue:

👤 *Student:* {student_name}
📚 *Class:* {class_name}
💰 *Outstanding Amount:* Rs.{outstanding_amount}
📅 *Due Date:* {due_date}
⏰ *Days Overdue:* {days_overdue} days

⚠️ *Action Required:*
Please make the payment immediately to avoid:
• Late payment charges
• Academic restrictions

💳 *Payment Options:*
• Visit school office
• Online payment available
• Call: {school_phone}

Thank you for your immediate attention!

*{school_name} Administration*''',
            'is_default': True
        },
        {
            'name': 'Fee Reminder - Email',
            'type': NotificationType.FEE_REMINDER,
            'channel': NotificationChannel.EMAIL,
            'subject': 'Fee Payment Reminder - {student_name}',
            'message_template': '''Dear Parent,

We hope this message finds you well.

This is a gentle reminder regarding the pending fee payment for your child {student_name} studying in {class_name}.

Payment Details:
- Student Name: {student_name}
- Class: {class_name}
- Amount Due: {pending_amount}
- Due Date: {due_date}

Please make the payment at your earliest convenience. You can pay online through our portal or visit the school office during working hours.

For any queries or assistance, please contact us at {school_phone}.

Thank you for your cooperation.

Best regards,
{school_name}
Accounts Department''',
            'is_default': True
        },
        
        # Fee Confirmation Templates
        {
            'name': 'Fee Confirmation - SMS',
            'type': NotificationType.FEE_CONFIRMATION,
            'channel': NotificationChannel.SMS,
            'subject': None,
            'message_template': 'Fee payment received! Amount: {amount_paid} for {student_name} ({class_name}). Receipt No: {receipt_no}. Date: {payment_date}. Thank you! - {school_name}',
            'is_default': True
        },
        {
            'name': 'Fee Confirmation - Email',
            'type': NotificationType.FEE_CONFIRMATION,
            'channel': NotificationChannel.EMAIL,
            'subject': 'Fee Payment Confirmation - Receipt #{receipt_no}',
            'message_template': '''Dear Parent,

Thank you for your payment. We have successfully received your fee payment.

Payment Details:
- Student Name: {student_name}
- Class: {class_name}
- Amount Paid: {amount_paid}
- Payment Date: {payment_date}
- Receipt Number: {receipt_no}

Please keep this receipt for your records. You can download the official receipt from our portal or collect it from the school office.

Thank you for your prompt payment.

Best regards,
{school_name}
Accounts Department''',
            'is_default': True
        },
        
        # Payment Confirmation Templates
        {
            'name': 'Payment Confirmation - SMS',
            'type': NotificationType.FEE_CONFIRMATION,
            'channel': NotificationChannel.SMS,
            'subject': None,
            'message_template': 'Payment Received! Rs.{amount} paid for {student_name} on {payment_date}. Receipt: {receipt_no}. Balance: Rs.{balance_amount}. Thank you! - {school_name}',
            'is_default': True
        },
        {
            'name': 'Payment Confirmation - WhatsApp',
            'type': NotificationType.FEE_CONFIRMATION,
            'channel': NotificationChannel.WHATSAPP,
            'subject': None,
            'message_template': '''🏫 *{school_name}*

✅ *Payment Confirmation*

Dear Parent,

Your payment has been successfully received!

👤 *Student:* {student_name}
💰 *Amount Paid:* Rs.{amount}
📅 *Payment Date:* {payment_date}
💳 *Payment Mode:* {payment_mode}
🧾 *Receipt No:* {receipt_no}
💵 *Remaining Balance:* Rs.{balance_amount}

📄 *Receipt:* Digital receipt has been generated.

Thank you for your payment!

*{school_name} Administration*''',
            'is_default': True
        },
        {
            'name': 'Payment Confirmation - Email',
            'type': NotificationType.FEE_CONFIRMATION,
            'channel': NotificationChannel.EMAIL,
            'subject': 'Payment Confirmation - {student_name} - Receipt #{receipt_no}',
            'message_template': '''Dear Parent,

We are pleased to confirm that your payment has been successfully received.

Payment Details:
- Student Name: {student_name}
- Amount Paid: Rs.{amount}
- Payment Date: {payment_date}
- Payment Mode: {payment_mode}
- Receipt Number: {receipt_no}
- Remaining Balance: Rs.{balance_amount}

Your digital receipt has been generated and is available for download.

Please keep this confirmation and the receipt for your records.

Thank you for your payment!

Best regards,
{school_name}
School Administration''',
            'is_default': True
        },

        # Holiday Announcement Templates
        {
            'name': 'Holiday Announcement - SMS',
            'type': NotificationType.HOLIDAY_ANNOUNCEMENT,
            'channel': NotificationChannel.SMS,
            'subject': None,
            'message_template': 'Holiday Notice: {holiday_name} on {holiday_date}. {description} School will remain closed. - {school_name}',
            'is_default': True
        },
        {
            'name': 'Holiday Announcement - WhatsApp',
            'type': NotificationType.HOLIDAY_ANNOUNCEMENT,
            'channel': NotificationChannel.WHATSAPP,
            'subject': None,
            'message_template': '''Dear Parents,

Holiday Announcement 📅

{holiday_name}
Date: {holiday_date}

{description}

The school will remain closed on this day. Regular classes will resume the next working day.

Regards,
{school_name}''',
            'is_default': True
        },
        
        # General Announcement Templates
        {
            'name': 'General Announcement - SMS',
            'type': NotificationType.GENERAL_ANNOUNCEMENT,
            'channel': NotificationChannel.SMS,
            'subject': None,
            'message_template': '{title}: {message} - {school_name}',
            'is_default': True
        },
        {
            'name': 'General Announcement - Email',
            'type': NotificationType.GENERAL_ANNOUNCEMENT,
            'channel': NotificationChannel.EMAIL,
            'subject': '{title}',
            'message_template': '''Dear Parents and Students,

{title}

{message}

Date: {date}

For any queries, please contact the school office.

Best regards,
{school_name}''',
            'is_default': True
        },
        
        # Exam Notification Templates
        {
            'name': 'Exam Notification - SMS',
            'type': NotificationType.EXAM_NOTIFICATION,
            'channel': NotificationChannel.SMS,
            'subject': None,
            'message_template': 'Exam Alert: {exam_name} for {class_name} on {exam_date} at {exam_time}. Venue: {venue}. Be prepared! - {school_name}',
            'is_default': True
        },
        {
            'name': 'Exam Notification - Email',
            'type': NotificationType.EXAM_NOTIFICATION,
            'channel': NotificationChannel.EMAIL,
            'subject': 'Exam Notification - {exam_name}',
            'message_template': '''Dear Students and Parents,

This is to inform you about the upcoming examination:

Exam Details:
- Exam Name: {exam_name}
- Class: {class_name}
- Date: {exam_date}
- Time: {exam_time}
- Venue: {venue}
- Duration: {duration}

Important Instructions:
- Students must report 15 minutes before the exam time
- Bring valid ID card and required stationery
- Mobile phones are strictly prohibited in the exam hall

Please ensure students are well prepared and reach on time.

Best regards,
{school_name}
Examination Department''',
            'is_default': True
        }
    ]
    
    created_count = 0
    
    for template_data in templates:
        # Check if template already exists
        existing = NotificationTemplate.query.filter_by(
            school_id=school_id,
            name=template_data['name']
        ).first()
        
        if not existing:
            template = NotificationTemplate(
                school_id=school_id,
                name=template_data['name'],
                type=template_data['type'],
                channel=template_data['channel'],
                subject=template_data['subject'],
                message_template=template_data['message_template'],
                is_active=True,
                is_default=template_data['is_default'],
                created_by=None  # System created
            )
            
            db.session.add(template)
            created_count += 1
    
    try:
        db.session.commit()
        return True, f"Created {created_count} default templates"
    except Exception as e:
        db.session.rollback()
        return False, str(e)


def get_template_variables():
    """Get list of available template variables"""
    return {
        'student': [
            'student_name', 'student_id', 'admission_no', 'roll_number',
            'class_name', 'section', 'father_name', 'mother_name'
        ],
        'school': [
            'school_name', 'school_phone', 'school_email', 'school_address'
        ],
        'dates': [
            'date', 'due_date', 'payment_date', 'exam_date', 'holiday_date'
        ],
        'fees': [
            'amount', 'pending_amount', 'amount_paid', 'receipt_no', 'total_fee'
        ],
        'exam': [
            'exam_name', 'exam_time', 'venue', 'duration', 'subject'
        ],
        'general': [
            'title', 'message', 'description', 'holiday_name'
        ]
    }


def validate_template_variables(message_template):
    """Validate that all variables in template are supported"""
    import re
    
    # Find all variables in the template
    variables = re.findall(r'\{(\w+)\}', message_template)
    
    # Get all supported variables
    all_variables = []
    for category in get_template_variables().values():
        all_variables.extend(category)
    
    # Check for unsupported variables
    unsupported = [var for var in variables if var not in all_variables]
    
    if unsupported:
        return False, f"Unsupported variables: {', '.join(unsupported)}"
    
    return True, "All variables are valid"