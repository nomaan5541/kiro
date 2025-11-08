"""
File validation utilities for secure file handling
"""
import os
import magic
import hashlib
from PIL import Image
from werkzeug.datastructures import FileStorage
from typing import List, Tuple, Optional, Dict


class FileValidator:
    """Comprehensive file validation for security and integrity"""
    
    # Allowed MIME types for different file categories
    ALLOWED_MIME_TYPES = {
        'image': {
            'image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp'
        },
        'document': {
            'application/pdf', 'application/msword', 
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain', 'application/rtf'
        },
        'spreadsheet': {
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/csv'
        },
        'presentation': {
            'application/vnd.ms-powerpoint',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        },
        'archive': {
            'application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed'
        }
    }
    
    # Maximum file sizes (in bytes)
    MAX_FILE_SIZES = {
        'image': 5 * 1024 * 1024,      # 5MB
        'document': 10 * 1024 * 1024,   # 10MB
        'spreadsheet': 10 * 1024 * 1024, # 10MB
        'presentation': 20 * 1024 * 1024, # 20MB
        'archive': 50 * 1024 * 1024,    # 50MB
        'assignment': 10 * 1024 * 1024, # 10MB
        'default': 10 * 1024 * 1024     # 10MB
    }
    
    # Dangerous file extensions that should never be allowed
    DANGEROUS_EXTENSIONS = {
        'exe', 'bat', 'cmd', 'com', 'pif', 'scr', 'vbs', 'js', 'jar',
        'msi', 'dll', 'scf', 'lnk', 'inf', 'reg', 'ps1', 'sh', 'php',
        'asp', 'aspx', 'jsp', 'py', 'rb', 'pl', 'cgi'
    }
    
    def __init__(self):
        """Initialize file validator"""
        self.magic_mime = magic.Magic(mime=True)
    
    def validate_file_upload(self, file: FileStorage, file_type: str = 'default', 
                           custom_rules: Dict = None) -> Tuple[bool, List[str]]:
        """
        Comprehensive file validation
        
        Args:
            file: The uploaded file
            file_type: Type of file (image, document, etc.)
            custom_rules: Custom validation rules
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        if not file or not file.filename:
            errors.append("No file provided")
            return False, errors
        
        # Basic filename validation
        filename_errors = self._validate_filename(file.filename)
        errors.extend(filename_errors)
        
        # File size validation
        size_errors = self._validate_file_size(file, file_type)
        errors.extend(size_errors)
        
        # MIME type validation
        mime_errors = self._validate_mime_type(file, file_type)
        errors.extend(mime_errors)
        
        # Content validation (for images)
        if file_type == 'image':
            content_errors = self._validate_image_content(file)
            errors.extend(content_errors)
        
        # Custom validation rules
        if custom_rules:
            custom_errors = self._apply_custom_rules(file, custom_rules)
            errors.extend(custom_errors)
        
        # Security validation
        security_errors = self._validate_security(file)
        errors.extend(security_errors)
        
        return len(errors) == 0, errors
    
    def _validate_filename(self, filename: str) -> List[str]:
        """Validate filename for security issues"""
        errors = []
        
        # Check for dangerous extensions
        if '.' in filename:
            extension = filename.rsplit('.', 1)[1].lower()
            if extension in self.DANGEROUS_EXTENSIONS:
                errors.append(f"File type '{extension}' is not allowed for security reasons")
        
        # Check for path traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            errors.append("Filename contains invalid characters")
        
        # Check filename length
        if len(filename) > 255:
            errors.append("Filename is too long (maximum 255 characters)")
        
        # Check for null bytes
        if '\x00' in filename:
            errors.append("Filename contains null bytes")
        
        return errors
    
    def _validate_file_size(self, file: FileStorage, file_type: str) -> List[str]:
        """Validate file size"""
        errors = []
        
        # Get file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        # Check against limits
        max_size = self.MAX_FILE_SIZES.get(file_type, self.MAX_FILE_SIZES['default'])
        
        if file_size > max_size:
            max_size_mb = max_size / (1024 * 1024)
            errors.append(f"File size ({file_size / (1024 * 1024):.1f}MB) exceeds maximum allowed size ({max_size_mb:.1f}MB)")
        
        if file_size == 0:
            errors.append("File is empty")
        
        return errors
    
    def _validate_mime_type(self, file: FileStorage, file_type: str) -> List[str]:
        """Validate MIME type using python-magic"""
        errors = []
        
        try:
            # Read first 2048 bytes for MIME detection
            file.seek(0)
            file_header = file.read(2048)
            file.seek(0)
            
            # Detect MIME type
            detected_mime = magic.from_buffer(file_header, mime=True)
            
            # Get allowed MIME types for this file type
            allowed_mimes = set()
            if file_type in self.ALLOWED_MIME_TYPES:
                allowed_mimes = self.ALLOWED_MIME_TYPES[file_type]
            else:
                # If file_type not specified, allow all known safe types
                for mime_set in self.ALLOWED_MIME_TYPES.values():
                    allowed_mimes.update(mime_set)
            
            if detected_mime not in allowed_mimes:
                errors.append(f"File type '{detected_mime}' is not allowed")
            
        except Exception as e:
            errors.append(f"Could not determine file type: {str(e)}")
        
        return errors
    
    def _validate_image_content(self, file: FileStorage) -> List[str]:
        """Validate image content for additional security"""
        errors = []
        
        try:
            file.seek(0)
            
            # Try to open with PIL to validate it's a real image
            with Image.open(file) as img:
                # Check image dimensions
                width, height = img.size
                
                # Reasonable size limits
                if width > 10000 or height > 10000:
                    errors.append("Image dimensions are too large")
                
                if width < 1 or height < 1:
                    errors.append("Invalid image dimensions")
                
                # Check for suspicious metadata
                if hasattr(img, '_getexif') and img._getexif():
                    exif = img._getexif()
                    # Remove potentially dangerous EXIF data
                    # This is more of a warning than an error
                    pass
            
            file.seek(0)
            
        except Exception as e:
            errors.append(f"Invalid image file: {str(e)}")
        
        return errors
    
    def _validate_security(self, file: FileStorage) -> List[str]:
        """Additional security validations"""
        errors = []
        
        try:
            file.seek(0)
            file_content = file.read(1024)  # Read first 1KB
            file.seek(0)
            
            # Check for executable signatures
            executable_signatures = [
                b'MZ',  # Windows PE
                b'\x7fELF',  # Linux ELF
                b'\xca\xfe\xba\xbe',  # Java class file
                b'PK\x03\x04',  # ZIP (could contain executables)
            ]
            
            for signature in executable_signatures:
                if file_content.startswith(signature):
                    # ZIP files are allowed for archives, but warn about others
                    if signature == b'PK\x03\x04':
                        # This is a ZIP file, which might be okay
                        pass
                    else:
                        errors.append("File appears to be an executable")
                        break
            
            # Check for script content in text files
            if file.filename and file.filename.lower().endswith(('.txt', '.csv')):
                try:
                    content_str = file_content.decode('utf-8', errors='ignore').lower()
                    script_indicators = ['<script', 'javascript:', 'vbscript:', 'onload=', 'onerror=']
                    
                    for indicator in script_indicators:
                        if indicator in content_str:
                            errors.append("File contains potentially malicious script content")
                            break
                except:
                    pass
            
        except Exception:
            # If we can't read the file, that's suspicious
            errors.append("Could not read file content for security validation")
        
        return errors
    
    def _apply_custom_rules(self, file: FileStorage, custom_rules: Dict) -> List[str]:
        """Apply custom validation rules"""
        errors = []
        
        # Custom file size limit
        if 'max_size' in custom_rules:
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)
            
            if file_size > custom_rules['max_size']:
                errors.append(f"File exceeds custom size limit")
        
        # Custom allowed extensions
        if 'allowed_extensions' in custom_rules:
            if '.' in file.filename:
                extension = file.filename.rsplit('.', 1)[1].lower()
                if extension not in custom_rules['allowed_extensions']:
                    errors.append(f"Extension '{extension}' not in allowed list")
        
        # Custom filename pattern
        if 'filename_pattern' in custom_rules:
            import re
            pattern = custom_rules['filename_pattern']
            if not re.match(pattern, file.filename):
                errors.append("Filename does not match required pattern")
        
        return errors
    
    def calculate_file_hash(self, file: FileStorage, algorithm: str = 'md5') -> str:
        """Calculate hash of file content"""
        file.seek(0)
        
        if algorithm == 'md5':
            hash_obj = hashlib.md5()
        elif algorithm == 'sha256':
            hash_obj = hashlib.sha256()
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")
        
        # Read file in chunks to handle large files
        while chunk := file.read(8192):
            hash_obj.update(chunk)
        
        file.seek(0)
        return hash_obj.hexdigest()
    
    def scan_for_viruses(self, file_path: str) -> Tuple[bool, str]:
        """
        Scan file for viruses using ClamAV (if available)
        This is a placeholder - implement based on your antivirus solution
        """
        try:
            # This would integrate with ClamAV or another antivirus solution
            # For now, return safe
            return True, "No antivirus scanner configured"
        except Exception as e:
            return False, f"Virus scan failed: {str(e)}"


# Utility functions for common validation scenarios

def validate_student_photo(file: FileStorage) -> Tuple[bool, List[str]]:
    """Validate student photo upload"""
    validator = FileValidator()
    return validator.validate_file_upload(file, 'image', {
        'max_size': 5 * 1024 * 1024,  # 5MB
        'allowed_extensions': {'jpg', 'jpeg', 'png'}
    })

def validate_teacher_photo(file: FileStorage) -> Tuple[bool, List[str]]:
    """Validate teacher photo upload"""
    validator = FileValidator()
    return validator.validate_file_upload(file, 'image', {
        'max_size': 5 * 1024 * 1024,  # 5MB
        'allowed_extensions': {'jpg', 'jpeg', 'png'}
    })

def validate_assignment_file(file: FileStorage) -> Tuple[bool, List[str]]:
    """Validate assignment file upload"""
    validator = FileValidator()
    return validator.validate_file_upload(file, 'assignment', {
        'max_size': 10 * 1024 * 1024,  # 10MB
        'allowed_extensions': {'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'zip'}
    })

def validate_document_upload(file: FileStorage) -> Tuple[bool, List[str]]:
    """Validate general document upload"""
    validator = FileValidator()
    return validator.validate_file_upload(file, 'document')

def validate_bulk_import_file(file: FileStorage) -> Tuple[bool, List[str]]:
    """Validate CSV/Excel file for bulk import"""
    validator = FileValidator()
    return validator.validate_file_upload(file, 'spreadsheet', {
        'max_size': 5 * 1024 * 1024,  # 5MB
        'allowed_extensions': {'csv', 'xlsx', 'xls'}
    })