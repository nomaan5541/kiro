"""
Report Service - Generate various reports for the school management system
"""
from extensions import db
from models.student import Student
from models.attendance import Attendance, AttendanceStatus, AttendanceSummary
from models.fee import Payment, StudentFeeStatus, FeeStructure
from models.activity import ActivityLog
from models.school import School
from models.classes import Class
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_
import json


class ReportService:
    """Service class for generating various reports"""
    
    @staticmethod
    def generate_attendance_report(school_id, class_id=None, start_date=None, end_date=None):
        """Generate attendance report for a school or specific class"""
        try:
            # Set default date range if not provided
            if not start_date:
                start_date = date.today() - timedelta(days=30)
            if not end_date:
                end_date = date.today()
            
            # Base query
            query = db.session.query(
                Student.id,
                Student.name,
                Student.roll_number,
                Student.admission_no,
                Class.class_name,
                Class.section,
                func.count(Attendance.id).label('total_days'),
                func.sum(func.case([(Attendance.status == AttendanceStatus.PRESENT, 1)], else_=0)).label('present_days'),
                func.sum(func.case([(Attendance.status == AttendanceStatus.ABSENT, 1)], else_=0)).label('absent_days'),
                func.sum(func.case([(Attendance.status == AttendanceStatus.LEAVE, 1)], else_=0)).label('leave_days')
            ).join(Class, Student.class_id == Class.id)\
             .outerjoin(Attendance, and_(
                 Student.id == Attendance.student_id,
                 Attendance.date >= start_date,
                 Attendance.date <= end_date
             )).filter(Student.school_id == school_id)
            
            if class_id:
                query = query.filter(Student.class_id == class_id)
            
            results = query.group_by(
                Student.id, Student.name, Student.roll_number, 
                Student.admission_no, Class.class_name, Class.section
            ).all()
            
            # Process results
            report_data = []
            for result in results:
                total_days = result.total_days or 0
                present_days = result.present_days or 0
                absent_days = result.absent_days or 0
                leave_days = result.leave_days or 0
                
                attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
                
                report_data.append({
                    'student_id': result.id,
                    'name': result.name,
                    'roll_number': result.roll_number,
                    'admission_no': result.admission_no,
                    'class': f"{result.class_name} {result.section}" if result.section else result.class_name,
                    'total_days': total_days,
                    'present_days': present_days,
                    'absent_days': absent_days,
                    'leave_days': leave_days,
                    'attendance_percentage': round(attendance_percentage, 2)
                })
            
            # Calculate summary statistics
            total_students = len(report_data)
            avg_attendance = sum(r['attendance_percentage'] for r in report_data) / total_students if total_students > 0 else 0
            
            summary = {
                'total_students': total_students,
                'average_attendance': round(avg_attendance, 2),
                'date_range': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'class_filter': class_id
            }
            
            return {
                'success': True,
                'data': report_data,
                'summary': summary
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error generating attendance report: {str(e)}"
            }
    
    @staticmethod
    def generate_fee_collection_report(school_id, start_date=None, end_date=None):
        """Generate fee collection report"""
        try:
            # Set default date range if not provided
            if not start_date:
                start_date = date.today() - timedelta(days=30)
            if not end_date:
                end_date = date.today()
            
            # Get payments in date range
            payments = Payment.query.filter(
                Payment.school_id == school_id,
                Payment.payment_date >= start_date,
                Payment.payment_date <= end_date
            ).all()
            
            # Calculate totals
            total_collected = sum(payment.amount for payment in payments)
            total_transactions = len(payments)
            
            # Payment mode breakdown
            mode_breakdown = {}
            for payment in payments:
                mode = payment.payment_mode.value
                mode_breakdown[mode] = mode_breakdown.get(mode, 0) + float(payment.amount)
            
            # Daily collection breakdown
            daily_breakdown = {}
            for payment in payments:
                day_key = payment.payment_date.isoformat()
                daily_breakdown[day_key] = daily_breakdown.get(day_key, 0) + float(payment.amount)
            
            # Class-wise collection
            class_breakdown = {}
            for payment in payments:
                if payment.student and payment.student.class_info:
                    class_name = payment.student.class_info.get_display_name()
                    class_breakdown[class_name] = class_breakdown.get(class_name, 0) + float(payment.amount)
            
            # Outstanding fees
            outstanding_fees = db.session.query(
                func.sum(StudentFeeStatus.remaining_amount)
            ).filter(
                StudentFeeStatus.school_id == school_id,
                StudentFeeStatus.remaining_amount > 0
            ).scalar() or 0
            
            return {
                'success': True,
                'summary': {
                    'total_collected': float(total_collected),
                    'total_transactions': total_transactions,
                    'average_payment': float(total_collected / total_transactions) if total_transactions > 0 else 0,
                    'outstanding_fees': float(outstanding_fees),
                    'date_range': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat()
                    }
                },
                'breakdowns': {
                    'payment_modes': mode_breakdown,
                    'daily_collections': daily_breakdown,
                    'class_wise': class_breakdown
                },
                'payments': [payment.to_dict() for payment in payments]
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error generating fee collection report: {str(e)}"
            }
    
    @staticmethod
    def generate_student_performance_report(school_id, class_id=None):
        """Generate student performance report"""
        try:
            # Base query for students
            query = Student.query.filter_by(school_id=school_id)
            if class_id:
                query = query.filter_by(class_id=class_id)
            
            students = query.all()
            
            report_data = []
            for student in students:
                # Get attendance summary
                attendance_summary = AttendanceSummary.query.filter_by(
                    student_id=student.id
                ).order_by(AttendanceSummary.year.desc(), AttendanceSummary.month.desc()).first()
                
                # Get fee status
                fee_status = StudentFeeStatus.query.filter_by(student_id=student.id).first()
                
                # Get recent activities
                recent_activities = ActivityLog.query.filter_by(
                    school_id=school_id,
                    entity_type='student',
                    entity_id=student.id
                ).order_by(ActivityLog.created_at.desc()).limit(5).all()
                
                student_data = {
                    'student': student.to_dict(),
                    'attendance': {
                        'percentage': attendance_summary.attendance_percentage if attendance_summary else 0,
                        'total_days': attendance_summary.total_days if attendance_summary else 0,
                        'present_days': attendance_summary.present_days if attendance_summary else 0
                    },
                    'fees': {
                        'total_fee': float(fee_status.total_fee) if fee_status else 0,
                        'paid_amount': float(fee_status.paid_amount) if fee_status else 0,
                        'payment_percentage': fee_status.payment_percentage if fee_status else 0,
                        'is_overdue': fee_status.is_overdue if fee_status else False
                    },
                    'recent_activities': [activity.to_dict() for activity in recent_activities]
                }
                
                report_data.append(student_data)
            
            # Calculate class statistics
            total_students = len(report_data)
            avg_attendance = sum(s['attendance']['percentage'] for s in report_data) / total_students if total_students > 0 else 0
            avg_fee_payment = sum(s['fees']['payment_percentage'] for s in report_data) / total_students if total_students > 0 else 0
            overdue_count = sum(1 for s in report_data if s['fees']['is_overdue'])
            
            summary = {
                'total_students': total_students,
                'average_attendance': round(avg_attendance, 2),
                'average_fee_payment': round(avg_fee_payment, 2),
                'overdue_fees_count': overdue_count,
                'class_filter': class_id
            }
            
            return {
                'success': True,
                'data': report_data,
                'summary': summary
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error generating student performance report: {str(e)}"
            }
    
    @staticmethod
    def generate_school_overview_report(school_id):
        """Generate comprehensive school overview report"""
        try:
            school = School.query.get(school_id)
            if not school:
                return {'success': False, 'error': 'School not found'}
            
            # Basic statistics
            total_students = Student.query.filter_by(school_id=school_id).count()
            total_classes = Class.query.filter_by(school_id=school_id).count()
            
            # Attendance statistics (last 30 days)
            thirty_days_ago = date.today() - timedelta(days=30)
            attendance_stats = db.session.query(
                func.count(Attendance.id).label('total_records'),
                func.sum(func.case([(Attendance.status == AttendanceStatus.PRESENT, 1)], else_=0)).label('present_count'),
                func.sum(func.case([(Attendance.status == AttendanceStatus.ABSENT, 1)], else_=0)).label('absent_count')
            ).filter(
                Attendance.school_id == school_id,
                Attendance.date >= thirty_days_ago
            ).first()
            
            overall_attendance = 0
            if attendance_stats.total_records and attendance_stats.total_records > 0:
                overall_attendance = (attendance_stats.present_count / attendance_stats.total_records) * 100
            
            # Fee statistics
            fee_stats = db.session.query(
                func.sum(StudentFeeStatus.total_fee).label('total_fees'),
                func.sum(StudentFeeStatus.paid_amount).label('collected_fees'),
                func.sum(StudentFeeStatus.remaining_amount).label('outstanding_fees'),
                func.count(StudentFeeStatus.id).label('total_fee_records')
            ).filter(StudentFeeStatus.school_id == school_id).first()
            
            # Recent activities
            recent_activities = ActivityLog.query.filter_by(
                school_id=school_id
            ).order_by(ActivityLog.created_at.desc()).limit(10).all()
            
            # Class-wise breakdown
            class_breakdown = db.session.query(
                Class.class_name,
                Class.section,
                func.count(Student.id).label('student_count')
            ).outerjoin(Student, Class.id == Student.class_id)\
             .filter(Class.school_id == school_id)\
             .group_by(Class.id, Class.class_name, Class.section).all()
            
            report_data = {
                'school_info': school.to_dict(),
                'statistics': {
                    'total_students': total_students,
                    'total_classes': total_classes,
                    'overall_attendance_percentage': round(overall_attendance, 2),
                    'total_fees': float(fee_stats.total_fees or 0),
                    'collected_fees': float(fee_stats.collected_fees or 0),
                    'outstanding_fees': float(fee_stats.outstanding_fees or 0),
                    'fee_collection_percentage': round(
                        (float(fee_stats.collected_fees or 0) / float(fee_stats.total_fees or 1)) * 100, 2
                    ) if fee_stats.total_fees else 0
                },
                'class_breakdown': [
                    {
                        'class_name': f"{cb.class_name} {cb.section}" if cb.section else cb.class_name,
                        'student_count': cb.student_count
                    }
                    for cb in class_breakdown
                ],
                'recent_activities': [activity.to_dict() for activity in recent_activities],
                'generated_at': datetime.now().isoformat()
            }
            
            return {
                'success': True,
                'data': report_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error generating school overview report: {str(e)}"
            }
    
    @staticmethod
    def generate_monthly_summary_report(school_id, month=None, year=None):
        """Generate monthly summary report"""
        try:
            # Use current month/year if not provided
            if not month:
                month = date.today().month
            if not year:
                year = date.today().year
            
            # Date range for the month
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
            
            # Attendance summary
            attendance_report = ReportService.generate_attendance_report(
                school_id, start_date=start_date, end_date=end_date
            )
            
            # Fee collection summary
            fee_report = ReportService.generate_fee_collection_report(
                school_id, start_date=start_date, end_date=end_date
            )
            
            # New enrollments
            new_students = Student.query.filter(
                Student.school_id == school_id,
                Student.admission_date >= start_date,
                Student.admission_date <= end_date
            ).count()
            
            # Activities summary
            activities_count = ActivityLog.query.filter(
                ActivityLog.school_id == school_id,
                func.date(ActivityLog.created_at) >= start_date,
                func.date(ActivityLog.created_at) <= end_date
            ).count()
            
            return {
                'success': True,
                'data': {
                    'month': month,
                    'year': year,
                    'date_range': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat()
                    },
                    'attendance_summary': attendance_report,
                    'fee_collection_summary': fee_report,
                    'new_enrollments': new_students,
                    'total_activities': activities_count,
                    'generated_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error generating monthly summary report: {str(e)}"
            }