"""Files Blueprint.

Handles secure serving and uploading of files, such as student photos,
teacher photos, assignments, and receipts. It implements role-based access
control to ensure that users can only access files they are authorized to
view.
"""
from flask import Blueprint, request, abort, session, current_app
from models.user import User, UserRole
from models.student import Student
from models.teacher import Teacher
from models.assignment import Assignment, AssignmentStatus, AssignmentType
from models.classes import Class
from services.file_upload_service import FileUploadService
from utils.auth import login_required
import os

files_bp = Blueprint('files', __name__)


@files_bp.route('/student/photo/<int:student_id>')
@login_required
def serve_student_photo(student_id):
    """Serves a student's photo with strict access control.

    Access is granted based on the user's role and their relationship to the
    student (e.g., a teacher in the same school, or the student themselves).

    Args:
        student_id (int): The ID of the student.

    Returns:
        File: The student's photo, or a 403/404 error.
    """
    user = User.query.get(session['user_id'])
    
    # Get student
    student = Student.query.get_or_404(student_id)
    
    # Access control
    if user.role == UserRole.SUPER_ADMIN:
        # Super admin can access any student photo
        pass
    elif user.role == UserRole.SCHOOL_ADMIN:
        # School admin can access students from their school
        if student.school_id != user.school_id:
            abort(403)
    elif user.role == UserRole.TEACHER:
        # Teachers can access students from their school
        teacher = Teacher.query.filter_by(user_id=user.id).first()
        if not teacher or student.school_id != teacher.school_id:
            abort(403)
    elif user.role == UserRole.STUDENT:
        # Students can only access their own photo
        student_profile = Student.query.filter_by(user_id=user.id).first()
        if not student_profile or student_profile.id != student_id:
            abort(403)
    else:
        abort(403)
    
    # Check if student has photo
    if not student.photo_url:
        abort(404)
    
    # Serve file
    service = FileUploadService()
    return service.serve_file(student.photo_url)


@files_bp.route('/teacher/photo/<int:teacher_id>')
@login_required
def serve_teacher_photo(teacher_id):
    """Serves a teacher's photo with access control.

    Access rules are based on the user's role and their school affiliation.

    Args:
        teacher_id (int): The ID of the teacher.

    Returns:
        File: The teacher's photo, or a 403/404 error.
    """
    user = User.query.get(session['user_id'])
    
    # Get teacher
    teacher = Teacher.query.get_or_404(teacher_id)
    
    # Access control
    if user.role == UserRole.SUPER_ADMIN:
        # Super admin can access any teacher photo
        pass
    elif user.role == UserRole.SCHOOL_ADMIN:
        # School admin can access teachers from their school
        if teacher.school_id != user.school_id:
            abort(403)
    elif user.role == UserRole.TEACHER:
        # Teachers can access photos from their school or their own
        teacher_profile = Teacher.query.filter_by(user_id=user.id).first()
        if not teacher_profile or (teacher.school_id != teacher_profile.school_id and teacher.id != teacher_profile.id):
            abort(403)
    elif user.role == UserRole.STUDENT:
        # Students can access teacher photos from their school
        student_profile = Student.query.filter_by(user_id=user.id).first()
        if not student_profile or teacher.school_id != student_profile.school_id:
            abort(403)
    else:
        abort(403)
    
    # Check if teacher has photo
    if not teacher.photo_url:
        abort(404)
    
    # Serve file
    service = FileUploadService()
    return service.serve_file(teacher.photo_url)


@files_bp.route('/assignment/<int:assignment_id>')
@login_required
def serve_assignment_file(assignment_id):
    """Serves an assignment file with access control.

    Students can only access assignments for their class.

    Args:
        assignment_id (int): The ID of the assignment.

    Returns:
        File: The assignment file, or a 403/404 error.
    """
    user = User.query.get(session['user_id'])
    
    # Get assignment
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Check if assignment has file
    if not assignment.file_path:
        abort(404)
    
    # Access control
    if user.role == UserRole.SUPER_ADMIN:
        # Super admin can access any assignment
        pass
    elif user.role == UserRole.SCHOOL_ADMIN:
        # School admin can access assignments from their school
        if assignment.school_id != user.school_id:
            abort(403)
    elif user.role == UserRole.TEACHER:
        # Teachers can access assignments from their school
        teacher = Teacher.query.filter_by(user_id=user.id).first()
        if not teacher or assignment.school_id != teacher.school_id:
            abort(403)
    elif user.role == UserRole.STUDENT:
        # Students can only access assignments for their class
        student = Student.query.filter_by(user_id=user.id).first()
        if not student or assignment.class_id != student.class_id or assignment.school_id != student.school_id:
            abort(403)
    else:
        abort(403)
    
    # Serve file
    service = FileUploadService()
    return service.serve_file(assignment.file_path, as_attachment=True)


