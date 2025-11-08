"""
Comprehensive Notification Service for SMS, WhatsApp, Email, and In-App notifications
"""
import requests
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from flask import current_app
from extensions import db
from models.notification import (
    NotificationTemplate, NotificationLog, NotificationType, 
    NotificationChannel, DeliveryStatus
)


class NotificationService:
    """Main notification service for handling all types of notifications"""
    
    def __init__(self, school_id):
        self.school_id = school_id
        self.sms_service = SMSService()
        self.whatsapp_service = WhatsAppService()
        self.email_service = EmailService()
    
    def send_notification(self, notification_type, channel, recipient_data, variables=None, template_id=None):
        """Send notification using specified channel"""
        try:
            # Get template
            template = self._get_template(notification_type, channel, template_id)
            if not template:
                return False, "No template found for notification type"
            
            # Render message
            message = template.render_message(variables or {})
            subject = template.subject
            
            # Create notification log
            log = NotificationLog(
                school_id=self.school_id,
                template_id=template.id,
                recipient_type=recipient_data.get('type', 'unknown'),
                recipient_id=recipient_data.get('id'),
                recipient_phone=recipient_data.get('phone'),
                recipient_email=recipient_data.get('email'),
                recipient_name=recipient_data.get('name'),
                type=notification_type,
                channel=channel,
                subject=subject,
                message=message
            )
            db.session.add(log)
            db.session.flush()  # Get log ID
            
            # Send notification based on channel
            success = False
            error_message = None
            
            if channel == NotificationChannel.SMS:
                success, result = self.sms_service.send_sms(
                    recipient_data.get('phone'), message
                )
                if success:
                    log.mark_sent(result.get('message_id'))
                else:
                    error_message = result
            
            elif channel == NotificationChannel.WHATSAPP:
                success, result = self.whatsapp_service.send_message(
                    recipient_data.get('phone'), message
                )
                if success:
                    log.mark_sent(result.get('message_id'))
                else:
                    error_message = result
            
            elif channel == NotificationChannel.EMAIL:
                success, result = self.email_service.send_email(
                    recipient_data.get('email'), subject, message
                )
                if success:
                    log.mark_sent(result.get('message_id'))
                else:
                    error_message = result
            
            elif channel == NotificationChannel.IN_APP:
                # For in-app notifications, we just mark as sent
                success = True
                log.mark_sent()
            
            if not success:
                log.mark_failed(error_message or "Unknown error")
            
            db.session.commit()
            return success, log.id
            
        except Exception as e:
            db.session.rollback()
            return False, str(e)
    
    def send_bulk_notification(self, notification_type, channel, recipients_data, variables=None, template_id=None):
        """Send bulk notifications to multiple recipients"""
        results = []
        
        for recipient in recipients_data:
            # Merge global variables with recipient-specific variables
            recipient_variables = variables.copy() if variables else {}
            if 'variables' in recipient:
                recipient_variables.update(recipient['variables'])
            
            success, result = self.send_notification(
                notification_type, channel, recipient, recipient_variables, template_id
            )
            
            results.append({
                'recipient': recipient.get('name', 'Unknown'),
                'success': success,
                'result': result
            })
        
        return results
    
    def send_attendance_alert(self, student, attendance_date):
        """Send attendance alert to parents"""
        variables = {
            'student_name': student.name,
            'class_name': student.class_info.get_display_name() if student.class_info else 'N/A',
            'date': attendance_date.strftime('%d/%m/%Y'),
            'school_name': student.school.name
        }
        
        # Send SMS to parent
        if student.parent_phone:
            self.send_notification(
                NotificationType.ATTENDANCE_ALERT,
                NotificationChannel.SMS,
                {
                    'type': 'parent',
                    'id': student.id,
                    'phone': student.parent_phone,
                    'name': student.father_name or student.mother_name or 'Parent'
                },
                variables
            )
        
        # Send WhatsApp if available
        if student.parent_phone:
            self.send_notification(
                NotificationType.ATTENDANCE_ALERT,
                NotificationChannel.WHATSAPP,
                {
                    'type': 'parent',
                    'id': student.id,
                    'phone': student.parent_phone,
                    'name': student.father_name or student.mother_name or 'Parent'
                },
                variables
            )
    
    def send_fee_reminder(self, student, fee_status):
        """Send fee payment reminder"""
        variables = {
            'student_name': student.name,
            'class_name': student.class_info.get_display_name() if student.class_info else 'N/A',
            'pending_amount': f"₹{fee_status.remaining_amount:,.2f}",
            'due_date': fee_status.due_date.strftime('%d/%m/%Y') if fee_status.due_date else 'N/A',
            'school_name': student.school.name,
            'school_phone': student.school.phone or ''
        }
        
        # Send to multiple channels
        channels = [NotificationChannel.SMS, NotificationChannel.WHATSAPP]
        
        for channel in channels:
            if student.parent_phone:
                self.send_notification(
                    NotificationType.FEE_REMINDER,
                    channel,
                    {
                        'type': 'parent',
                        'id': student.id,
                        'phone': student.parent_phone,
                        'email': student.email,
                        'name': student.father_name or student.mother_name or 'Parent'
                    },
                    variables
                )
    
    def send_fee_confirmation(self, student, payment):
        """Send fee payment confirmation"""
        variables = {
            'student_name': student.name,
            'class_name': student.class_info.get_display_name() if student.class_info else 'N/A',
            'amount_paid': f"₹{payment.amount:,.2f}",
            'receipt_no': payment.receipt_no,
            'payment_date': payment.payment_date.strftime('%d/%m/%Y'),
            'school_name': student.school.name
        }
        
        # Send confirmation via SMS and Email
        if student.parent_phone:
            self.send_notification(
                NotificationType.FEE_CONFIRMATION,
                NotificationChannel.SMS,
                {
                    'type': 'parent',
                    'id': student.id,
                    'phone': student.parent_phone,
                    'name': student.father_name or student.mother_name or 'Parent'
                },
                variables
            )
        
        if student.email:
            self.send_notification(
                NotificationType.FEE_CONFIRMATION,
                NotificationChannel.EMAIL,
                {
                    'type': 'parent',
                    'id': student.id,
                    'email': student.email,
                    'name': student.father_name or student.mother_name or 'Parent'
                },
                variables
            )
    
    def send_holiday_announcement(self, recipients, holiday_data):
        """Send holiday announcement to multiple recipients"""
        variables = {
            'holiday_name': holiday_data.get('name', ''),
            'holiday_date': holiday_data.get('date', ''),
            'description': holiday_data.get('description', ''),
            'school_name': holiday_data.get('school_name', '')
        }
        
        return self.send_bulk_notification(
            NotificationType.HOLIDAY_ANNOUNCEMENT,
            NotificationChannel.SMS,
            recipients,
            variables
        )
    
    def send_general_announcement(self, recipients, announcement_data):
        """Send general announcement"""
        variables = {
            'title': announcement_data.get('title', ''),
            'message': announcement_data.get('message', ''),
            'date': announcement_data.get('date', ''),
            'school_name': announcement_data.get('school_name', '')
        }
        
        results = []
        
        # Send via multiple channels
        for channel in [NotificationChannel.SMS, NotificationChannel.EMAIL]:
            channel_results = self.send_bulk_notification(
                NotificationType.GENERAL_ANNOUNCEMENT,
                channel,
                recipients,
                variables
            )
            results.extend(channel_results)
        
        return results
    
    def _get_template(self, notification_type, channel, template_id=None):
        """Get notification template"""
        if template_id:
            return NotificationTemplate.query.filter_by(
                id=template_id,
                school_id=self.school_id
            ).first()
        
        # Get default template for type and channel
        return NotificationTemplate.query.filter_by(
            school_id=self.school_id,
            type=notification_type,
            channel=channel,
            is_active=True,
            is_default=True
        ).first()
    
    def get_delivery_statistics(self, days=30):
        """Get notification delivery statistics"""
        from datetime import datetime, timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        stats = db.session.query(
            NotificationLog.channel,
            NotificationLog.status,
            db.func.count(NotificationLog.id).label('count')
        ).filter(
            NotificationLog.school_id == self.school_id,
            NotificationLog.created_at >= start_date
        ).group_by(
            NotificationLog.channel,
            NotificationLog.status
        ).all()
        
        # Format statistics
        result = {}
        for channel in NotificationChannel:
            result[channel.value] = {
                'total': 0,
                'sent': 0,
                'delivered': 0,
                'failed': 0,
                'pending': 0
            }
        
        for stat in stats:
            channel = stat.channel.value
            status = stat.status.value
            count = stat.count
            
            result[channel]['total'] += count
            result[channel][status] += count
        
        return result


