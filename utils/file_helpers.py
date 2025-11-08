"""
File handling utilities and helpers
"""
import os
import mimetypes
from flask import url_for, current_app
from services.file_upload_service import FileUploadService


def get_file_url(file_path, file_type='general'):
    """Get URL for serving a file based on its type and path"""
    if not file_path:
        return None
    
    # Determine the appropriate endpoint based on file type and path
    if file_path.startswith('students/photos/'):
        # Extract student ID from filename if possible
        filename = os.path.basename(file_path)
        if filename.startswith('student_'):
            try:
                student_id = filename.split('_')[1]
                return url_for('files.serve_student_photo', student_id=int(student_id))
            except (IndexError, ValueError):
                pass
    
    elif file_path.startswith('teachers/photos/'):
        # Extract teacher ID from filename if possible
        filename = os.path.basename(file_path)
        if filename.startswith('teacher_'):
            try:
                teacher_id = filename.split('_')[1]
                return url_for('files.serve_teacher_photo', teacher_id=int(teacher_id))
            except (IndexError, ValueError):
                pass
    
    elif file_path.startswith('assignments/materials/'):
        # For assignments, we need the assignment ID from database
        # This should be handled in the template with the assignment object
        return None
    
    elif file_path.startswith('system/receipts/'):
        filename = os.path.basename(file_path)
        return url_for('files.serve_receipt', filename=filename)
    
    elif file_path.startswith('system/backups/'):
        filename = os.path.basename(file_path)
        return url_for('files.serve_backup', filename=filename)
    
    # Default: return None if we can't determine the URL
    return None


def get_file_icon(filename):
    """Get appropriate icon class for file type"""
    if not filename:
        return 'fas fa-file'
    
    extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    icon_map = {
        'pdf': 'fas fa-file-pdf text-danger',
        'doc': 'fas fa-file-word text-primary',
        'docx': 'fas fa-file-word text-primary',
        'xls': 'fas fa-file-excel text-success',
        'xlsx': 'fas fa-file-excel text-success',
        'ppt': 'fas fa-file-powerpoint text-warning',
        'pptx': 'fas fa-file-powerpoint text-warning',
        'jpg': 'fas fa-file-image text-info',
        'jpeg': 'fas fa-file-image text-info',
        'png': 'fas fa-file-image text-info',
        'gif': 'fas fa-file-image text-info',
        'zip': 'fas fa-file-archive text-secondary',
        'rar': 'fas fa-file-archive text-secondary',
        '7z': 'fas fa-file-archive text-secondary',
        'txt': 'fas fa-file-alt text-muted',
        'csv': 'fas fa-file-csv text-success'
    }
    
    return icon_map.get(extension, 'fas fa-file text-muted')


def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if not size_bytes:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.1f} TB"


def is_image_file(filename):
    """Check if file is an image"""
    if not filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    return extension in {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'}


def get_mime_type(filename):
    """Get MIME type for file"""
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream'


def validate_upload_file(file, allowed_types=None, max_size_mb=10):
    """Validate uploaded file"""
    errors = []
    
    if not file or file.filename == '':
        errors.append("No file selected")
        return errors
    
    # Check file extension
    if allowed_types:
        extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if extension not in allowed_types:
            errors.append(f"File type not allowed. Allowed types: {', '.join(allowed_types)}")
    
    # Check file size
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    
    max_size_bytes = max_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        errors.append(f"File too large. Maximum size: {max_size_mb}MB")
    
    return errors


def get_upload_progress_info(file_path):
    """Get upload progress information for a file"""
    service = FileUploadService()
    file_info = service.get_file_info(file_path)
    
    if not file_info:
        return None
    
    return {
        'file_size': file_info['file_size'],
        'file_size_formatted': format_file_size(file_info['file_size']),
        'mime_type': file_info['mime_type'],
        'created_date': file_info['created_date'],
        'is_image': is_image_file(os.path.basename(file_path)),
        'icon_class': get_file_icon(os.path.basename(file_path))
    }


def cleanup_orphaned_files():
    """Clean up files that are no longer referenced in database"""
    # This would be run as a maintenance task
    service = FileUploadService()
    
    # Get all file paths from database
    from models.student import Student
    from models.teacher import Teacher
    from models.assignment import Assignment, AssignmentStatus, AssignmentType
    
    referenced_files = set()
    
    # Student photos
    students = Student.query.filter(Student.photo_url.isnot(None)).all()
    for student in students:
        referenced_files.add(student.photo_url)
    
    # Teacher photos
    teachers = Teacher.query.filter(Teacher.photo_url.isnot(None)).all()
    for teacher in teachers:
        referenced_files.add(teacher.photo_url)
    
    # Assignment files
    assignments = Assignment.query.filter(Assignment.file_path.isnot(None)).all()
    for assignment in assignments:
        referenced_files.add(assignment.file_path)
    
    # Check physical files and remove orphaned ones
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    
    for root, dirs, files in os.walk(upload_folder):
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, upload_folder)
            
            # Skip system files and temp files
            if relative_path.startswith('system/') or relative_path.startswith('temp/'):
                continue
            
            # Check if file is referenced
            if relative_path not in referenced_files:
                try:
                    os.remove(file_path)
                    print(f"Removed orphaned file: {relative_path}")
                except Exception as e:
                    print(f"Error removing file {relative_path}: {e}")


# Template filters for Jinja2
def register_file_filters(app):
    """Register file-related template filters"""
    
    @app.template_filter('file_size')
    def file_size_filter(size_bytes):
        return format_file_size(size_bytes)
    
    @app.template_filter('file_icon')
    def file_icon_filter(filename):
        return get_file_icon(filename)
    
    @app.template_filter('file_url')
    def file_url_filter(file_path, file_type='general'):
        return get_file_url(file_path, file_type)
    
    @app.template_filter('is_image')
    def is_image_filter(filename):
        return is_image_file(filename)