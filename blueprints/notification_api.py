"""
Notification API Blueprint - Handles notification-related API endpoints
"""
from flask import Blueprint, request, jsonify, session, Response
from extensions import db
from models.user import User
from models.student import Student
from models.notification import NotificationTemplate, NotificationLog, NotificationType, NotificationChannel
from services.notification_service import NotificationService
from utils.auth import login_required, role_required
from datetime import datetime
import csv
import io

notification_api_bp = Blueprint('notification_api', __name__)


@notification_api_bp.route('/api/notifications/send', methods=['POST'])
@role_required('school_admin')
def send_notification():
    """Send notification to selected recipients"""
    user = User.query.get(session['user_id'])
    
    try:
        data = request.get_json()
        
        notification_service = NotificationService(user.school_id)
        
        # Get recipients
        recipient_ids = data.get('recipients', [])
        students = Student.query.filter(
            Student.id.in_(recipient_ids),
            Student.school_id == user.school_id
        ).all()
        
        if not students:
            return jsonify({'success': False, 'message': 'No valid recipients found'}), 400
        
        # Prepare recipients data
        recipients_data = []
        for student in students:
            recipients_data.append({
                'type': 'student',
                'id': student.id,
                'phone': student.phone or student.parent_phone,
                'email': student.email,
                'name': student.name,
                'variables': {
                    'student_name': student.name,
                    'class_name': student.class_info.get_display_name() if student.class_info else 'N/A',
                    'school_name': student.school.name,
                    'date': datetime.now().strftime('%d/%m/%Y')
                }
            })
        
        # Determine notification type and channel
        notification_type = NotificationType(data['type'])
        
        # Handle multiple channels
        channels = []
        if data['channel'] == 'all':
            channels = [NotificationChannel.SMS, NotificationChannel.WHATSAPP, NotificationChannel.EMAIL]
        else:
            channels = [NotificationChannel(data['channel'])]
        
        # Send notifications
        total_sent = 0
        results = []
        
        for channel in channels:
            # Skip email if no email addresses
            if channel == NotificationChannel.EMAIL:
                email_recipients = [r for r in recipients_data if r.get('email')]
                if not email_recipients:
                    continue
                channel_recipients = email_recipients
            else:
                # Skip SMS/WhatsApp if no phone numbers
                phone_recipients = [r for r in recipients_data if r.get('phone')]
                if not phone_recipients:
                    continue
                channel_recipients = phone_recipients
            
            # Use template or custom message
            template_id = data.get('template_id') if data.get('template_id') else None
            
            # For custom messages, create a temporary template
            if not template_id:
                # Create variables for message rendering
                variables = {
                    'message': data['message'],
                    'subject': data.get('subject', '')
                }
                
                # Send to each recipient individually for custom messages
                for recipient in channel_recipients:
                    success, result = notification_service.send_notification(
                        notification_type,
                        channel,
                        recipient,
                        recipient.get('variables', {}),
                        template_id
                    )
                    
                    if success:
                        total_sent += 1
                    
                    results.append({
                        'recipient': recipient['name'],
                        'channel': channel.value,
                        'success': success,
                        'result': result
                    })
            else:
                # Use existing template
                channel_results = notification_service.send_bulk_notification(
                    notification_type,
                    channel,
                    channel_recipients,
                    template_id=template_id
                )
                
                for result in channel_results:
                    if result['success']:
                        total_sent += 1
                
                results.extend(channel_results)
        
        return jsonify({
            'success': True,
            'sent_count': total_sent,
            'results': results
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@notification_api_bp.route('/api/notifications/templates', methods=['POST'])
@role_required('school_admin')
def create_template():
    """Create a new notification template"""
    user = User.query.get(session['user_id'])
    
    try:
        data = request.get_json()
        
        # Check if template with same name exists
        existing = NotificationTemplate.query.filter_by(
            school_id=user.school_id,
            name=data['name']
        ).first()
        
        if existing:
            return jsonify({'success': False, 'message': 'Template with this name already exists'}), 400
        
        # Create template
        template = NotificationTemplate(
            school_id=user.school_id,
            name=data['name'],
            type=NotificationType(data['type']),
            channel=NotificationChannel(data['channel']),
            subject=data.get('subject'),
            message_template=data['message'],
            is_active=True,
            is_default=False,
            created_by=user.id
        )
        
        db.session.add(template)
        db.session.commit()
        
        return jsonify({'success': True, 'template_id': template.id})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@notification_api_bp.route('/api/notifications/templates/<int:template_id>', methods=['PUT'])
@role_required('school_admin')
def update_template(template_id):
    """Update an existing notification template"""
    user = User.query.get(session['user_id'])
    
    try:
        template = NotificationTemplate.query.filter_by(
            id=template_id,
            school_id=user.school_id
        ).first()
        
        if not template:
            return jsonify({'success': False, 'message': 'Template not found'}), 404
        
        data = request.get_json()
        
        # Update template
        template.name = data.get('name', template.name)
        template.type = NotificationType(data['type']) if data.get('type') else template.type
        template.channel = NotificationChannel(data['channel']) if data.get('channel') else template.channel
        template.subject = data.get('subject', template.subject)
        template.message_template = data.get('message', template.message_template)
        template.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@notification_api_bp.route('/api/notifications/templates/<int:template_id>', methods=['DELETE'])
@role_required('school_admin')
def delete_template(template_id):
    """Delete a notification template"""
    user = User.query.get(session['user_id'])
    
    try:
        template = NotificationTemplate.query.filter_by(
            id=template_id,
            school_id=user.school_id
        ).first()
        
        if not template:
            return jsonify({'success': False, 'message': 'Template not found'}), 404
        
        # Check if template is being used
        usage_count = NotificationLog.query.filter_by(template_id=template_id).count()
        if usage_count > 0:
            # Soft delete - mark as inactive
            template.is_active = False
            db.session.commit()
            return jsonify({'success': True, 'message': 'Template deactivated (was in use)'})
        else:
            # Hard delete
            db.session.delete(template)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Template deleted'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@notification_api_bp.route('/api/notifications/<int:notification_id>/resend', methods=['POST'])
@role_required('school_admin')
def resend_notification(notification_id):
    """Resend a failed notification"""
    user = User.query.get(session['user_id'])
    
    try:
        notification_log = NotificationLog.query.filter_by(
            id=notification_id,
            school_id=user.school_id
        ).first()
        
        if not notification_log:
            return jsonify({'success': False, 'message': 'Notification not found'}), 404
        
        if notification_log.status.value != 'failed':
            return jsonify({'success': False, 'message': 'Can only resend failed notifications'}), 400
        
        # Prepare recipient data
        recipient_data = {
            'type': notification_log.recipient_type,
            'id': notification_log.recipient_id,
            'phone': notification_log.recipient_phone,
            'email': notification_log.recipient_email,
            'name': notification_log.recipient_name
        }
        
        # Resend notification
        notification_service = NotificationService(user.school_id)
        success, result = notification_service.send_notification(
            notification_log.type,
            notification_log.channel,
            recipient_data,
            template_id=notification_log.template_id
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Notification resent successfully'})
        else:
            return jsonify({'success': False, 'message': f'Failed to resend: {result}'}), 500
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@notification_api_bp.route('/api/notifications/statistics')
@role_required('school_admin')
def get_statistics():
    """Get detailed notification statistics"""
    user = User.query.get(session['user_id'])
    
    try:
        notification_service = NotificationService(user.school_id)
        stats = notification_service.get_delivery_statistics(30)
        
        return jsonify({'success': True, 'statistics': stats})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@notification_api_bp.route('/api/notifications/export')
@role_required('school_admin')
def export_notifications():
    """Export notification logs to CSV"""
    user = User.query.get(session['user_id'])
    
    try:
        # Get notification logs
        notifications = NotificationLog.query.filter_by(
            school_id=user.school_id
        ).order_by(NotificationLog.created_at.desc()).limit(1000).all()
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Date', 'Type', 'Channel', 'Recipient Name', 'Recipient Contact',
            'Subject', 'Message', 'Status', 'Sent At', 'Delivered At'
        ])
        
        # Write data
        for notification in notifications:
            writer.writerow([
                notification.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                notification.type.value.replace('_', ' ').title(),
                notification.channel.value.upper(),
                notification.recipient_name or 'Unknown',
                notification.recipient_phone or notification.recipient_email or 'N/A',
                notification.subject or 'N/A',
                notification.message[:100] + '...' if len(notification.message) > 100 else notification.message,
                notification.status.value.title(),
                notification.sent_at.strftime('%Y-%m-%d %H:%M:%S') if notification.sent_at else 'Not sent',
                notification.delivered_at.strftime('%Y-%m-%d %H:%M:%S') if notification.delivered_at else 'Not delivered'
            ])
        
        # Create response
        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=notifications_{datetime.now().strftime("%Y%m%d")}.csv'}
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@notification_api_bp.route('/api/notifications/send_bulk_reminders', methods=['POST'])
@role_required('school_admin')
def send_bulk_reminders():
    """Send bulk fee reminders to all overdue students"""
    user = User.query.get(session['user_id'])
    
    try:
        from services.fee_service import FeeService
        
        fee_service = FeeService(user.school_id)
        result = fee_service.send_fee_reminders()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@notification_api_bp.route('/api/notifications/send_attendance_alerts', methods=['POST'])
@role_required('school_admin')
def send_attendance_alerts():
    """Send attendance alerts for today's absent students"""
    user = User.query.get(session['user_id'])
    
    try:
        from services.notification_service import NotificationScheduler
        
        scheduler = NotificationScheduler(user.school_id)
        scheduler.schedule_daily_attendance_alerts()
        
        return jsonify({'success': True, 'message': 'Attendance alerts sent successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@notification_api_bp.route('/api/notifications/templates/<int:template_id>/preview', methods=['POST'])
@role_required('school_admin')
def preview_template(template_id):
    """Preview a notification template with sample data"""
    user = User.query.get(session['user_id'])
    
    try:
        template = NotificationTemplate.query.filter_by(
            id=template_id,
            school_id=user.school_id
        ).first()
        
        if not template:
            return jsonify({'success': False, 'message': 'Template not found'}), 404
        
        # Sample variables for preview
        sample_variables = {
            'student_name': 'John Doe',
            'class_name': 'Class 10-A',
            'school_name': 'Demo School',
            'date': datetime.now().strftime('%d/%m/%Y'),
            'amount': '₹5,000',
            'due_date': '31/12/2024'
        }
        
        # Render template
        rendered_message = template.render_message(sample_variables)
        
        return jsonify({
            'success': True,
            'preview': {
                'subject': template.subject,
                'message': rendered_message,
                'channel': template.channel.value,
                'type': template.type.value
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# Error handlers
@notification_api_bp.errorhandler(403)
def forbidden(error):
    return jsonify({'error': 'Access denied'}), 403

@notification_api_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@notification_api_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500