class SMSService:
    """SMS service using various SMS gateways"""
    
    def __init__(self):
        self.api_key = current_app.config.get('SMS_API_KEY')
        self.sender_id = current_app.config.get('SMS_SENDER_ID', 'SCHOOL')
        self.gateway_url = current_app.config.get('SMS_GATEWAY_URL')
    
    def send_sms(self, phone_number, message):
        """Send SMS using configured gateway"""
        if not self.api_key or not self.gateway_url:
            # Mock SMS for development
            return True, {'message_id': f'mock_sms_{datetime.now().timestamp()}'}
        
        try:
            # Format phone number
            phone = self._format_phone_number(phone_number)
            
            # Prepare SMS data
            data = {
                'apikey': self.api_key,
                'sender': self.sender_id,
                'numbers': phone,
                'message': message
            }
            
            # Send SMS
            response = requests.post(self.gateway_url, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    return True, {'message_id': result.get('message_id')}
                else:
                    return False, result.get('message', 'SMS sending failed')
            else:
                return False, f'HTTP {response.status_code}: {response.text}'
                
        except Exception as e:
            return False, str(e)
    
    def _format_phone_number(self, phone):
        """Format phone number for SMS gateway"""
        # Remove all non-digit characters
        phone = ''.join(filter(str.isdigit, phone))
        
        # Add country code if not present
        if len(phone) == 10:
            phone = '91' + phone
        
        return phone
    
    def get_delivery_status(self, message_id):
        """Get SMS delivery status"""
        if not self.api_key:
            return True, 'delivered'
        
        try:
            # This would be implemented based on your SMS gateway's API
            # For now, return mock status
            return True, 'delivered'
        except Exception as e:
            return False, str(e)


class WhatsAppService:
    """WhatsApp Business API service"""
    
    def __init__(self):
        self.api_token = current_app.config.get('WHATSAPP_API_TOKEN')
        self.phone_number_id = current_app.config.get('WHATSAPP_PHONE_NUMBER_ID')
        self.api_url = current_app.config.get('WHATSAPP_API_URL', 'https://graph.facebook.com/v17.0')
    
    def send_message(self, phone_number, message):
        """Send WhatsApp message"""
        if not self.api_token or not self.phone_number_id:
            # Mock WhatsApp for development
            return True, {'message_id': f'mock_whatsapp_{datetime.now().timestamp()}'}
        
        try:
            phone = self._format_phone_number(phone_number)
            
            url = f"{self.api_url}/{self.phone_number_id}/messages"
            
            headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'messaging_product': 'whatsapp',
                'to': phone,
                'type': 'text',
                'text': {
                    'body': message
                }
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                message_id = result.get('messages', [{}])[0].get('id')
                return True, {'message_id': message_id}
            else:
                return False, f'HTTP {response.status_code}: {response.text}'
                
        except Exception as e:
            return False, str(e)
    
    def send_template_message(self, phone_number, template_name, parameters=None):
        """Send WhatsApp template message"""
        if not self.api_token:
            return True, {'message_id': f'mock_template_{datetime.now().timestamp()}'}
        
        try:
            phone = self._format_phone_number(phone_number)
            
            url = f"{self.api_url}/{self.phone_number_id}/messages"
            
            headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'messaging_product': 'whatsapp',
                'to': phone,
                'type': 'template',
                'template': {
                    'name': template_name,
                    'language': {
                        'code': 'en'
                    }
                }
            }
            
            if parameters:
                data['template']['components'] = [{
                    'type': 'body',
                    'parameters': [{'type': 'text', 'text': param} for param in parameters]
                }]
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                message_id = result.get('messages', [{}])[0].get('id')
                return True, {'message_id': message_id}
            else:
                return False, f'HTTP {response.status_code}: {response.text}'
                
        except Exception as e:
            return False, str(e)
    
    def _format_phone_number(self, phone):
        """Format phone number for WhatsApp API"""
        phone = ''.join(filter(str.isdigit, phone))
        if len(phone) == 10:
            phone = '91' + phone
        return phone


