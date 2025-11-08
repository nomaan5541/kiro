"""
Advanced Reporting Service for comprehensive school analytics
"""
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import func, and_, or_, extract, case
from extensions import db
import json
import csv
import io


class AdvancedReportService:
    """Service for generating comprehensive school reports"""
    
    def __init__(self, school_id):
        self.school_id = school_id
    
    def generate_report(self, category, report_type, filters=None):
        """Main method to generate reports based on category and type"""
        if filters is None:
            filters = {}
        
        # Parse date filters
        start_date = None
        end_date = None
        
        if filters.get('dateRange') == 'custom':
            if filters.get('fromDate'):
                start_date = datetime.strptime(filters['fromDate'], '%Y-%m-%d').date()
            if filters.get('toDate'):
                end_date = datetime.strptime(filters['toDate'], '%Y-%m-%d').date()
        else:
            start_date, end_date = self._get_date_range(filters.get('dateRange', 'month'))
        
        class_filter = filters.get('classFilter') if filters.get('classFilter') else None
        
        # Generate report based on category and type
        if category == 'student':
            return self._generate_student_report(report_type, start_date, end_date, class_filter)
        elif category == 'financial':
            return self._generate_financial_report(report_type, start_date, end_date, class_filter)
        elif category == 'academic':
            return self._generate_academic_report(report_type, class_filter)
        elif category == 'admin':
            return self._generate_admin_report(report_type)
        else:
            raise ValueError(f"Unknown report category: {category}")
    
    def _get_date_range(self, range_type):
        """Get start and end dates based on range type"""
        today = date.today()
        
        if range_type == 'today':
            return today, today
        elif range_type == 'week':
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=6)
            return start, end
        elif range_type == 'month':
            start = today.replace(day=1)
            if today.month == 12:
                end = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            return start, end
        elif range_type == 'quarter':
            quarter = (today.month - 1) // 3 + 1
            start = date(today.year, (quarter - 1) * 3 + 1, 1)
            if quarter == 4:
                end = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                end = date(today.year, quarter * 3 + 1, 1) - timedelta(days=1)
            return start, end
        elif range_type == 'year':
            start = date(today.year, 1, 1)
            end = date(today.year, 12, 31)
            return start, end
        else:
            # Default to current month
            start = today.replace(day=1)
            if today.month == 12:
                end = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            return start, end
    
    def _generate_student_report(self, report_type, start_date, end_date, class_filter):
        """Generate student category reports"""
        if report_type == 'enrollment':
            data = self.generate_enrollment_report(start_date, end_date, class_filter)
            return self._format_enrollment_report(data)
        elif report_type == 'performance':
            data = self.generate_performance_report(class_filter)
            return self._format_performance_report(data)
        elif report_type == 'attendance':
            data = self.generate_attendance_report(start_date, end_date, class_filter)
            return self._format_attendance_report(data)
        elif report_type == 'demographics':
            data = self.generate_demographics_report()
            return self._format_demographics_report(data)
        else:
            raise ValueError(f"Unknown student report type: {report_type}")
    
    def _generate_financial_report(self, report_type, start_date, end_date, class_filter):
        """Generate financial category reports"""
        if report_type == 'collection':
            data = self.generate_fee_collection_report(start_date, end_date, class_filter)
            return self._format_fee_collection_report(data)
        elif report_type == 'outstanding':
            data = self.generate_outstanding_fees_report(class_filter)
            return self._format_outstanding_fees_report(data)
        elif report_type == 'revenue':
            data = self.generate_monthly_revenue_report()
            return self._format_revenue_report(data)
        elif report_type == 'expenses':
            # Placeholder for expense tracking
            return self._format_expense_report({})
        else:
            raise ValueError(f"Unknown financial report type: {report_type}")
    
    def _generate_academic_report(self, report_type, class_filter):
        """Generate academic category reports"""
        if report_type == 'class_performance':
            data = self.generate_class_wise_report(class_filter)
            return self._format_class_performance_report(data)
        elif report_type == 'subject_analysis':
            # Placeholder for subject analysis
            return self._format_subject_analysis_report({})
        elif report_type == 'teacher_performance':
            data = self.generate_teacher_performance_report()
            return self._format_teacher_performance_report(data)
        elif report_type == 'curriculum':
            # Placeholder for curriculum progress
            return self._format_curriculum_report({})
        else:
            raise ValueError(f"Unknown academic report type: {report_type}")
    
    def _generate_admin_report(self, report_type):
        """Generate administrative category reports"""
        if report_type == 'staff':
            data = self.generate_staff_report()
            return self._format_staff_report(data)
        elif report_type == 'infrastructure':
            # Placeholder for infrastructure report
            return self._format_infrastructure_report({})
        elif report_type == 'compliance':
            # Placeholder for compliance report
            return self._format_compliance_report({})
        elif report_type == 'activity':
            # Placeholder for activity report
            return self._format_activity_report({})
        else:
            raise ValueError(f"Unknown admin report type: {report_type}")
    
    # Student Reports
    def generate_enrollment_report(self, start_date=None, end_date=None, class_filter=None):
        """Generate student enrollment report"""
        from models.student import Student, StudentStatus
        from models.classes import Class
        
        query = Student.query.filter_by(school_id=self.school_id)
        
        if start_date:
            query = query.filter(Student.admission_date >= start_date)
        if end_date:
            query = query.filter(Student.admission_date <= end_date)
        if class_filter:
            query = query.filter_by(class_id=class_filter)
        
        students = query.all()
        
        # Calculate enrollment statistics
        total_enrolled = len(students)
        active_students = len([s for s in students if s.status == StudentStatus.ACTIVE])
        inactive_students = total_enrolled - active_students
        
        # Group by class
        class_breakdown = {}
        for student in students:
            class_name = student.class_info.get_display_name() if student.class_info else 'No Class'
            if class_name not in class_breakdown:
                class_breakdown[class_name] = {'total': 0, 'active': 0, 'inactive': 0}
            
            class_breakdown[class_name]['total'] += 1
            if student.status == StudentStatus.ACTIVE:
                class_breakdown[class_name]['active'] += 1
            else:
                class_breakdown[class_name]['inactive'] += 1
        
        # Monthly enrollment trend
        monthly_trend = self._get_monthly_enrollment_trend(start_date, end_date)
        
        return {
            'summary': {
                'total_enrolled': total_enrolled,
                'active_students': active_students,
                'inactive_students': inactive_students,
                'enrollment_rate': (active_students / max(total_enrolled, 1)) * 100
            },
            'class_breakdown': class_breakdown,
            'monthly_trend': monthly_trend,
            'students': [s.to_dict() for s in students]
        }
    
    def generate_performance_report(self, class_filter=None, subject_filter=None):
        """Generate student performance report"""
        from models.student import Student
        from models.classes import Class, Subject
        
        # This is a placeholder implementation
        # In a real system, you'd have grades/marks tables
        
        query = Student.query.filter_by(school_id=self.school_id)
        if class_filter:
            query = query.filter_by(class_id=class_filter)
        
        students = query.all()
        
        # Mock performance data
        import random
        performance_data = []
        
        for student in students:
            performance = {
                'student_id': student.id,
                'student_name': student.name,
                'class': student.class_info.get_display_name() if student.class_info else 'No Class',
                'overall_grade': random.choice(['A+', 'A', 'B+', 'B', 'C+', 'C']),
                'percentage': random.randint(60, 98),
                'subjects': []
            }
            
            # Mock subject-wise performance
            subjects = ['Mathematics', 'English', 'Science', 'Social Studies']
            for subject in subjects:
                performance['subjects'].append({
                    'subject': subject,
                    'marks': random.randint(50, 100),
                    'grade': random.choice(['A', 'B', 'C', 'D'])
                })
            
            performance_data.append(performance)
        
        # Calculate class averages
        class_averages = {}
        for perf in performance_data:
            class_name = perf['class']
            if class_name not in class_averages:
                class_averages[class_name] = {'total': 0, 'count': 0}
            class_averages[class_name]['total'] += perf['percentage']
            class_averages[class_name]['count'] += 1
        
        for class_name in class_averages:
            class_averages[class_name]['average'] = class_averages[class_name]['total'] / class_averages[class_name]['count']
        
        return {
            'performance_data': performance_data,
            'class_averages': class_averages,
            'top_performers': sorted(performance_data, key=lambda x: x['percentage'], reverse=True)[:10]
        }    

    def generate_attendance_report(self, start_date=None, end_date=None, class_filter=None):
        """Generate comprehensive attendance report"""
        from models.attendance import Attendance, AttendanceStatus
        from models.student import Student
        from models.classes import Class
        
        # Set default date range if not provided
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()
        
        # Base query
        query = Attendance.query.filter(
            Attendance.school_id == self.school_id,
            Attendance.date >= start_date,
            Attendance.date <= end_date
        )
        
        if class_filter:
            query = query.filter_by(class_id=class_filter)
        
        attendance_records = query.all()
        
        # Calculate overall statistics
        total_records = len(attendance_records)
        present_records = len([a for a in attendance_records if a.status == AttendanceStatus.PRESENT])
        absent_records = total_records - present_records
        
        overall_percentage = (present_records / max(total_records, 1)) * 100
        
        # Student-wise attendance
        student_attendance = {}
        for record in attendance_records:
            student_id = record.student_id
            if student_id not in student_attendance:
                student_attendance[student_id] = {
                    'student': record.student,
                    'total_days': 0,
                    'present_days': 0,
                    'absent_days': 0,
                    'percentage': 0
                }
            
            student_attendance[student_id]['total_days'] += 1
            if record.status == AttendanceStatus.PRESENT:
                student_attendance[student_id]['present_days'] += 1
            else:
                student_attendance[student_id]['absent_days'] += 1
        
        # Calculate percentages
        for student_id in student_attendance:
            data = student_attendance[student_id]
            data['percentage'] = (data['present_days'] / max(data['total_days'], 1)) * 100
        
        # Class-wise attendance
        class_attendance = {}
        for record in attendance_records:
            class_name = record.class_info.get_display_name() if record.class_info else 'No Class'
            if class_name not in class_attendance:
                class_attendance[class_name] = {
                    'total_records': 0,
                    'present_records': 0,
                    'percentage': 0
                }
            
            class_attendance[class_name]['total_records'] += 1
            if record.status == AttendanceStatus.PRESENT:
                class_attendance[class_name]['present_records'] += 1
        
        # Calculate class percentages
        for class_name in class_attendance:
            data = class_attendance[class_name]
            data['percentage'] = (data['present_records'] / max(data['total_records'], 1)) * 100
        
        # Daily attendance trend
        daily_trend = self._get_daily_attendance_trend(start_date, end_date)
        
        return {
            'summary': {
                'total_records': total_records,
                'present_records': present_records,
                'absent_records': absent_records,
                'overall_percentage': round(overall_percentage, 2),
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                }
            },
            'student_attendance': list(student_attendance.values()),
            'class_attendance': class_attendance,
            'daily_trend': daily_trend
        }
    
    def generate_demographics_report(self):
        """Generate student demographics report"""
        from models.student import Student
        
        students = Student.query.filter_by(school_id=self.school_id).all()
        
        # Gender distribution
        gender_distribution = {'male': 0, 'female': 0, 'other': 0}
        for student in students:
            gender_distribution[student.gender] = gender_distribution.get(student.gender, 0) + 1
        
        # Age distribution
        age_distribution = {}
        for student in students:
            if student.date_of_birth:
                age = student.get_age()
                age_group = f"{(age // 5) * 5}-{(age // 5) * 5 + 4}"
                age_distribution[age_group] = age_distribution.get(age_group, 0) + 1
        
        # Class distribution
        class_distribution = {}
        for student in students:
            class_name = student.class_info.get_display_name() if student.class_info else 'No Class'
            class_distribution[class_name] = class_distribution.get(class_name, 0) + 1
        
        # Blood group distribution
        blood_group_distribution = {}
        for student in students:
            if student.blood_group:
                blood_group_distribution[student.blood_group] = blood_group_distribution.get(student.blood_group, 0) + 1
        
        # Geographic distribution (by city/state)
        geographic_distribution = {}
        for student in students:
            location = f"{student.city or 'Unknown'}, {student.state or 'Unknown'}"
            geographic_distribution[location] = geographic_distribution.get(location, 0) + 1
        
        return {
            'total_students': len(students),
            'gender_distribution': gender_distribution,
            'age_distribution': age_distribution,
            'class_distribution': class_distribution,
            'blood_group_distribution': blood_group_distribution,
            'geographic_distribution': geographic_distribution
        }  
  
    # Financial Reports
    def generate_fee_collection_report(self, start_date=None, end_date=None, class_filter=None):
        """Generate comprehensive fee collection report"""
        from models.fee import Payment, StudentFeeStatus, FeeStructure
        from models.student import Student
        
        # Set default date range
        if not start_date:
            start_date = date.today().replace(day=1)  # Start of current month
        if not end_date:
            end_date = date.today()
        
        # Get payments in date range
        payments_query = Payment.query.filter(
            Payment.school_id == self.school_id,
            Payment.payment_date >= start_date,
            Payment.payment_date <= end_date
        )
        
        if class_filter:
            payments_query = payments_query.join(Student).filter(Student.class_id == class_filter)
        
        payments = payments_query.all()
        
        # Calculate totals
        total_collected = sum(payment.amount for payment in payments)
        total_transactions = len(payments)
        
        # Payment mode breakdown
        payment_modes = {}
        for payment in payments:
            mode = payment.payment_mode.value if payment.payment_mode else 'Unknown'
            payment_modes[mode] = payment_modes.get(mode, 0) + float(payment.amount)
        
        # Class-wise collection
        class_collections = {}
        for payment in payments:
            student = payment.student
            class_name = student.class_info.get_display_name() if student and student.class_info else 'No Class'
            if class_name not in class_collections:
                class_collections[class_name] = {'amount': 0, 'transactions': 0}
            class_collections[class_name]['amount'] += float(payment.amount)
            class_collections[class_name]['transactions'] += 1
        
        # Daily collection trend
        daily_collections = {}
        for payment in payments:
            day = payment.payment_date.isoformat()
            daily_collections[day] = daily_collections.get(day, 0) + float(payment.amount)
        
        # Outstanding fees calculation
        outstanding_fees = self._calculate_outstanding_fees(class_filter)
        
        return {
            'summary': {
                'total_collected': float(total_collected),
                'total_transactions': total_transactions,
                'average_transaction': float(total_collected) / max(total_transactions, 1),
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                }
            },
            'payment_modes': payment_modes,
            'class_collections': class_collections,
            'daily_collections': daily_collections,
            'outstanding_fees': outstanding_fees,
            'recent_payments': [self._payment_to_dict(p) for p in payments[-10:]]
        }
    
    def generate_outstanding_fees_report(self, class_filter=None):
        """Generate outstanding fees report"""
        from models.fee import StudentFeeStatus, FeeStructure
        from models.student import Student
        
        query = StudentFeeStatus.query.filter_by(school_id=self.school_id)
        if class_filter:
            query = query.join(Student).filter(Student.class_id == class_filter)
        
        fee_statuses = query.all()
        
        outstanding_students = []
        total_outstanding = Decimal('0')
        
        for status in fee_statuses:
            if status.remaining_amount > 0:
                outstanding_students.append({
                    'student_id': status.student_id,
                    'student_name': status.student.name if status.student else 'Unknown',
                    'class': status.student.class_info.get_display_name() if status.student and status.student.class_info else 'No Class',
                    'total_fee': float(status.total_fee),
                    'paid_amount': float(status.paid_amount),
                    'remaining_amount': float(status.remaining_amount),
                    'last_payment_date': status.last_payment_date.isoformat() if status.last_payment_date else None,
                    'is_overdue': status.is_overdue
                })
                total_outstanding += status.remaining_amount
        
        # Group by class
        class_outstanding = {}
        for student in outstanding_students:
            class_name = student['class']
            if class_name not in class_outstanding:
                class_outstanding[class_name] = {'students': 0, 'amount': 0}
            class_outstanding[class_name]['students'] += 1
            class_outstanding[class_name]['amount'] += student['remaining_amount']
        
        return {
            'summary': {
                'total_outstanding': float(total_outstanding),
                'students_with_dues': len(outstanding_students),
                'overdue_students': len([s for s in outstanding_students if s['is_overdue']])
            },
            'outstanding_students': outstanding_students,
            'class_outstanding': class_outstanding
        }
    
    def generate_monthly_revenue_report(self, year=None, month=None):
        """Generate monthly revenue report"""
        from models.fee import Payment
        
        if not year:
            year = date.today().year
        if not month:
            month = date.today().month
        
        # Get payments for the month
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        payments = Payment.query.filter(
            Payment.school_id == self.school_id,
            Payment.payment_date >= start_date,
            Payment.payment_date <= end_date
        ).all()
        
        total_revenue = sum(payment.amount for payment in payments)
        
        # Daily breakdown
        daily_revenue = {}
        for payment in payments:
            day = payment.payment_date.day
            daily_revenue[day] = daily_revenue.get(day, 0) + float(payment.amount)
        
        # Compare with previous month
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        
        prev_start = date(prev_year, prev_month, 1)
        if prev_month == 12:
            prev_end = date(prev_year + 1, 1, 1) - timedelta(days=1)
        else:
            prev_end = date(prev_year, prev_month + 1, 1) - timedelta(days=1)
        
        prev_payments = Payment.query.filter(
            Payment.school_id == self.school_id,
            Payment.payment_date >= prev_start,
            Payment.payment_date <= prev_end
        ).all()
        
        prev_revenue = sum(payment.amount for payment in prev_payments)
        growth_rate = ((float(total_revenue) - float(prev_revenue)) / max(float(prev_revenue), 1)) * 100
        
        return {
            'month': f"{year}-{month:02d}",
            'total_revenue': float(total_revenue),
            'total_transactions': len(payments),
            'daily_revenue': daily_revenue,
            'previous_month_revenue': float(prev_revenue),
            'growth_rate': round(growth_rate, 2),
            'average_daily_revenue': float(total_revenue) / max((end_date - start_date).days + 1, 1)
        }   
 
    # Academic Reports
    def generate_class_wise_report(self, class_id=None):
        """Generate class-wise performance and statistics report"""
        from models.classes import Class
        from models.student import Student
        from models.teacher import Teacher, TeacherClassAssignment
        
        if class_id:
            classes = [Class.query.get(class_id)]
        else:
            classes = Class.query.filter_by(school_id=self.school_id).all()
        
        class_reports = []
        
        for class_obj in classes:
            students = Student.query.filter_by(class_id=class_obj.id).all()
            
            # Get class teacher
            class_teacher_assignment = TeacherClassAssignment.query.filter_by(
                class_id=class_obj.id,
                is_class_teacher=True,
                is_active=True
            ).first()
            
            class_teacher = class_teacher_assignment.teacher if class_teacher_assignment else None
            
            # Calculate class statistics
            total_students = len(students)
            active_students = len([s for s in students if s.status.value == 'active'])
            
            # Mock performance data
            import random
            avg_performance = random.randint(70, 90)
            
            class_report = {
                'class_id': class_obj.id,
                'class_name': class_obj.get_display_name(),
                'class_teacher': class_teacher.user.name if class_teacher and class_teacher.user else 'Not Assigned',
                'total_students': total_students,
                'active_students': active_students,
                'capacity': class_obj.capacity,
                'utilization_rate': (total_students / max(class_obj.capacity, 1)) * 100,
                'average_performance': avg_performance,
                'academic_year': class_obj.academic_year,
                'subjects': self._get_class_subjects(class_obj.id)
            }
            
            class_reports.append(class_report)
        
        return {
            'class_reports': class_reports,
            'summary': {
                'total_classes': len(class_reports),
                'total_students': sum(r['total_students'] for r in class_reports),
                'average_class_size': sum(r['total_students'] for r in class_reports) / max(len(class_reports), 1),
                'overall_utilization': sum(r['utilization_rate'] for r in class_reports) / max(len(class_reports), 1)
            }
        }
    
    def generate_teacher_performance_report(self):
        """Generate teacher performance and workload report"""
        from models.teacher import Teacher, TeacherClassAssignment, TeacherSubjectAssignment
        from models.student import Student
        
        teachers = Teacher.query.filter_by(school_id=self.school_id).all()
        teacher_reports = []
        
        for teacher in teachers:
            # Get assigned classes and subjects
            class_assignments = TeacherClassAssignment.query.filter_by(
                teacher_id=teacher.id,
                is_active=True
            ).all()
            
            subject_assignments = TeacherSubjectAssignment.query.filter_by(
                teacher_id=teacher.id,
                is_active=True
            ).all()
            
            # Calculate workload
            total_students = 0
            for assignment in class_assignments:
                students_count = Student.query.filter_by(class_id=assignment.class_id).count()
                total_students += students_count
            
            # Mock performance metrics
            import random
            performance_score = random.randint(75, 95)
            
            teacher_report = {
                'teacher_id': teacher.id,
                'teacher_name': teacher.user.name if teacher.user else 'Unknown',
                'employee_id': teacher.employee_id,
                'designation': teacher.designation,
                'experience_years': teacher.experience_years,
                'classes_assigned': len(class_assignments),
                'subjects_assigned': len(subject_assignments),
                'total_students': total_students,
                'performance_score': performance_score,
                'status': teacher.status.value,
                'classes': [assignment.class_info.get_display_name() for assignment in class_assignments if assignment.class_info],
                'subjects': [assignment.subject.name for assignment in subject_assignments if assignment.subject]
            }
            
            teacher_reports.append(teacher_report)
        
        return {
            'teacher_reports': teacher_reports,
            'summary': {
                'total_teachers': len(teacher_reports),
                'average_workload': sum(r['total_students'] for r in teacher_reports) / max(len(teacher_reports), 1),
                'average_performance': sum(r['performance_score'] for r in teacher_reports) / max(len(teacher_reports), 1),
                'top_performers': sorted(teacher_reports, key=lambda x: x['performance_score'], reverse=True)[:5]
            }
        }
    
    # Administrative Reports
    def generate_staff_report(self):
        """Generate comprehensive staff report"""
        from models.teacher import Teacher, TeacherStatus
        from models.user import User, UserRole
        
        # Get all staff members
        teachers = Teacher.query.filter_by(school_id=self.school_id).all()
        admins = User.query.filter_by(school_id=self.school_id, role=UserRole.SCHOOL_ADMIN).all()
        
        # Teacher statistics
        teacher_stats = {
            'total': len(teachers),
            'active': len([t for t in teachers if t.status == TeacherStatus.ACTIVE]),
            'inactive': len([t for t in teachers if t.status == TeacherStatus.INACTIVE]),
            'on_leave': len([t for t in teachers if t.status == TeacherStatus.ON_LEAVE])
        }
        
        # Experience distribution
        experience_distribution = {'0-2': 0, '3-5': 0, '6-10': 0, '10+': 0}
        for teacher in teachers:
            exp = teacher.experience_years or 0
            if exp <= 2:
                experience_distribution['0-2'] += 1
            elif exp <= 5:
                experience_distribution['3-5'] += 1
            elif exp <= 10:
                experience_distribution['6-10'] += 1
            else:
                experience_distribution['10+'] += 1
        
        # Department distribution
        department_distribution = {}
        for teacher in teachers:
            dept = teacher.department or 'General'
            department_distribution[dept] = department_distribution.get(dept, 0) + 1
        
        return {
            'teacher_statistics': teacher_stats,
            'admin_count': len(admins),
            'experience_distribution': experience_distribution,
            'department_distribution': department_distribution,
            'staff_list': [
                {
                    'name': teacher.user.name if teacher.user else 'Unknown',
                    'employee_id': teacher.employee_id,
                    'designation': teacher.designation,
                    'department': teacher.department,
                    'experience': teacher.experience_years,
                    'status': teacher.status.value,
                    'joining_date': teacher.date_of_joining.isoformat() if teacher.date_of_joining else None
                }
                for teacher in teachers
            ]
        }    

    # Helper Methods
    def _get_monthly_enrollment_trend(self, start_date, end_date):
        """Get monthly enrollment trend data"""
        from models.student import Student
        
        if not start_date:
            start_date = date.today() - timedelta(days=365)
        if not end_date:
            end_date = date.today()
        
        monthly_data = []
        current_date = start_date.replace(day=1)
        
        while current_date <= end_date:
            month_end = (current_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            enrollments = Student.query.filter(
                Student.school_id == self.school_id,
                Student.admission_date >= current_date,
                Student.admission_date <= min(month_end, end_date)
            ).count()
            
            monthly_data.append({
                'month': current_date.strftime('%Y-%m'),
                'enrollments': enrollments
            })
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        return monthly_data
    
    def _get_daily_attendance_trend(self, start_date, end_date):
        """Get daily attendance trend data"""
        from models.attendance import Attendance, AttendanceStatus
        
        daily_data = []
        current_date = start_date
        
        while current_date <= end_date:
            total_attendance = Attendance.query.filter_by(
                school_id=self.school_id,
                date=current_date
            ).count()
            
            present_attendance = Attendance.query.filter_by(
                school_id=self.school_id,
                date=current_date,
                status=AttendanceStatus.PRESENT
            ).count()
            
            percentage = (present_attendance / max(total_attendance, 1)) * 100 if total_attendance > 0 else 0
            
            daily_data.append({
                'date': current_date.isoformat(),
                'total': total_attendance,
                'present': present_attendance,
                'percentage': round(percentage, 2)
            })
            
            current_date += timedelta(days=1)
        
        return daily_data
    
    def _calculate_outstanding_fees(self, class_filter=None):
        """Calculate outstanding fees summary"""
        from models.fee import StudentFeeStatus
        from models.student import Student
        
        query = StudentFeeStatus.query.filter_by(school_id=self.school_id)
        if class_filter:
            query = query.join(Student).filter(Student.class_id == class_filter)
        
        fee_statuses = query.all()
        
        total_outstanding = sum(status.remaining_amount for status in fee_statuses if status.remaining_amount > 0)
        students_with_dues = len([status for status in fee_statuses if status.remaining_amount > 0])
        overdue_amount = sum(status.remaining_amount for status in fee_statuses if status.is_overdue)
        
        return {
            'total_outstanding': float(total_outstanding),
            'students_with_dues': students_with_dues,
            'overdue_amount': float(overdue_amount)
        }
    
    def _get_class_subjects(self, class_id):
        """Get subjects for a class"""
        from models.classes import Subject
        
        subjects = Subject.query.filter_by(class_id=class_id).all()
        return [{'name': subject.name, 'code': subject.code} for subject in subjects]
    
    def _payment_to_dict(self, payment):
        """Convert payment to dictionary"""
        return {
            'id': payment.id,
            'student_name': payment.student.name if payment.student else 'Unknown',
            'amount': float(payment.amount),
            'payment_date': payment.payment_date.isoformat(),
            'payment_mode': payment.payment_mode.value if payment.payment_mode else 'Unknown',
            'receipt_no': payment.receipt_no
        }
    
    # Report Formatting Methods
    def _format_enrollment_report(self, data):
        """Format enrollment report for display"""
        return {
            'title': 'Student Enrollment Report',
            'summary': f"Total enrolled students: {data['summary']['total_enrolled']} ({data['summary']['active_students']} active, {data['summary']['inactive_students']} inactive)",
            'metrics': [
                {'label': 'Total Enrolled', 'value': data['summary']['total_enrolled']},
                {'label': 'Active Students', 'value': data['summary']['active_students']},
                {'label': 'Inactive Students', 'value': data['summary']['inactive_students']},
                {'label': 'Enrollment Rate', 'value': f"{data['summary']['enrollment_rate']:.1f}%"}
            ],
            'charts': [
                {
                    'title': 'Class-wise Distribution',
                    'type': 'bar',
                    'data': {
                        'labels': list(data['class_breakdown'].keys()),
                        'datasets': [{
                            'label': 'Students',
                            'data': [breakdown['total'] for breakdown in data['class_breakdown'].values()],
                            'backgroundColor': '#ff6b35'
                        }]
                    }
                },
                {
                    'title': 'Monthly Enrollment Trend',
                    'type': 'line',
                    'data': {
                        'labels': [item['month'] for item in data['monthly_trend']],
                        'datasets': [{
                            'label': 'New Enrollments',
                            'data': [item['enrollments'] for item in data['monthly_trend']],
                            'borderColor': '#3b82f6',
                            'backgroundColor': 'rgba(59, 130, 246, 0.1)'
                        }]
                    }
                }
            ],
            'table': {
                'headers': ['Class', 'Total', 'Active', 'Inactive'],
                'rows': [[class_name, str(breakdown['total']), str(breakdown['active']), str(breakdown['inactive'])] 
                        for class_name, breakdown in data['class_breakdown'].items()]
            },
            'recommendations': [
                {
                    'priority': 'medium',
                    'title': 'Monitor Inactive Students',
                    'description': 'Review inactive student records and follow up on re-enrollment possibilities.'
                }
            ]
        }
    
    def _format_performance_report(self, data):
        """Format performance report for display"""
        return {
            'title': 'Student Performance Analysis',
            'summary': f"Performance analysis for {len(data['performance_data'])} students across all classes",
            'metrics': [
                {'label': 'Total Students', 'value': len(data['performance_data'])},
                {'label': 'Average Performance', 'value': f"{sum(p['percentage'] for p in data['performance_data']) / len(data['performance_data']):.1f}%"},
                {'label': 'Top Performers', 'value': len([p for p in data['performance_data'] if p['percentage'] >= 90])},
                {'label': 'Classes Analyzed', 'value': len(data['class_averages'])}
            ],
            'charts': [
                {
                    'title': 'Class-wise Average Performance',
                    'type': 'bar',
                    'data': {
                        'labels': list(data['class_averages'].keys()),
                        'datasets': [{
                            'label': 'Average %',
                            'data': [avg['average'] for avg in data['class_averages'].values()],
                            'backgroundColor': '#22c55e'
                        }]
                    }
                }
            ],
            'table': {
                'headers': ['Student', 'Class', 'Overall Grade', 'Percentage'],
                'rows': [[p['student_name'], p['class'], p['overall_grade'], f"{p['percentage']}%"] 
                        for p in data['performance_data'][:20]]  # Limit to first 20
            },
            'recommendations': [
                {
                    'priority': 'high',
                    'title': 'Support Low Performers',
                    'description': 'Identify and provide additional support to students scoring below 70%.'
                }
            ]
        }
    
    def _format_attendance_report(self, data):
        """Format attendance report for display"""
        return {
            'title': 'Attendance Analysis Report',
            'summary': f"Attendance analysis from {data['summary']['date_range']['start']} to {data['summary']['date_range']['end']}. Overall attendance rate: {data['summary']['overall_percentage']}%",
            'metrics': [
                {'label': 'Total Records', 'value': data['summary']['total_records']},
                {'label': 'Present Records', 'value': data['summary']['present_records']},
                {'label': 'Absent Records', 'value': data['summary']['absent_records']},
                {'label': 'Overall Rate', 'value': f"{data['summary']['overall_percentage']}%"}
            ],
            'charts': [
                {
                    'title': 'Daily Attendance Trend',
                    'type': 'line',
                    'data': {
                        'labels': [item['date'] for item in data['daily_trend']],
                        'datasets': [{
                            'label': 'Attendance %',
                            'data': [item['percentage'] for item in data['daily_trend']],
                            'borderColor': '#8b5cf6',
                            'backgroundColor': 'rgba(139, 92, 246, 0.1)'
                        }]
                    }
                },
                {
                    'title': 'Class-wise Attendance',
                    'type': 'bar',
                    'data': {
                        'labels': list(data['class_attendance'].keys()),
                        'datasets': [{
                            'label': 'Attendance %',
                            'data': [att['percentage'] for att in data['class_attendance'].values()],
                            'backgroundColor': '#06b6d4'
                        }]
                    }
                }
            ],
            'table': {
                'headers': ['Student', 'Total Days', 'Present', 'Absent', 'Percentage'],
                'rows': [[att['student'].name if att['student'] else 'Unknown', 
                         str(att['total_days']), str(att['present_days']), 
                         str(att['absent_days']), f"{att['percentage']:.1f}%"] 
                        for att in data['student_attendance'][:20]]
            },
            'recommendations': [
                {
                    'priority': 'high' if data['summary']['overall_percentage'] < 85 else 'medium',
                    'title': 'Improve Attendance Rate',
                    'description': 'Focus on students with attendance below 80% and implement intervention strategies.'
                }
            ]
        }
    
    def _format_demographics_report(self, data):
        """Format demographics report for display"""
        return {
            'title': 'Student Demographics Report',
            'summary': f"Demographic analysis of {data['total_students']} students across various categories",
            'metrics': [
                {'label': 'Total Students', 'value': data['total_students']},
                {'label': 'Gender Categories', 'value': len(data['gender_distribution'])},
                {'label': 'Age Groups', 'value': len(data['age_distribution'])},
                {'label': 'Geographic Locations', 'value': len(data['geographic_distribution'])}
            ],
            'charts': [
                {
                    'title': 'Gender Distribution',
                    'type': 'pie',
                    'data': {
                        'labels': list(data['gender_distribution'].keys()),
                        'datasets': [{
                            'data': list(data['gender_distribution'].values()),
                            'backgroundColor': ['#3b82f6', '#ec4899', '#10b981']
                        }]
                    }
                },
                {
                    'title': 'Age Distribution',
                    'type': 'bar',
                    'data': {
                        'labels': list(data['age_distribution'].keys()),
                        'datasets': [{
                            'label': 'Students',
                            'data': list(data['age_distribution'].values()),
                            'backgroundColor': '#f59e0b'
                        }]
                    }
                }
            ],
            'table': {
                'headers': ['Category', 'Count', 'Percentage'],
                'rows': [
                    ['Male', str(data['gender_distribution'].get('male', 0)), f"{(data['gender_distribution'].get('male', 0) / data['total_students'] * 100):.1f}%"],
                    ['Female', str(data['gender_distribution'].get('female', 0)), f"{(data['gender_distribution'].get('female', 0) / data['total_students'] * 100):.1f}%"]
                ]
            },
            'recommendations': [
                {
                    'priority': 'low',
                    'title': 'Maintain Diversity',
                    'description': 'Continue efforts to maintain balanced demographics across all categories.'
                }
            ]
        }
    
    def _format_fee_collection_report(self, data):
        """Format fee collection report for display"""
        return {
            'title': 'Fee Collection Report',
            'summary': f"Total collected: ₹{data['summary']['total_collected']:,.2f} from {data['summary']['total_transactions']} transactions",
            'metrics': [
                {'label': 'Total Collected', 'value': f"₹{data['summary']['total_collected']:,.0f}"},
                {'label': 'Total Transactions', 'value': data['summary']['total_transactions']},
                {'label': 'Average Transaction', 'value': f"₹{data['summary']['average_transaction']:,.0f}"},
                {'label': 'Outstanding Amount', 'value': f"₹{data['outstanding_fees']['total_outstanding']:,.0f}"}
            ],
            'charts': [
                {
                    'title': 'Payment Mode Distribution',
                    'type': 'pie',
                    'data': {
                        'labels': list(data['payment_modes'].keys()),
                        'datasets': [{
                            'data': list(data['payment_modes'].values()),
                            'backgroundColor': ['#22c55e', '#3b82f6', '#f59e0b', '#ef4444']
                        }]
                    }
                },
                {
                    'title': 'Daily Collection Trend',
                    'type': 'line',
                    'data': {
                        'labels': list(data['daily_collections'].keys()),
                        'datasets': [{
                            'label': 'Amount (₹)',
                            'data': list(data['daily_collections'].values()),
                            'borderColor': '#22c55e',
                            'backgroundColor': 'rgba(34, 197, 94, 0.1)'
                        }]
                    }
                }
            ],
            'table': {
                'headers': ['Date', 'Student', 'Amount', 'Mode', 'Receipt No'],
                'rows': [[p['payment_date'], p['student_name'], f"₹{p['amount']:,.0f}", 
                         p['payment_mode'], p['receipt_no']] for p in data['recent_payments']]
            },
            'recommendations': [
                {
                    'priority': 'medium',
                    'title': 'Follow Up on Outstanding Fees',
                    'description': f"₹{data['outstanding_fees']['total_outstanding']:,.0f} is still outstanding from {data['outstanding_fees']['students_with_dues']} students."
                }
            ]
        }
    
    def _format_outstanding_fees_report(self, data):
        """Format outstanding fees report for display"""
        return {
            'title': 'Outstanding Fees Report',
            'summary': f"₹{data['summary']['total_outstanding']:,.2f} outstanding from {data['summary']['students_with_dues']} students",
            'metrics': [
                {'label': 'Total Outstanding', 'value': f"₹{data['summary']['total_outstanding']:,.0f}"},
                {'label': 'Students with Dues', 'value': data['summary']['students_with_dues']},
                {'label': 'Overdue Students', 'value': data['summary']['overdue_students']},
                {'label': 'Collection Rate', 'value': '75%'}  # Mock data
            ],
            'charts': [
                {
                    'title': 'Class-wise Outstanding',
                    'type': 'bar',
                    'data': {
                        'labels': list(data['class_outstanding'].keys()),
                        'datasets': [{
                            'label': 'Amount (₹)',
                            'data': [cls['amount'] for cls in data['class_outstanding'].values()],
                            'backgroundColor': '#ef4444'
                        }]
                    }
                }
            ],
            'table': {
                'headers': ['Student', 'Class', 'Total Fee', 'Paid', 'Outstanding', 'Status'],
                'rows': [[s['student_name'], s['class'], f"₹{s['total_fee']:,.0f}", 
                         f"₹{s['paid_amount']:,.0f}", f"₹{s['remaining_amount']:,.0f}",
                         'Overdue' if s['is_overdue'] else 'Pending'] 
                        for s in data['outstanding_students'][:20]]
            },
            'recommendations': [
                {
                    'priority': 'high',
                    'title': 'Immediate Follow-up Required',
                    'description': f"Contact {data['summary']['overdue_students']} overdue students immediately for payment collection."
                }
            ]
        }
    
    def _format_revenue_report(self, data):
        """Format revenue report for display"""
        return {
            'title': f"Revenue Report - {data['month']}",
            'summary': f"Total revenue: ₹{data['total_revenue']:,.2f} from {data['total_transactions']} transactions",
            'metrics': [
                {'label': 'Total Revenue', 'value': f"₹{data['total_revenue']:,.0f}"},
                {'label': 'Total Transactions', 'value': data['total_transactions']},
                {'label': 'Growth Rate', 'value': f"{data['growth_rate']}%", 'change': data['growth_rate']},
                {'label': 'Daily Average', 'value': f"₹{data['average_daily_revenue']:,.0f}"}
            ],
            'charts': [
                {
                    'title': 'Daily Revenue Trend',
                    'type': 'line',
                    'data': {
                        'labels': list(data['daily_revenue'].keys()),
                        'datasets': [{
                            'label': 'Revenue (₹)',
                            'data': list(data['daily_revenue'].values()),
                            'borderColor': '#8b5cf6',
                            'backgroundColor': 'rgba(139, 92, 246, 0.1)'
                        }]
                    }
                }
            ],
            'table': {
                'headers': ['Day', 'Revenue', 'Transactions'],
                'rows': [[str(day), f"₹{amount:,.0f}", '1'] for day, amount in data['daily_revenue'].items()]
            },
            'recommendations': [
                {
                    'priority': 'medium',
                    'title': 'Revenue Growth Analysis',
                    'description': f"Revenue {'increased' if data['growth_rate'] >= 0 else 'decreased'} by {abs(data['growth_rate'])}% compared to previous month."
                }
            ]
        }
    
    # Placeholder formatting methods for other report types
    def _format_expense_report(self, data):
        return {'title': 'Expense Report', 'summary': 'Expense tracking feature coming soon.'}
    
    def _format_class_performance_report(self, data):
        return {'title': 'Class Performance Report', 'summary': f"Analysis of {data['summary']['total_classes']} classes"}
    
    def _format_subject_analysis_report(self, data):
        return {'title': 'Subject Analysis Report', 'summary': 'Subject-wise analysis feature coming soon.'}
    
    def _format_teacher_performance_report(self, data):
        return {'title': 'Teacher Performance Report', 'summary': f"Performance analysis of {data['summary']['total_teachers']} teachers"}
    
    def _format_curriculum_report(self, data):
        return {'title': 'Curriculum Progress Report', 'summary': 'Curriculum tracking feature coming soon.'}
    
    def _format_staff_report(self, data):
        return {'title': 'Staff Management Report', 'summary': f"Staff analysis: {data['teacher_statistics']['total']} teachers, {data['admin_count']} admins"}
    
    def _format_infrastructure_report(self, data):
        return {'title': 'Infrastructure Report', 'summary': 'Infrastructure management feature coming soon.'}
    
    def _format_compliance_report(self, data):
        return {'title': 'Compliance Report', 'summary': 'Compliance tracking feature coming soon.'}
    
    def _format_activity_report(self, data):
        return {'title': 'System Activity Report', 'summary': 'Activity logging feature coming soon.'}

    # Export Functions
    def export_to_pdf(self, report_data, filters):
        """Export report to PDF format"""
        from utils.pdf_generator import PDFGenerator
        
        pdf_generator = PDFGenerator()
        pdf_content = pdf_generator.generate_report_pdf(report_data, filters)
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return pdf_content, filename
    
    def export_to_excel(self, report_data, filters):
        """Export report to Excel format"""
        # This would require openpyxl library
        # For now, return CSV format
        csv_content, _ = self.export_to_csv(report_data, filters)
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return csv_content.encode('utf-8'), filename
    
    def export_to_csv(self, report_data, filters):
        """Export report data to CSV format"""
        output = io.StringIO()
        
        # Write report header
        output.write(f"Report: {report_data.get('title', 'School Report')}\n")
        output.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        output.write(f"Summary: {report_data.get('summary', '')}\n\n")
        
        # Write metrics if available
        if 'metrics' in report_data:
            output.write("Key Metrics:\n")
            for metric in report_data['metrics']:
                output.write(f"{metric['label']}: {metric['value']}\n")
            output.write("\n")
        
        # Write table data if available
        if 'table' in report_data and report_data['table']:
            table = report_data['table']
            writer = csv.writer(output)
            writer.writerow(table['headers'])
            writer.writerows(table['rows'])
        
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return output.getvalue(), filename
    
    def generate_yearly_summary(self, year=None):
        """Generate comprehensive yearly summary report"""
        if not year:
            year = date.today().year
        
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        
        # Get all data for the year
        enrollment_data = self.generate_enrollment_report(start_date, end_date)
        fee_data = self.generate_fee_collection_report(start_date, end_date)
        attendance_data = self.generate_attendance_report(start_date, end_date)
        
        # Monthly breakdown
        monthly_summary = []
        for month in range(1, 13):
            month_start = date(year, month, 1)
            if month == 12:
                month_end = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = date(year, month + 1, 1) - timedelta(days=1)
            
            month_revenue = self.generate_monthly_revenue_report(year, month)
            
            monthly_summary.append({
                'month': month_start.strftime('%B %Y'),
                'revenue': month_revenue['total_revenue'],
                'transactions': month_revenue['total_transactions']
            })
        
        return {
            'year': year,
            'enrollment_summary': enrollment_data['summary'],
            'financial_summary': fee_data['summary'],
            'attendance_summary': attendance_data['summary'],
            'monthly_breakdown': monthly_summary,
            'total_revenue': sum(m['revenue'] for m in monthly_summary),
            'total_transactions': sum(m['transactions'] for m in monthly_summary)
        }