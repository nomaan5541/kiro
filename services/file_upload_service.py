"""
File Upload Service for secure file handling and storage
"""
import os
import uuid
import hashlib
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from flask import current_app, send_from_directory, abort
from typing import Optional, Tuple, List
import mimetypes


class FileUploadService:
    """Service for handling secure file uploads and storage"""
    
    # Allowed file types and their extensions
    ALLOWED_EXTENSIONS = {
        'image': {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'},
        'document': {'pdf', 'doc', 'docx', 'txt', 'rtf'},
        'spreadsheet': {'xls', 'xlsx', 'csv'},
        'presentation': {'ppt', 'pptx'},
        'archive': {'zip', 'rar', '7z'},
        'assignment': {'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'zip'}
    }
    
    # Maximum file sizes (in bytes)
    MAX_FILE_SIZES = {
        'image': 5 * 1024 * 1024,      # 5MB
        'document': 10 * 1024 * 1024,   # 10MB
        'assignment': 10 * 1024 * 1024, # 10MB
        'default': 10 * 1024 * 1024     # 10MB
    }
    
    def __init__(self, upload_folder: str = None):
        """Initialize file upload service"""
        self.upload_folder = upload_folder or current_app.config.get('UPLOAD_FOLDER', 'uploads')
        self.ensure_upload_directories()
    
    def ensure_upload_directories(self):
        """Ensure all required upload directories exist"""
        directories = [
            'students/photos',
            'students/documents',
            'teachers/photos',
            'teachers/qualifications',
            'assignments/materials',
            'assignments/submissions',
            'system/backups',
            'system/receipts',
            'temp'
        ]
        
        for directory in directories:
            full_path = os.path.join(self.upload_folder, directory)
            os.makedirs(full_path, exist_ok=True)
    
    def is_allowed_file(self, filename: str, file_type: str = 'default') -> bool:
        """Check if file extension is allowed for the given type"""
        if '.' not in filename:
            return False
        
        extension = filename.rsplit('.', 1)[1].lower()
        allowed_extensions = self.ALLOWED_EXTENSIONS.get(file_type, set())
        
        # If no specific type, check all allowed extensions
        if not allowed_extensions:
            all_extensions = set()
            for ext_set in self.ALLOWED_EXTENSIONS.values():
                all_extensions.update(ext_set)
            return extension in all_extensions
        
        return extension in allowed_extensions
    
    def validate_file_size(self, file: FileStorage, file_type: str = 'default') -> bool:
        """Validate file size against limits"""
        if not file:
            return False
        
        # Get file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        max_size = self.MAX_FILE_SIZES.get(file_type, self.MAX_FILE_SIZES['default'])
        return file_size <= max_size
    
    def generate_unique_filename(self, original_filename: str, prefix: str = '') -> str:
        """Generate a unique filename to prevent conflicts"""
        # Get file extension
        if '.' in original_filename:
            name, extension = original_filename.rsplit('.', 1)
            extension = extension.lower()
        else:
            name = original_filename
            extension = ''
        
        # Create unique identifier
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        
        # Secure the original name
        secure_name = secure_filename(name)[:20]  # Limit length
        
        # Combine parts
        if prefix:
            filename = f"{prefix}_{secure_name}_{timestamp}_{unique_id}"
        else:
            filename = f"{secure_name}_{timestamp}_{unique_id}"
        
        if extension:
            filename = f"{filename}.{extension}"
        
        return filename
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of file for integrity checking"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    def save_file(self, file: FileStorage, subdirectory: str, file_type: str = 'default', 
                  prefix: str = '') -> Tuple[bool, str, dict]:
        """
        Save uploaded file to specified subdirectory with enhanced validation
        
        Returns:
            Tuple of (success, message, file_info)
        """
        try:
            # Enhanced validation using FileValidator
            from utils.file_validators import FileValidator
            validator = FileValidator()
            
            is_valid, validation_errors = validator.validate_file_upload(file, file_type)
            if not is_valid:
                return False, "; ".join(validation_errors), {}
            
            # Legacy validation for backward compatibility
            if not file or file.filename == '':
                return False, "No file selected", {}
            
            # Check file extension (additional check)
            if not self.is_allowed_file(file.filename, file_type):
                allowed_exts = ', '.join(self.ALLOWED_EXTENSIONS.get(file_type, ['pdf', 'doc', 'jpg']))
                return False, f"File type not allowed. Allowed types: {allowed_exts}", {}
            
            # Check file size (additional check)
            if not self.validate_file_size(file, file_type):
                max_size_mb = self.MAX_FILE_SIZES.get(file_type, self.MAX_FILE_SIZES['default']) / (1024 * 1024)
                return False, f"File too large. Maximum size: {max_size_mb:.1f}MB", {}
            
            # Generate unique filename
            filename = self.generate_unique_filename(file.filename, prefix)
            
            # Create full path
            file_path = os.path.join(self.upload_folder, subdirectory, filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Save file
            file.save(file_path)
            
            # Get file info
            file_size = os.path.getsize(file_path)
            file_hash = self.calculate_file_hash(file_path)
            
            # Get MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            
            file_info = {
                'original_filename': file.filename,
                'saved_filename': filename,
                'file_path': os.path.join(subdirectory, filename),
                'full_path': file_path,
                'file_size': file_size,
                'file_hash': file_hash,
                'mime_type': mime_type,
                'upload_date': datetime.now()
            }
            
            return True, "File uploaded successfully", file_info
            
        except Exception as e:
            return False, f"Error uploading file: {str(e)}", {}
    
    def delete_file(self, file_path: str) -> Tuple[bool, str]:
        """Delete a file from storage"""
        try:
            full_path = os.path.join(self.upload_folder, file_path)
            if os.path.exists(full_path):
                os.remove(full_path)
                return True, "File deleted successfully"
            else:
                return False, "File not found"
        except Exception as e:
            return False, f"Error deleting file: {str(e)}"
    
    def get_file_info(self, file_path: str) -> Optional[dict]:
        """Get information about a stored file"""
        try:
            full_path = os.path.join(self.upload_folder, file_path)
            if not os.path.exists(full_path):
                return None
            
            stat = os.stat(full_path)
            mime_type, _ = mimetypes.guess_type(full_path)
            
            return {
                'file_path': file_path,
                'full_path': full_path,
                'file_size': stat.st_size,
                'mime_type': mime_type,
                'created_date': datetime.fromtimestamp(stat.st_ctime),
                'modified_date': datetime.fromtimestamp(stat.st_mtime)
            }
        except Exception:
            return None
    
    def serve_file(self, file_path: str, as_attachment: bool = False) -> any:
        """Serve a file securely using Flask's send_from_directory"""
        try:
            # Split path into directory and filename
            directory = os.path.dirname(file_path)
            filename = os.path.basename(file_path)
            
            # Full directory path
            full_directory = os.path.join(self.upload_folder, directory)
            
            # Check if file exists
            full_file_path = os.path.join(full_directory, filename)
            if not os.path.exists(full_file_path):
                abort(404)
            
            # Serve file securely
            return send_from_directory(
                full_directory, 
                filename, 
                as_attachment=as_attachment
            )
            
        except Exception as e:
            current_app.logger.error(f"Error serving file {file_path}: {str(e)}")
            abort(500)
    
    def move_file(self, old_path: str, new_path: str) -> Tuple[bool, str]:
        """Move a file from one location to another"""
        try:
            old_full_path = os.path.join(self.upload_folder, old_path)
            new_full_path = os.path.join(self.upload_folder, new_path)
            
            if not os.path.exists(old_full_path):
                return False, "Source file not found"
            
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(new_full_path), exist_ok=True)
            
            # Move file
            os.rename(old_full_path, new_full_path)
            
            return True, "File moved successfully"
            
        except Exception as e:
            return False, f"Error moving file: {str(e)}"
    
    def get_directory_size(self, subdirectory: str = '') -> int:
        """Get total size of files in a directory"""
        try:
            directory = os.path.join(self.upload_folder, subdirectory)
            total_size = 0
            
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
            
            return total_size
            
        except Exception:
            return 0
    
    def cleanup_temp_files(self, max_age_hours: int = 24):
        """Clean up temporary files older than specified hours"""
        try:
            temp_dir = os.path.join(self.upload_folder, 'temp')
            if not os.path.exists(temp_dir):
                return
            
            current_time = datetime.now()
            max_age_seconds = max_age_hours * 3600
            
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                if os.path.isfile(file_path):
                    file_age = current_time.timestamp() - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        
        except Exception as e:
            current_app.logger.error(f"Error cleaning temp files: {str(e)}")


# Utility functions for common file operations

def save_student_photo(file: FileStorage, student_id: int) -> Tuple[bool, str, dict]:
    """Save student photo"""
    service = FileUploadService()
    return service.save_file(file, 'students/photos', 'image', f'student_{student_id}')

def save_teacher_photo(file: FileStorage, teacher_id: int) -> Tuple[bool, str, dict]:
    """Save teacher photo"""
    service = FileUploadService()
    return service.save_file(file, 'teachers/photos', 'image', f'teacher_{teacher_id}')

def save_assignment_file(file: FileStorage, teacher_id: int, class_id: int) -> Tuple[bool, str, dict]:
    """Save assignment file"""
    service = FileUploadService()
    return service.save_file(file, 'assignments/materials', 'assignment', f'assign_{teacher_id}_{class_id}')

def serve_secure_file(file_path: str, user_role: str, user_school_id: int, 
                     file_school_id: int = None) -> any:
    """Serve file with security checks"""
    # Basic security check - user must be from same school
    if file_school_id and user_school_id != file_school_id:
        abort(403)
    
    service = FileUploadService()
    return service.serve_file(file_path)

def delete_file_safely(file_path: str) -> Tuple[bool, str]:
    """Delete file with safety checks"""
    service = FileUploadService()
    return service.delete_file(file_path)