class EmailService:
    """Email service using SMTP"""
    
    def __init__(self):
        self.smtp_server = current_app.config.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = current_app.config.get('SMTP_PORT', 587)
        self.smtp_username = current_app.config.get('SMTP_USERNAME')
        self.smtp_password = current_app.config.get('SMTP_PASSWORD')
        self.from_email = current_app.config.get('FROM_EMAIL', self.smtp_username)
        self.from_name = current_app.config.get('FROM_NAME', 'School Management System')
    
    def send_email(self, to_email, subject, message, attachments=None):
        """Send email"""
        if not self.smtp_username or not self.smtp_password:
            # Mock email for development
            return True, {'message_id': f'mock_email_{datetime.now().timestamp()}'}
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(message, 'html' if '<' in message else 'plain'))
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    self._add_attachment(msg, attachment)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            
            text = msg.as_string()
            server.sendmail(self.from_email, to_email, text)
            server.quit()
            
            return True, {'message_id': f'email_{datetime.now().timestamp()}'}
            
        except Exception as e:
            return False, str(e)
    
    def _add_attachment(self, msg, attachment):
        """Add attachment to email"""
        try:
            with open(attachment['path'], 'rb') as attachment_file:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment_file.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {attachment["name"]}'
                )
                msg.attach(part)
        except Exception as e:
            print(f"Error adding attachment: {e}")


