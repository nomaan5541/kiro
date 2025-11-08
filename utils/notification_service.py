"""
Notification service for sending SMS and WhatsApp messages
"""
import requests
import json
from datetime import datetime
from models.notification import NotificationLog, NotificationTemplate, NotificationType, NotificationChannel, DeliveryStatus
from models.activity import ActivityLog, ActivityType
from extensions import db


class NotificationService:
    """Service class for handling notifications"""
    
    def __init__(self, school_id):
        self.school_id = school_id
        self.settings = self._get_notification_settings()
    
    def _get_notification_settings(self):
        """Get notification settings for the school"""
        from models.system_settings import SystemSettings
        return NotificationSettings.query.filter_by(school_id=self.school_id).first()
    
    def send_sms(self, phone, message, notification_type, student_id=None, entity_type=None, entity_id=None):
        """Send SMS notification"""
        if not self.settings or not self.settings.sms_enabled:
            return False, "SMS notifications are disabled"
        
        # Create notification record
        notification = Notification(
            school_id=self.school_id,
            student_id=student_id,
            notification_type=notification_type,
            method=NotificationMethod.SMS,
            recipient_phone=phone,
            recipient_name="Student Parent",  # Will be updated with actual name
            message=message,
            entity_type=entity_type,
            entity_id=entity_id
        )
        
        try:
            # Send SMS based on provider
            if self.settings.sms_provider == 'fast2sms':
                success, response = self._send_fast2sms(phone, message)
            else:
                success, response = False, "Unsupported SMS provider"
            
            if success:
                notification.mark_sent(provider_response=response)
                # Log activity
                ActivityLog.log_activity(
                    ActivityType.SYSTEM_ERROR if not success else ActivityType.USER_LOGIN,
                    f"SMS sent to {phone}",
                    school_id=self.school_id,
                    entity_type='notification',
                    entity_id=notification.id
                )
            else:
                notification.mark_failed(response)
            
            db.session.add(notification)
            db.session.commit()
            
            return success, response
            
        except Exception as e:
            notification.mark_failed(str(e))
            db.session.add(notification)
            db.session.commit()
            return False, str(e)
    
    def _send_fast2sms(self, phone, message):
        """Send SMS using Fast2SMS API"""
        if not self.settings.sms_api_key:
            return False, "SMS API key not configured"
        
        url = "https://www.fast2sms.com/dev/bulkV2"
        
        payload = {
            "authorization": self.settings.sms_api_key,
            "sender_id": self.settings.sms_sender_id or "SCHOOL",
            "message": message,
            "language": "english",
            "route": "q",
            "numbers": phone
        }
        
        headers = {
            'authorization': self.settings.sms_api_key,
            'Content-Type': "application/x-www-form-urlencoded",
            'Cache-Control': "no-cache",
        }
        
        try:
            response = requests.post(url, data=payload, headers=headers, timeout=30)
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('return'):
                return True, json.dumps(response_data)
            else:
                return False, json.dumps(response_data)
                
        except Exception as e:
            return False, f"API Error: {str(e)}"
    
    def send_whatsapp(self, phone, message, notification_type, student_id=None, entity_type=None, entity_id=None):
        """Send WhatsApp notification"""
        if not self.settings or not self.settings.whatsapp_enabled:
            return False, "WhatsApp notifications are disabled"
        
        # Create notification record
        notification = Notification(
            school_id=self.school_id,
            student_id=student_id,
            notification_type=notification_type,
            method=NotificationMethod.WHATSAPP,
            recipient_phone=phone,
            recipient_name="Student Parent",
            message=message,
            entity_type=entity_type,
            entity_id=entity_id
        )
        
        try:
            # Send WhatsApp based on provider
            if self.settings.whatsapp_provider == 'twilio':
                success, response = self._send_twilio_whatsapp(phone, message)
            else:
                success, response = False, "Unsupported WhatsApp provider"
            
            if success:
                notification.mark_sent(provider_response=response)
            else:
                notification.mark_failed(response)
            
            db.session.add(notification)
            db.session.commit()
            
            return success, response
            
        except Exception as e:
            notification.mark_failed(str(e))
            db.session.add(notification)
            db.session.commit()
            return False, str(e)
    
    def _send_twilio_whatsapp(self, phone, message):
        """Send WhatsApp using Twilio API"""
        # Placeholder for Twilio WhatsApp implementation
        return False, "Twilio WhatsApp integration not implemented yet"
    
    def send_attendance_alert(self, student, attendance_status, date_obj=None):
        """Send attendance alert notification"""
        if not self.settings or not self.settings.auto_attendance_alerts:
            return False, "Attendance alerts are disabled"
        
        # Only send alerts for absent and leave status
        if attendance_status not in ['absent', 'leave']:
            return False, "No alert needed for present status"
        
        # Get template or create default message
        template = self._get_template(NotificationType.ATTENDANCE_ALERT, NotificationMethod.SMS)
        if template:
            message = template.render_message(
                student_name=student.name,
                status=attendance_status.upper(),
                date=(date_obj or datetime.now()).strftime('%d/%m/%Y'),
                school_name=student.school.name
            )
        else:
            message = f"Dear Parent, {student.name} was marked {attendance_status.upper()} today ({(date_obj or datetime.now()).strftime('%d/%m/%Y')}). - {student.school.name}"
        
        # Send SMS if enabled
        sms_success = False
        if self.settings.sms_enabled:
            sms_success, _ = self.send_sms(
                student.phone, 
                message, 
                notification_type=NotificationType.ATTENDANCE_ALERT,
                student_id=student.id,
                entity_type='attendance'
            )
        
        # Send WhatsApp if enabled
        whatsapp_success = False
        if self.settings.whatsapp_enabled:
            whatsapp_success, _ = self.send_whatsapp(
                student.phone, 
                message, 
                notification_type=NotificationType.ATTENDANCE_ALERT,
                student_id=student.id,
                entity_type='attendance'
            )
        
        return sms_success or whatsapp_success, "Notification sent successfully"
    
    def send_payment_confirmation(self, student, payment):
        """Send payment confirmation notification"""
        if not self.settings or not self.settings.auto_payment_confirmations:
            return False, "Payment confirmations are disabled"
        
        # Create message
        message = f"Dear Parent, Payment of ₹{payment.amount} received for {student.name} (Receipt: {payment.receipt_no}). Thank you! - {student.school.name}"
        
        # Send notifications
        sms_success = False
        if self.settings.sms_enabled:
            sms_success, _ = self.send_sms(
                student.phone, 
                message, 
                notification_type=NotificationType.PAYMENT_CONFIRMATION,
                student_id=student.id,
                entity_type='payment',
                entity_id=payment.id
            )
        
        whatsapp_success = False
        if self.settings.whatsapp_enabled:
            whatsapp_success, _ = self.send_whatsapp(
                student.phone, 
                message, 
                notification_type=NotificationType.PAYMENT_CONFIRMATION,
                student_id=student.id,
                entity_type='payment',
                entity_id=payment.id
            )
        
        return sms_success or whatsapp_success, "Payment confirmation sent"
    
    def _get_template(self, notification_type, method):
        """Get notification template"""
        # Template already imported at top
        return NotificationTemplate.query.filter_by(
            school_id=self.school_id,
            notification_type=notification_type,
            method=method,
            is_active=True
        ).first()
    
    def send_fee_reminder(self, student, fee_status):
        """Send fee reminder notification"""
        if not self.settings or not self.settings.auto_fee_reminders:
            return False, "Fee reminders are disabled"
        
        # Create message
        remaining_amount = fee_status.remaining_amount
        due_date = fee_status.next_due_date.strftime('%d/%m/%Y') if fee_status.next_due_date else 'N/A'
        
        message = f"Dear Parent, Fee reminder for {student.name}. Pending amount: ₹{remaining_amount}. Due date: {due_date}. - {student.school.name}"
        
        # Send notifications
        sms_success = False
        if self.settings.sms_enabled:
            sms_success, _ = self.send_sms(
                student.phone, 
                message, 
                notification_type=NotificationType.FEE_REMINDER,
                student_id=student.id,
                entity_type='fee_status',
                entity_id=fee_status.id
            )
        
        whatsapp_success = False
        if self.settings.whatsapp_enabled:
            whatsapp_success, _ = self.send_whatsapp(
                student.phone, 
                message, 
                notification_type=NotificationType.FEE_REMINDER,
                student_id=student.id,
                entity_type='fee_status',
                entity_id=fee_status.id
            )
        
        return sms_success or whatsapp_success, "Fee reminder sent"
    
    def send_bulk_notification(self, students, message, notification_type):
        """Send bulk notification to multiple students"""
        results = []
        
        for student in students:
            # Send SMS if enabled
            if self.settings and self.settings.sms_enabled:
                success, response = self.send_sms(
                    student.phone,
                    message,
                    notification_type=notification_type,
                    student_id=student.id
                )
                results.append({
                    'student_id': student.id,
                    'student_name': student.name,
                    'method': 'SMS',
                    'success': success,
                    'response': response
                })
            
            # Send WhatsApp if enabled
            if self.settings and self.settings.whatsapp_enabled:
                success, response = self.send_whatsapp(
                    student.phone,
                    message,
                    notification_type=notification_type,
                    student_id=student.id
                )
                results.append({
                    'student_id': student.id,
                    'student_name': student.name,
                    'method': 'WhatsApp',
                    'success': success,
                    'response': response
                })
        
        return results


# Import required enums at the end to avoid circular imports
# NotificationType already imported at top