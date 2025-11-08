"""
Background scheduler for automatic notifications
"""
import schedule
import time
import threading
from datetime import datetime, date, timedelta
from flask import current_app
from extensions import db
from services.notification_service import NotificationScheduler
from models.school import School


class NotificationBackgroundScheduler:
    """Background scheduler for automatic notifications"""
    
    def __init__(self):
        self.running = False
        self.thread = None
    
    def start(self):
        """Start the background scheduler"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.thread.start()
            print("Notification scheduler started")
    
    def stop(self):
        """Stop the background scheduler"""
        self.running = False
        if self.thread:
            self.thread.join()
        print("Notification scheduler stopped")
    
    def _run_scheduler(self):
        """Run the scheduler in background thread"""
        # Schedule daily tasks
        schedule.every().day.at("08:00").do(self._send_daily_attendance_alerts)
        schedule.every().day.at("09:00").do(self._send_fee_reminders)
        schedule.every().day.at("10:00").do(self._send_holiday_announcements)
        
        # Schedule weekly tasks
        schedule.every().monday.at("09:00").do(self._send_weekly_reports)
        
        # Schedule monthly tasks
        schedule.every().month.do(self._cleanup_old_logs)
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                print(f"Scheduler error: {e}")
                time.sleep(300)  # Wait 5 minutes on error
    
    def _send_daily_attendance_alerts(self):
        """Send daily attendance alerts for all schools"""
        try:
            with current_app.app_context():
                schools = School.query.filter_by(is_active=True).all()
                
                for school in schools:
                    try:
                        scheduler = NotificationScheduler(school.id)
                        scheduler.schedule_daily_attendance_alerts()
                        print(f"Sent attendance alerts for school: {school.name}")
                    except Exception as e:
                        print(f"Error sending attendance alerts for school {school.id}: {e}")
                        
        except Exception as e:
            print(f"Error in daily attendance alerts: {e}")
    
    def _send_fee_reminders(self):
        """Send fee reminders for all schools"""
        try:
            with current_app.app_context():
                schools = School.query.filter_by(is_active=True).all()
                
                for school in schools:
                    try:
                        scheduler = NotificationScheduler(school.id)
                        scheduler.schedule_fee_reminders()
                        print(f"Sent fee reminders for school: {school.name}")
                    except Exception as e:
                        print(f"Error sending fee reminders for school {school.id}: {e}")
                        
        except Exception as e:
            print(f"Error in fee reminders: {e}")
    
    def _send_holiday_announcements(self):
        """Send holiday announcements for all schools"""
        try:
            with current_app.app_context():
                schools = School.query.filter_by(is_active=True).all()
                
                for school in schools:
                    try:
                        scheduler = NotificationScheduler(school.id)
                        scheduler.schedule_holiday_announcements()
                        print(f"Sent holiday announcements for school: {school.name}")
                    except Exception as e:
                        print(f"Error sending holiday announcements for school {school.id}: {e}")
                        
        except Exception as e:
            print(f"Error in holiday announcements: {e}")
    
    def _send_weekly_reports(self):
        """Send weekly notification reports to school admins"""
        try:
            with current_app.app_context():
                from models.user import User, UserRole
                from services.notification_service import NotificationService
                from models.notification import NotificationType, NotificationChannel
                
                schools = School.query.filter_by(is_active=True).all()
                
                for school in schools:
                    try:
                        # Get school admin
                        admin = User.query.filter_by(
                            school_id=school.id,
                            role=UserRole.SCHOOL_ADMIN
                        ).first()
                        
                        if admin and admin.email:
                            notification_service = NotificationService(school.id)
                            
                            # Get weekly stats
                            stats = notification_service.get_delivery_statistics(days=7)
                            
                            # Prepare report data
                            report_data = {
                                'school_name': school.name,
                                'week_start': (date.today() - timedelta(days=7)).strftime('%d/%m/%Y'),
                                'week_end': date.today().strftime('%d/%m/%Y'),
                                'total_sent': sum(channel_stats['sent'] for channel_stats in stats.values()),
                                'total_delivered': sum(channel_stats['delivered'] for channel_stats in stats.values()),
                                'total_failed': sum(channel_stats['failed'] for channel_stats in stats.values()),
                                'sms_sent': stats.get('sms', {}).get('sent', 0),
                                'whatsapp_sent': stats.get('whatsapp', {}).get('sent', 0),
                                'email_sent': stats.get('email', {}).get('sent', 0)
                            }
                            
                            # Send weekly report
                            notification_service.send_notification(
                                NotificationType.GENERAL_ANNOUNCEMENT,
                                NotificationChannel.EMAIL,
                                {
                                    'type': 'admin',
                                    'id': admin.id,
                                    'email': admin.email,
                                    'name': admin.name
                                },
                                report_data
                            )
                            
                            print(f"Sent weekly report for school: {school.name}")
                            
                    except Exception as e:
                        print(f"Error sending weekly report for school {school.id}: {e}")
                        
        except Exception as e:
            print(f"Error in weekly reports: {e}")
    
    def _cleanup_old_logs(self):
        """Clean up old notification logs"""
        try:
            with current_app.app_context():
                from models.notification import NotificationLog
                
                # Delete logs older than 6 months
                cutoff_date = datetime.utcnow() - timedelta(days=180)
                
                old_logs = NotificationLog.query.filter(
                    NotificationLog.created_at < cutoff_date
                ).delete()
                
                db.session.commit()
                print(f"Cleaned up {old_logs} old notification logs")
                
        except Exception as e:
            print(f"Error in cleanup: {e}")
            db.session.rollback()


# Global scheduler instance
notification_scheduler = NotificationBackgroundScheduler()


def start_notification_scheduler():
    """Start the notification scheduler"""
    notification_scheduler.start()


def stop_notification_scheduler():
    """Stop the notification scheduler"""
    notification_scheduler.stop()


class ManualNotificationTrigger:
    """Manual trigger for notifications (for testing or immediate sending)"""
    
    @staticmethod
    def trigger_attendance_alerts(school_id):
        """Manually trigger attendance alerts for a school"""
        try:
            scheduler = NotificationScheduler(school_id)
            scheduler.schedule_daily_attendance_alerts()
            return True, "Attendance alerts sent successfully"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def trigger_fee_reminders(school_id):
        """Manually trigger fee reminders for a school"""
        try:
            scheduler = NotificationScheduler(school_id)
            scheduler.schedule_fee_reminders()
            return True, "Fee reminders sent successfully"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def trigger_holiday_announcements(school_id):
        """Manually trigger holiday announcements for a school"""
        try:
            scheduler = NotificationScheduler(school_id)
            scheduler.schedule_holiday_announcements()
            return True, "Holiday announcements sent successfully"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def send_custom_announcement(school_id, announcement_data, recipient_groups):
        """Send custom announcement to specified groups"""
        try:
            from services.notification_service import NotificationService
            from models.notification import NotificationType, NotificationChannel
            from models.student import Student
            from models.teacher import Teacher
            
            notification_service = NotificationService(school_id)
            
            # Build recipients list
            recipients = []
            
            for group in recipient_groups:
                if group == 'all_parents':
                    students = Student.query.filter_by(school_id=school_id).all()
                    for student in students:
                        if student.parent_phone or student.email:
                            recipients.append({
                                'type': 'parent',
                                'id': student.id,
                                'phone': student.parent_phone,
                                'email': student.email,
                                'name': student.father_name or student.mother_name or 'Parent',
                                'variables': {
                                    'student_name': student.name,
                                    'class_name': student.class_info.get_display_name() if student.class_info else 'N/A'
                                }
                            })
                
                elif group == 'all_teachers':
                    teachers = Teacher.query.filter_by(school_id=school_id).all()
                    for teacher in teachers:
                        if teacher.phone or teacher.email:
                            recipients.append({
                                'type': 'teacher',
                                'id': teacher.id,
                                'phone': teacher.phone,
                                'email': teacher.email,
                                'name': teacher.user.name if teacher.user else 'Teacher'
                            })
            
            # Send announcements
            results = notification_service.send_general_announcement(recipients, announcement_data)
            
            sent_count = sum(1 for result in results if result.get('success'))
            
            return True, f"Announcement sent to {sent_count} recipients"
            
        except Exception as e:
            return False, str(e)


def setup_notification_templates_for_school(school_id):
    """Setup default notification templates for a new school"""
    try:
        from utils.notification_templates import create_default_templates
        
        success, message = create_default_templates(school_id)
        return success, message
        
    except Exception as e:
        return False, str(e)


def get_notification_delivery_report(school_id, days=30):
    """Get comprehensive notification delivery report"""
    try:
        from services.notification_service import NotificationService
        from models.notification import NotificationLog, NotificationChannel, DeliveryStatus
        from datetime import datetime, timedelta
        
        notification_service = NotificationService(school_id)
        
        # Get basic statistics
        stats = notification_service.get_delivery_statistics(days)
        
        # Get detailed breakdown
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Daily breakdown
        daily_stats = db.session.query(
            db.func.date(NotificationLog.created_at).label('date'),
            NotificationLog.channel,
            NotificationLog.status,
            db.func.count(NotificationLog.id).label('count')
        ).filter(
            NotificationLog.school_id == school_id,
            NotificationLog.created_at >= start_date
        ).group_by(
            db.func.date(NotificationLog.created_at),
            NotificationLog.channel,
            NotificationLog.status
        ).all()
        
        # Format daily stats
        daily_breakdown = {}
        for stat in daily_stats:
            date_str = stat.date.strftime('%Y-%m-%d')
            if date_str not in daily_breakdown:
                daily_breakdown[date_str] = {}
            
            channel = stat.channel.value
            status = stat.status.value
            
            if channel not in daily_breakdown[date_str]:
                daily_breakdown[date_str][channel] = {}
            
            daily_breakdown[date_str][channel][status] = stat.count
        
        # Top failure reasons
        failure_reasons = db.session.query(
            NotificationLog.error_message,
            db.func.count(NotificationLog.id).label('count')
        ).filter(
            NotificationLog.school_id == school_id,
            NotificationLog.status == DeliveryStatus.FAILED,
            NotificationLog.created_at >= start_date,
            NotificationLog.error_message.isnot(None)
        ).group_by(
            NotificationLog.error_message
        ).order_by(
            db.func.count(NotificationLog.id).desc()
        ).limit(10).all()
        
        return {
            'summary': stats,
            'daily_breakdown': daily_breakdown,
            'failure_reasons': [
                {'reason': reason.error_message, 'count': reason.count}
                for reason in failure_reasons
            ],
            'period': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': datetime.utcnow().strftime('%Y-%m-%d'),
                'days': days
            }
        }
        
    except Exception as e:
        return {'error': str(e)}