@files_bp.route('/assignment/<int:assignment_id>/download')
@login_required
def download_assignment_file(assignment_id):
    """Alias for serving an assignment file that forces a download.

    Args:
        assignment_id (int): The ID of the assignment.

    Returns:
        File: The assignment file as a download.
    """
    return serve_assignment_file(assignment_id)


@files_bp.route('/receipt/<path:filename>')
@login_required
def serve_receipt(filename):
    """Serves a fee receipt with access control.

    Access is determined by parsing the school ID from the filename and
    comparing it with the user's school affiliation.

    Args:
        filename (str): The name of the receipt file.

    Returns:
        File: The receipt file, or a 403 error.
    """
    user = User.query.get(session['user_id'])
    
    # Only allow access to receipts from user's school
    # Extract school_id from filename if it follows our naming convention
    # Format: receipt_schoolid_receiptno_timestamp.pdf
    try:
        parts = filename.split('_')
        if len(parts) >= 2 and parts[0] == 'receipt':
            file_school_id = int(parts[1])
            
            # Access control
            if user.role == UserRole.SUPER_ADMIN:
                pass
            elif user.role in [UserRole.SCHOOL_ADMIN, UserRole.TEACHER]:
                if user.school_id != file_school_id:
                    abort(403)
            elif user.role == UserRole.STUDENT:
                student = Student.query.filter_by(user_id=user.id).first()
                if not student or student.school_id != file_school_id:
                    abort(403)
            else:
                abort(403)
        else:
            # If filename doesn't follow convention, only super admin can access
            if user.role != UserRole.SUPER_ADMIN:
                abort(403)
    except (ValueError, IndexError):
        # If parsing fails, only super admin can access
        if user.role != UserRole.SUPER_ADMIN:
            abort(403)
    
    # Serve file
    service = FileUploadService()
    file_path = f"system/receipts/{filename}"
    return service.serve_file(file_path, as_attachment=True)


@files_bp.route('/backup/<path:filename>')
@login_required
def serve_backup(filename):
    """Serves a backup file with access control.

    Only super admins and school admins can access backups. School admins
    are restricted to backups from their own school.

    Args:
        filename (str): The name of the backup file.

    Returns:
        File: The backup file, or a 403 error.
    """
    user = User.query.get(session['user_id'])
    
    # Only super admin and school admin can access backups
    if user.role not in [UserRole.SUPER_ADMIN, UserRole.SCHOOL_ADMIN]:
        abort(403)
    
    # Extract school_id from filename if it follows our naming convention
    # Format: backup_schoolid_timestamp.zip
    try:
        parts = filename.split('_')
        if len(parts) >= 2 and parts[0] == 'backup':
            file_school_id = int(parts[1])
            
            # School admin can only access their school's backups
            if user.role == UserRole.SCHOOL_ADMIN and user.school_id != file_school_id:
                abort(403)
        else:
            # If filename doesn't follow convention, only super admin can access
            if user.role != UserRole.SUPER_ADMIN:
                abort(403)
    except (ValueError, IndexError):
        # If parsing fails, only super admin can access
        if user.role != UserRole.SUPER_ADMIN:
            abort(403)
    
    # Serve file
    service = FileUploadService()
    file_path = f"system/backups/{filename}"
    return service.serve_file(file_path, as_attachment=True)


