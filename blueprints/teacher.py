"""
Teacher Blueprint - Handles teacher-specific functionality
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from werkzeug.utils import secure_filename
from extensions import db
from models.user import User
from models.teacher import Teacher, TeacherClassAssignment, TeacherSubjectAssignment
from models.assignment import Assignment, AssignmentStatus
from models.student import Student
from models.attendance import Attendance, AttendanceStatus
from models.classes import Class, Subject
from utils.auth import login_required, role_required
from utils.helpers import allowed_file, save_uploaded_file
from datetime import datetime, date
import os

teacher_bp = Blueprint('teacher', __name__)


@teacher_bp.route('/dashboard')
@role_required('teacher')
def dashboard():
    """Teacher dashboard"""
    user = User.query.get(session['user_id'])
    teacher = Teacher.query.filter_by(user_id=user.id).first()
    
    if not teacher:
        flash('Teacher profile not found. Please contact administrator.', 'error')
        return redirect(url_for('auth.logout'))
    
    # Get assigned classes
    assigned_classes = teacher.get_assigned_classes()
    
    # Get recent assignments
    # AssignmentStatus already imported above
    recent_assignments = Assignment.query.filter_by(
        teacher_id=teacher.id,
        status=AssignmentStatus.PUBLISHED
    ).order_by(Assignment.created_at.desc()).limit(5).all()
    
    # Calculate statistics
    total_students = 0
    for class_info in assigned_classes:
        total_students += len(class_info.students)
    
    # Get today's attendance summary
    today = date.today()
    today_attendance = []
    for class_info in assigned_classes:
        attendance_count = Attendance.query.filter_by(
            class_id=class_info.id,
            date=today
        ).count()
        
        today_attendance.append({
            'class': class_info,
            'marked': attendance_count,
            'total': len(class_info.students)
        })
    
    return render_template('teacher/dashboard.html',
                         user=user,
                         teacher=teacher,
                         assigned_classes=assigned_classes,
                         recent_assignments=recent_assignments,
                         total_students=total_students,
                         today_attendance=today_attendance)


@teacher_bp.route('/profile', methods=['GET', 'POST'])
@role_required('teacher')
def profile():
    """Teacher profile management"""
    user = User.query.get(session['user_id'])
    teacher = Teacher.query.filter_by(user_id=user.id).first()
    
    if not teacher:
        flash('Teacher profile not found. Please contact administrator.', 'error')
        return redirect(url_for('auth.logout'))
    
    if request.method == 'POST':
        try:
            # Update user information
            user.name = request.form.get('name')
            user.email = request.form.get('email')
            
            # Update teacher information
            teacher.phone = request.form.get('phone')
            teacher.emergency_contact = request.form.get('emergency_contact')
            teacher.address = request.form.get('address')
            teacher.qualification = request.form.get('qualification')
            teacher.bio = request.form.get('bio')
            
            # Handle date fields
            if request.form.get('date_of_birth'):
                teacher.date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date()
            
            # Handle photo upload
            if 'photo' in request.files:
                file = request.files['photo']
                if file and file.filename and allowed_file(file.filename, ['png', 'jpg', 'jpeg']):
                    filename = save_uploaded_file(file, 'teachers')
                    teacher.photo_url = filename
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'error')
    
    return render_template('teacher/profile.html', user=user, teacher=teacher)


@teacher_bp.route('/classes')
@role_required('teacher')
def classes():
    """View assigned classes"""
    user = User.query.get(session['user_id'])
    teacher = Teacher.query.filter_by(user_id=user.id).first()
    
    if not teacher:
        flash('Teacher profile not found. Please contact administrator.', 'error')
        return redirect(url_for('auth.logout'))
    
    # Get class assignments with details
    class_assignments = TeacherClassAssignment.query.filter_by(
        teacher_id=teacher.id,
        is_active=True
    ).all()
    
    # Get subject assignments
    subject_assignments = TeacherSubjectAssignment.query.filter_by(
        teacher_id=teacher.id,
        is_active=True
    ).all()
    
    return render_template('teacher/classes.html',
                         user=user,
                         teacher=teacher,
                         class_assignments=class_assignments,
                         subject_assignments=subject_assignments,
                         today=date.today())


@teacher_bp.route('/attendance')
@role_required('teacher')
def attendance():
    """Teacher attendance interface"""
    user = User.query.get(session['user_id'])
    teacher = Teacher.query.filter_by(user_id=user.id).first()
    
    if not teacher:
        flash('Teacher profile not found. Please contact administrator.', 'error')
        return redirect(url_for('auth.logout'))
    
    # Get assigned classes
    assigned_classes = teacher.get_assigned_classes()
    
    selected_date = None
    selected_class_id = None
    selected_class = None
    students = []
    attendance_data = {}
    
    # Handle GET request with date and class selection
    if request.args.get('date') and request.args.get('class_id'):
        try:
            selected_date = datetime.strptime(request.args.get('date'), '%Y-%m-%d').date()
            selected_class_id = int(request.args.get('class_id'))
            
            # Verify teacher has access to this class
            class_assignment = TeacherClassAssignment.query.filter_by(
                teacher_id=teacher.id,
                class_id=selected_class_id,
                is_active=True
            ).first()
            
            if not class_assignment:
                flash('You do not have access to this class.', 'error')
                return redirect(url_for('teacher.attendance'))
            
            selected_class = class_assignment.class_info
            students = Student.query.filter_by(class_id=selected_class_id).all()
            
            # Get existing attendance data
            existing_attendance = Attendance.query.filter_by(
                class_id=selected_class_id,
                date=selected_date
            ).all()
            
            for att in existing_attendance:
                attendance_data[att.student_id] = att.status.value
                
        except Exception as e:
            flash(f'Error loading attendance data: {str(e)}', 'error')
    
    return render_template('teacher/attendance.html',
                         user=user,
                         teacher=teacher,
                         assigned_classes=assigned_classes,
                         selected_date=selected_date,
                         selected_class_id=selected_class_id,
                         selected_class=selected_class,
                         students=students,
                         attendance_data=attendance_data,
                         today=date.today())


@teacher_bp.route('/mark_attendance', methods=['POST'])
@role_required('teacher')
def mark_attendance():
    """Mark attendance for assigned class"""
    user = User.query.get(session['user_id'])
    teacher = Teacher.query.filter_by(user_id=user.id).first()
    
    if not teacher:
        flash('Teacher profile not found. Please contact administrator.', 'error')
        return redirect(url_for('auth.logout'))
    
    try:
        selected_date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        selected_class_id = int(request.form.get('class_id'))
        
        # Verify teacher has access to this class
        class_assignment = TeacherClassAssignment.query.filter_by(
            teacher_id=teacher.id,
            class_id=selected_class_id,
            is_active=True
        ).first()
        
        if not class_assignment:
            flash('You do not have access to this class.', 'error')
            return redirect(url_for('teacher.attendance'))
        
        # Get all students in the class
        students = Student.query.filter_by(class_id=selected_class_id).all()
        
        # Process attendance data
        for student in students:
            attendance_status = request.form.get(f'attendance_{student.id}')
            if attendance_status:
                # Check if attendance already exists
                existing_attendance = Attendance.query.filter_by(
                    student_id=student.id,
                    date=selected_date
                ).first()
                
                if existing_attendance:
                    existing_attendance.status = AttendanceStatus(attendance_status)
                    existing_attendance.marked_by = user.id
                    existing_attendance.marked_at = datetime.utcnow()
                else:
                    attendance = Attendance(
                        school_id=teacher.school_id,
                        student_id=student.id,
                        class_id=selected_class_id,
                        date=selected_date,
                        status=AttendanceStatus(attendance_status),
                        marked_by=user.id
                    )
                    db.session.add(attendance)
        
        db.session.commit()
        flash('Attendance marked successfully!', 'success')
        
        # Send notifications for absent students
        try:
            from utils.notification_service import NotificationService
            notification_service = NotificationService(teacher.school_id)
            
            for student in students:
                attendance_status = request.form.get(f'attendance_{student.id}')
                if attendance_status in ['absent', 'leave']:
                    notification_service.send_attendance_alert(student, attendance_status, selected_date)
        except Exception as e:
            print(f"Notification error: {e}")
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error marking attendance: {str(e)}', 'error')
    
    return redirect(url_for('teacher.attendance', 
                          date=request.form.get('date'),
                          class_id=request.form.get('class_id')))


@teacher_bp.route('/assignments')
@role_required('teacher')
def assignments():
    """Assignment management dashboard for teachers"""
    user = User.query.get(session['user_id'])
    teacher = Teacher.query.filter_by(user_id=user.id).first_or_404()
    
    from models.assignment import Assignment, AssignmentStatus, SubmissionStatus
    from models.classes import Class, Subject
    from services.assignment_service import AssignmentService
    
    assignment_service = AssignmentService(teacher.school_id)
    
    # Get teacher's assignments
    assignments = assignment_service.get_teacher_assignments(teacher.id)
    
    # Get assignment statistics
    assignment_stats = assignment_service.get_assignment_statistics(teacher.id)
    
    # Get teacher's classes and subjects
    teacher_classes = Class.query.join(TeacherClassAssignment).filter(
        TeacherClassAssignment.teacher_id == teacher.id,
        TeacherClassAssignment.is_active == True
    ).all()
    
    teacher_subjects = Subject.query.join(TeacherSubjectAssignment).filter(
        TeacherSubjectAssignment.teacher_id == teacher.id,
        TeacherSubjectAssignment.is_active == True
    ).distinct().all()
    
    return render_template('teacher/assignments.html',
                         user=user,
                         teacher=teacher,
                         assignments=assignments,
                         assignment_stats=assignment_stats,
                         teacher_classes=teacher_classes,
                         teacher_subjects=teacher_subjects)


@teacher_bp.route('/assignments/create', methods=['POST'])
@role_required('teacher')
def create_assignment():
    """Create new assignment"""
    user = User.query.get(session['user_id'])
    teacher = Teacher.query.filter_by(user_id=user.id).first_or_404()
    
    from services.assignment_service import AssignmentService
    
    try:
        assignment_service = AssignmentService(teacher.school_id)
        
        # Get form data
        assignment_data = {
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'instructions': request.form.get('instructions'),
            'class_id': int(request.form.get('class_id')),
            'subject_id': int(request.form.get('subject_id')) if request.form.get('subject_id') else None,
            'type': request.form.get('type', 'assignment'),
            'status': request.form.get('status', 'published'),
            'due_date': request.form.get('due_date'),
            'max_marks': request.form.get('max_marks', 100),
            'allow_late_submission': request.form.get('allow_late_submission') == 'on',
            'allow_multiple_submissions': request.form.get('allow_multiple_submissions') == 'on'
        }
        
        # Verify teacher has access to this class
        class_assignment = TeacherClassAssignment.query.filter_by(
            teacher_id=teacher.id,
            class_id=assignment_data['class_id'],
            is_active=True
        ).first()
        
        if not class_assignment:
            return jsonify({'success': False, 'message': 'You do not have access to this class.'})
        
        # Get uploaded files
        files = request.files.getlist('files')
        
        # Create assignment
        result = assignment_service.create_assignment(teacher.id, assignment_data, files)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@teacher_bp.route('/assignments/<int:assignment_id>')
@role_required('teacher')
def view_assignment(assignment_id):
    """View assignment details"""
    user = User.query.get(session['user_id'])
    teacher = Teacher.query.filter_by(user_id=user.id).first_or_404()
    
    from models.assignment import Assignment
    
    assignment = Assignment.query.filter_by(
        id=assignment_id,
        teacher_id=teacher.id,
        school_id=teacher.school_id
    ).first_or_404()
    
    return render_template('teacher/view_assignment.html',
                         user=user,
                         teacher=teacher,
                         assignment=assignment)


@teacher_bp.route('/assignments/<int:assignment_id>/submissions')
@role_required('teacher')
def assignment_submissions(assignment_id):
    """View assignment submissions"""
    user = User.query.get(session['user_id'])
    teacher = Teacher.query.filter_by(user_id=user.id).first_or_404()
    
    from models.assignment import Assignment
    from services.assignment_service import AssignmentService
    
    assignment_service = AssignmentService(teacher.school_id)
    
    assignment = Assignment.query.filter_by(
        id=assignment_id,
        teacher_id=teacher.id,
        school_id=teacher.school_id
    ).first_or_404()
    
    submissions = assignment_service.get_assignment_submissions(assignment_id, teacher.id)
    
    return render_template('teacher/assignment_submissions.html',
                         user=user,
                         teacher=teacher,
                         assignment=assignment,
                         submissions=submissions)


@teacher_bp.route('/assignments/<int:assignment_id>/delete', methods=['POST'])
@role_required('teacher')
def delete_assignment(assignment_id):
    """Delete assignment"""
    user = User.query.get(session['user_id'])
    teacher = Teacher.query.filter_by(user_id=user.id).first_or_404()
    
    from services.assignment_service import AssignmentService
    
    assignment_service = AssignmentService(teacher.school_id)
    result = assignment_service.delete_assignment(assignment_id, teacher.id)
    
    return jsonify(result)


@teacher_bp.route('/study_materials')
@role_required('teacher')
def study_materials():
    """Study materials management"""
    user = User.query.get(session['user_id'])
    teacher = Teacher.query.filter_by(user_id=user.id).first_or_404()
    
    from services.assignment_service import AssignmentService
    from models.classes import Class, Subject
    
    assignment_service = AssignmentService(teacher.school_id)
    
    # Get study materials
    materials = assignment_service.get_study_materials(teacher_id=teacher.id)
    
    # Get teacher's classes and subjects
    teacher_classes = Class.query.join(TeacherClassAssignment).filter(
        TeacherClassAssignment.teacher_id == teacher.id,
        TeacherClassAssignment.is_active == True
    ).all()
    
    teacher_subjects = Subject.query.join(TeacherSubjectAssignment).filter(
        TeacherSubjectAssignment.teacher_id == teacher.id,
        TeacherSubjectAssignment.is_active == True
    ).distinct().all()
    
    return render_template('teacher/study_materials.html',
                         user=user,
                         teacher=teacher,
                         materials=materials,
                         teacher_classes=teacher_classes,
                         teacher_subjects=teacher_subjects)


@teacher_bp.route('/study_materials/create', methods=['POST'])
@role_required('teacher')
def create_study_material():
    """Create study material"""
    user = User.query.get(session['user_id'])
    teacher = Teacher.query.filter_by(user_id=user.id).first_or_404()
    
    from services.assignment_service import AssignmentService
    
    try:
        assignment_service = AssignmentService(teacher.school_id)
        
        # Get form data
        material_data = {
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'content': request.form.get('content'),
            'class_id': int(request.form.get('class_id')) if request.form.get('class_id') else None,
            'subject_id': int(request.form.get('subject_id')) if request.form.get('subject_id') else None,
            'category': request.form.get('category', 'general'),
            'tags': request.form.get('tags'),
            'is_public': request.form.get('is_public') == 'on',
            'is_downloadable': request.form.get('is_downloadable') == 'on'
        }
        
        # Get uploaded files
        files = request.files.getlist('files')
        
        # Create study material
        result = assignment_service.create_study_material(teacher.id, material_data, files)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@teacher_bp.route('/edit_profile', methods=['GET', 'POST'])
@role_required('teacher')
def edit_profile():
    """Edit teacher profile"""
    user = User.query.get(session['user_id'])
    teacher = Teacher.query.filter_by(user_id=user.id).first()
    
    if not teacher:
        flash('Teacher profile not found. Please contact administrator.', 'error')
        return redirect(url_for('auth.logout'))
    
    if request.method == 'POST':
        try:
            # Update user information
            user.name = request.form.get('name')
            user.email = request.form.get('email')
            
            # Update teacher information
            teacher.phone = request.form.get('phone')
            teacher.address = request.form.get('address')
            teacher.designation = request.form.get('designation')
            teacher.department = request.form.get('department')
            teacher.qualification = request.form.get('qualification')
            teacher.experience_years = int(request.form.get('experience_years')) if request.form.get('experience_years') else None
            teacher.blood_group = request.form.get('blood_group')
            teacher.gender = request.form.get('gender')
            teacher.emergency_contact_name = request.form.get('emergency_contact_name')
            teacher.emergency_contact_phone = request.form.get('emergency_contact_phone')
            teacher.emergency_contact_relation = request.form.get('emergency_contact_relation')
            
            # Handle date fields
            if request.form.get('date_of_birth'):
                teacher.date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date()
            if request.form.get('date_of_joining'):
                teacher.date_of_joining = datetime.strptime(request.form.get('date_of_joining'), '%Y-%m-%d').date()
            
            # Handle photo upload
            if 'photo' in request.files:
                file = request.files['photo']
                if file and file.filename and allowed_file(file.filename, ['png', 'jpg', 'jpeg']):
                    filename = save_uploaded_file(file, 'teachers')
                    teacher.photo_url = filename
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('teacher.profile'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'error')
    
    return render_template('teacher/edit_profile.html', user=user, teacher=teacher, today=date.today())


@teacher_bp.route('/change_password', methods=['GET', 'POST'])
@role_required('teacher')
def change_password():
    """Change teacher password"""
    user = User.query.get(session['user_id'])
    teacher = Teacher.query.filter_by(user_id=user.id).first()
    
    if not teacher:
        flash('Teacher profile not found. Please contact administrator.', 'error')
        return redirect(url_for('auth.logout'))
    
    if request.method == 'POST':
        try:
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            # Verify current password
            if not user.check_password(current_password):
                flash('Current password is incorrect.', 'error')
                return render_template('teacher/change_password.html', user=user, teacher=teacher)
            
            # Verify new passwords match
            if new_password != confirm_password:
                flash('New passwords do not match.', 'error')
                return render_template('teacher/change_password.html', user=user, teacher=teacher)
            
            # Update password
            user.set_password(new_password)
            db.session.commit()
            
            flash('Password changed successfully!', 'success')
            return redirect(url_for('teacher.profile'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error changing password: {str(e)}', 'error')
    
    return render_template('teacher/change_password.html', user=user, teacher=teacher)


@teacher_bp.route('/schedule')
@role_required('teacher')
def schedule():
    """View teacher schedule"""
    user = User.query.get(session['user_id'])
    teacher = Teacher.query.filter_by(user_id=user.id).first()
    
    if not teacher:
        flash('Teacher profile not found. Please contact administrator.', 'error')
        return redirect(url_for('auth.logout'))
    
    # Get assigned classes for schedule context
    assigned_classes = teacher.get_assigned_classes()
    
    # Mock schedule data - in real implementation, this would come from a Schedule model
    schedule = {}
    todays_schedule = []
    
    # Calculate week dates
    from datetime import timedelta
    today = date.today()
    current_week_start = today - timedelta(days=today.weekday())
    current_week_end = current_week_start + timedelta(days=6)
    
    return render_template('teacher/schedule.html',
                         user=user,
                         teacher=teacher,
                         assigned_classes=assigned_classes,
                         schedule=schedule,
                         todays_schedule=todays_schedule,
                         today=today,
                         current_week_start=current_week_start,
                         current_week_end=current_week_end,
                         total_periods=25,
                         classes_count=len(assigned_classes),
                         subjects_count=len(teacher.get_assigned_subjects()),
                         free_periods=8)


@teacher_bp.route('/reports')
@role_required('teacher')
def reports():
    """View teacher reports and analytics"""
    user = User.query.get(session['user_id'])
    teacher = Teacher.query.filter_by(user_id=user.id).first()
    
    if not teacher:
        flash('Teacher profile not found. Please contact administrator.', 'error')
        return redirect(url_for('auth.logout'))
    
    # Get assigned classes for context
    assigned_classes = teacher.get_assigned_classes()
    
    # Calculate basic statistics
    total_students = sum(len(class_info.students) for class_info in assigned_classes)
    
    # Mock data - in real implementation, calculate from actual data
    stats = {
        'total_reports': 12,
        'avg_attendance': 92,
        'assignments_graded': 45,
        'avg_performance': 78
    }
    
    return render_template('teacher/reports.html',
                         user=user,
                         teacher=teacher,
                         assigned_classes=assigned_classes,
                         total_students=total_students,
                         **stats)


@teacher_bp.route('/api/subjects/<int:class_id>')
@role_required('teacher')
def get_class_subjects(class_id):
    """API endpoint to get subjects for a class"""
    user = User.query.get(session['user_id'])
    teacher = Teacher.query.filter_by(user_id=user.id).first()
    
    if not teacher:
        return jsonify({'error': 'Teacher profile not found'}), 404
    
    # Verify teacher has access to this class
    class_assignment = TeacherClassAssignment.query.filter_by(
        teacher_id=teacher.id,
        class_id=class_id,
        is_active=True
    ).first()
    
    if not class_assignment:
        return jsonify({'error': 'Access denied'}), 403
    
    # Get subjects for this class that the teacher is assigned to
    subject_assignments = TeacherSubjectAssignment.query.filter_by(
        teacher_id=teacher.id,
        class_id=class_id,
        is_active=True
    ).all()
    
    subjects = []
    for assignment in subject_assignments:
        subjects.append({
            'id': assignment.subject.id,
            'name': assignment.subject.name,
            'code': assignment.subject.code
        })
    
    return jsonify({'subjects': subjects})