class NotificationScheduler:
    """Service for scheduling and managing automatic notifications"""
    
    def __init__(self, school_id):
        self.school_id = school_id
        self.notification_service = NotificationService(school_id)
    
    def schedule_daily_attendance_alerts(self):
        """Send attendance alerts for absent students"""
        from models.student import Student
        from models.attendance import Attendance, AttendanceStatus
        from datetime import date
        
        today = date.today()
        
        # Get absent students for today
        absent_students = db.session.query(Student).join(Attendance).filter(
            Student.school_id == self.school_id,
            Attendance.date == today,
            Attendance.status == AttendanceStatus.ABSENT
        ).all()
        
        for student in absent_students:
            self.notification_service.send_attendance_alert(student, today)
    
    def schedule_fee_reminders(self):
        """Send fee reminders to students with pending payments"""
        from models.student import Student
        from models.fee import StudentFeeStatus
        from datetime import date, timedelta
        
        # Get students with overdue fees
        overdue_date = date.today() - timedelta(days=7)  # 7 days grace period
        
        overdue_students = db.session.query(Student).join(StudentFeeStatus).filter(
            Student.school_id == self.school_id,
            StudentFeeStatus.remaining_amount > 0,
            StudentFeeStatus.due_date <= overdue_date
        ).all()
        
        for student in overdue_students:
            fee_status = StudentFeeStatus.query.filter_by(
                student_id=student.id,
                school_id=self.school_id
            ).first()
            
            if fee_status:
                self.notification_service.send_fee_reminder(student, fee_status)
    
    def schedule_holiday_announcements(self):
        """Send holiday announcements"""
        from models.holiday import Holiday
        from models.student import Student
        from datetime import date, timedelta
        
        # Get holidays in next 3 days
        start_date = date.today()
        end_date = start_date + timedelta(days=3)
        
        upcoming_holidays = Holiday.query.filter(
            Holiday.school_id == self.school_id,
            Holiday.date >= start_date,
            Holiday.date <= end_date,
            Holiday.is_active == True
        ).all()
        
        if upcoming_holidays:
            # Get all students and parents
            students = Student.query.filter_by(school_id=self.school_id).all()
            
            recipients = []
            for student in students:
                if student.parent_phone:
                    recipients.append({
                        'type': 'parent',
                        'id': student.id,
                        'phone': student.parent_phone,
                        'email': student.email,
                        'name': student.father_name or student.mother_name or 'Parent',
                        'variables': {
                            'student_name': student.name
                        }
                    })
            
            for holiday in upcoming_holidays:
                holiday_data = {
                    'name': holiday.name,
                    'date': holiday.date.strftime('%d/%m/%Y'),
                    'description': holiday.description or '',
                    'school_name': holiday.school.name
                }
                
                self.notification_service.send_holiday_announcement(recipients, holiday_data)