@files_bp.route('/upload/student/photo/<int:student_id>', methods=['POST'])
@login_required
def upload_student_photo(student_id):
    """Handles the upload of a student's photo.

    Allows school admins and teachers to upload a photo for a student in
    their school.

    Args:
        student_id (int): The ID of the student.

    Returns:
        dict: A success or error message, along with the URL of the new photo.
    """
    user = User.query.get(session['user_id'])
    
    # Get student
    student = Student.query.get_or_404(student_id)
    
    # Access control - only school admin and teachers from same school can upload
    if user.role == UserRole.SUPER_ADMIN:
        pass
    elif user.role == UserRole.SCHOOL_ADMIN:
        if student.school_id != user.school_id:
            abort(403)
    elif user.role == UserRole.TEACHER:
        teacher = Teacher.query.filter_by(user_id=user.id).first()
        if not teacher or student.school_id != teacher.school_id:
            abort(403)
    else:
        abort(403)
    
    # Check if file was uploaded
    if 'photo' not in request.files:
        return {'success': False, 'message': 'No file uploaded'}, 400
    
    file = request.files['photo']
    if file.filename == '':
        return {'success': False, 'message': 'No file selected'}, 400
    
    # Upload file
    service = FileUploadService()
    success, message, file_info = service.save_file(file, 'students/photos', 'image', f'student_{student_id}')
    
    if success:
        # Delete old photo if exists
        if student.photo_url:
            service.delete_file(student.photo_url)
        
        # Update student record
        student.photo_url = file_info['file_path']
        from extensions import db
        db.session.commit()
        
        return {'success': True, 'message': message, 'photo_url': file_info['file_path']}
    else:
        return {'success': False, 'message': message}, 400


@files_bp.route('/upload/teacher/photo/<int:teacher_id>', methods=['POST'])
@login_required
def upload_teacher_photo(teacher_id):
    """Handles the upload of a teacher's photo.

    Allows school admins to upload photos for teachers in their school, and
    teachers to upload their own photo.

    Args:
        teacher_id (int): The ID of the teacher.

    Returns:
        dict: A success or error message, along with the URL of the new photo.
    """
    user = User.query.get(session['user_id'])
    
    # Get teacher
    teacher = Teacher.query.get_or_404(teacher_id)
    
    # Access control - only school admin and the teacher themselves can upload
    if user.role == UserRole.SUPER_ADMIN:
        pass
    elif user.role == UserRole.SCHOOL_ADMIN:
        if teacher.school_id != user.school_id:
            abort(403)
    elif user.role == UserRole.TEACHER:
        teacher_profile = Teacher.query.filter_by(user_id=user.id).first()
        if not teacher_profile or teacher.id != teacher_profile.id:
            abort(403)
    else:
        abort(403)
    
    # Check if file was uploaded
    if 'photo' not in request.files:
        return {'success': False, 'message': 'No file uploaded'}, 400
    
    file = request.files['photo']
    if file.filename == '':
        return {'success': False, 'message': 'No file selected'}, 400
    
    # Upload file
    service = FileUploadService()
    success, message, file_info = service.save_file(file, 'teachers/photos', 'image', f'teacher_{teacher_id}')
    
    if success:
        # Delete old photo if exists
        if teacher.photo_url:
            service.delete_file(teacher.photo_url)
        
        # Update teacher record
        teacher.photo_url = file_info['file_path']
        from extensions import db
        db.session.commit()
        
        return {'success': True, 'message': message, 'photo_url': file_info['file_path']}
    else:
        return {'success': False, 'message': message}, 400


@files_bp.route('/upload/assignment', methods=['POST'])
@login_required
def upload_assignment_file():
    """Handles the upload of an assignment file by a teacher.

    Returns:
        dict: A success or error message, along with information about the
              uploaded file.
    """
    user = User.query.get(session['user_id'])
    
    # Only teachers can upload assignments
    if user.role != UserRole.TEACHER:
        abort(403)
    
    teacher = Teacher.query.filter_by(user_id=user.id).first()
    if not teacher:
        abort(403)
    
    # Check if file was uploaded
    if 'assignment_file' not in request.files:
        return {'success': False, 'message': 'No file uploaded'}, 400
    
    file = request.files['assignment_file']
    if file.filename == '':
        return {'success': False, 'message': 'No file selected'}, 400
    
    # Get additional data
    class_id = request.form.get('class_id')
    if not class_id:
        return {'success': False, 'message': 'Class ID required'}, 400
    
    # Upload file
    service = FileUploadService()
    success, message, file_info = service.save_file(
        file, 'assignments/materials', 'assignment', f'teacher_{teacher.id}_class_{class_id}'
    )
    
    if success:
        return {
            'success': True, 
            'message': message, 
            'file_info': {
                'file_path': file_info['file_path'],
                'original_filename': file_info['original_filename'],
                'file_size': file_info['file_size']
            }
        }
    else:
        return {'success': False, 'message': message}, 400


# File Management API Routes

@files_bp.route('/api/files/list')
@login_required
def list_files():
    """Lists files in a specified directory.

    Accessible only by admin users. Can list files in a specific directory
    or all files across all managed directories.

    Args:
        directory (str, optional): The directory to list. Defaults to 'all'.

    Returns:
        dict: A list of files with their metadata.
    """
    user = User.query.get(session['user_id'])
    
    # Only admin users can access file manager
    if user.role not in [UserRole.SUPER_ADMIN, UserRole.SCHOOL_ADMIN]:
        abort(403)
    
    directory = request.args.get('directory', 'all')
    
    try:
        service = FileUploadService()
        files = []
        
        if directory == 'all':
            # List all files from all directories
            directories = [
                'students/photos', 'teachers/photos', 'assignments/materials',
                'assignments/submissions', 'system/receipts', 'system/backups', 'temp'
            ]
            
            for dir_path in directories:
                full_path = os.path.join(service.upload_folder, dir_path)
                if os.path.exists(full_path):
                    for filename in os.listdir(full_path):
                        file_path = os.path.join(full_path, filename)
                        if os.path.isfile(file_path):
                            stat = os.stat(file_path)
                            files.append({
                                'name': filename,
                                'path': os.path.join(dir_path, filename),
                                'size': stat.st_size,
                                'modified': stat.st_mtime,
                                'directory': dir_path
                            })
        else:
            # List files from specific directory
            full_path = os.path.join(service.upload_folder, directory)
            if os.path.exists(full_path):
                for filename in os.listdir(full_path):
                    file_path = os.path.join(full_path, filename)
                    if os.path.isfile(file_path):
                        stat = os.stat(file_path)
                        files.append({
                            'name': filename,
                            'path': os.path.join(directory, filename),
                            'size': stat.st_size,
                            'modified': stat.st_mtime,
                            'directory': directory
                        })
        
        # Sort files by modification time (newest first)
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        return {'success': True, 'files': files}
        
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500


@files_bp.route('/api/files/download')
@login_required
def download_file():
    """Serves a file for download.

    Accessible only by admin users.

    Args:
        path (str): The path to the file to download.

    Returns:
        File: The requested file as a download.
    """
    user = User.query.get(session['user_id'])
    
    # Only admin users can download files through file manager
    if user.role not in [UserRole.SUPER_ADMIN, UserRole.SCHOOL_ADMIN]:
        abort(403)
    
    file_path = request.args.get('path')
    if not file_path:
        abort(400)
    
    service = FileUploadService()
    return service.serve_file(file_path, as_attachment=True)


@files_bp.route('/api/files/view')
@login_required
def view_file():
    """Serves a file for viewing in the browser.

    Accessible only by admin users.

    Args:
        path (str): The path to the file to view.

    Returns:
        File: The requested file.
    """
    user = User.query.get(session['user_id'])
    
    # Only admin users can view files through file manager
    if user.role not in [UserRole.SUPER_ADMIN, UserRole.SCHOOL_ADMIN]:
        abort(403)
    
    file_path = request.args.get('path')
    if not file_path:
        abort(400)
    
    service = FileUploadService()
    return service.serve_file(file_path, as_attachment=False)


@files_bp.route('/api/files/delete', methods=['POST'])
@login_required
def delete_file():
    """Deletes a file from the server.

    Accessible only by admin users.

    Args:
        path (str): The path to the file to delete.

    Returns:
        dict: A success or error message.
    """
    user = User.query.get(session['user_id'])
    
    # Only admin users can delete files
    if user.role not in [UserRole.SUPER_ADMIN, UserRole.SCHOOL_ADMIN]:
        abort(403)
    
    data = request.get_json()
    file_path = data.get('path')
    
    if not file_path:
        return {'success': False, 'message': 'File path required'}, 400
    
    try:
        service = FileUploadService()
        success, message = service.delete_file(file_path)
        
        return {'success': success, 'message': message}
        
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500


@files_bp.route('/api/files/upload', methods=['POST'])
@login_required
def upload_files():
    """Handles the upload of multiple files by an admin user.

    Args:
        directory (str, optional): The directory to upload the files to.
                                   Defaults to 'temp'.
        files (list): The list of files to upload.

    Returns:
        dict: A summary of the upload operation, including the number of
              successful uploads and any errors.
    """
    user = User.query.get(session['user_id'])
    
    # Only admin users can upload files through file manager
    if user.role not in [UserRole.SUPER_ADMIN, UserRole.SCHOOL_ADMIN]:
        abort(403)
    
    directory = request.form.get('directory', 'temp')
    files = request.files.getlist('files')
    
    if not files:
        return {'success': False, 'message': 'No files uploaded'}, 400
    
    try:
        service = FileUploadService()
        uploaded_count = 0
        errors = []
        
        for file in files:
            if file and file.filename:
                success, message, file_info = service.save_file(file, directory, 'default')
                if success:
                    uploaded_count += 1
                else:
                    errors.append(f"{file.filename}: {message}")
        
        return {
            'success': uploaded_count > 0,
            'uploaded': uploaded_count,
            'errors': errors,
            'message': f'Uploaded {uploaded_count} files successfully'
        }
        
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500


@files_bp.route('/api/files/cleanup', methods=['POST'])
@login_required
def cleanup_temp_files():
    """Cleans up temporary files older than a specified age.

    Accessible only by admin users.

    Returns:
        dict: A success or error message.
    """
    user = User.query.get(session['user_id'])
    
    # Only admin users can cleanup files
    if user.role not in [UserRole.SUPER_ADMIN, UserRole.SCHOOL_ADMIN]:
        abort(403)
    
    try:
        service = FileUploadService()
        service.cleanup_temp_files(24)  # Clean files older than 24 hours
        
        return {'success': True, 'message': 'Temporary files cleaned up successfully'}
        
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500


@files_bp.route('/api/files/stats')
@login_required
def get_storage_stats():
    """Retrieves storage statistics for the application.

    Calculates the total size of uploaded files and provides a breakdown by
    directory and file type. Accessible only by admin users.

    Returns:
        dict: A dictionary containing storage statistics.
    """
    user = User.query.get(session['user_id'])
    
    # Only admin users can view storage stats
    if user.role not in [UserRole.SUPER_ADMIN, UserRole.SCHOOL_ADMIN]:
        abort(403)
    
    try:
        service = FileUploadService()
        
        # Calculate directory sizes
        directories = {
            'students/photos': 0,
            'teachers/photos': 0,
            'assignments/materials': 0,
            'assignments/submissions': 0,
            'system/receipts': 0,
            'system/backups': 0,
            'temp': 0
        }
        
        total_size = 0
        file_counts = {
            'image': 0,
            'document': 0,
            'assignment': 0,
            'total': 0
        }
        
        for directory in directories:
            dir_size = service.get_directory_size(directory)
            directories[directory] = dir_size
            total_size += dir_size
            
            # Count files by type
            full_path = os.path.join(service.upload_folder, directory)
            if os.path.exists(full_path):
                for filename in os.listdir(full_path):
                    if os.path.isfile(os.path.join(full_path, filename)):
                        file_counts['total'] += 1
                        
                        # Categorize by extension
                        ext = filename.split('.')[-1].lower()
                        if ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
                            file_counts['image'] += 1
                        elif ext in ['pdf', 'doc', 'docx', 'txt', 'rtf']:
                            file_counts['document'] += 1
                        elif directory.startswith('assignments'):
                            file_counts['assignment'] += 1
        
        return {
            'success': True,
            'stats': {
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'directories': directories,
                'image_count': file_counts['image'],
                'document_count': file_counts['document'],
                'assignment_count': file_counts['assignment'],
                'total_files': file_counts['total']
            }
        }
        
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500


# Error handlers
@files_bp.errorhandler(403)
def forbidden(error):
    """Handles 403 Forbidden errors for the blueprint."""
    return {'error': 'Access denied'}, 403

@files_bp.errorhandler(404)
def not_found(error):
    """Handles 404 Not Found errors for the blueprint."""
    return {'error': 'File not found'}, 404

@files_bp.errorhandler(500)
def internal_error(error):
    """Handles 500 Internal Server errors for the blueprint."""
    return {'error': 'Internal server error'}, 500