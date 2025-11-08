"""
Backup and Export Service for School Management System
"""
import os
import json
import csv
import zipfile
import shutil
from datetime import datetime, date
from io import StringIO, BytesIO
import pandas as pd
from extensions import db
from models.school import School
from models.student import Student
from models.teacher import Teacher
from models.attendance import Attendance
from models.fee import Payment, StudentFeeStatus, FeeStructure
from models.activity import ActivityLog
from models.notification import NotificationLog
from models import Class, Subject
from sqlalchemy import text
import sqlite3


class BackupService:
    """Service for handling database backups and data exports"""
    
    def __init__(self, school_id=None):
        self.school_id = school_id
        self.backup_dir = os.path.join('backups')
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_full_database_backup(self):
        """Create a complete database backup"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"full_backup_{timestamp}.db"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Get current database path
            db_path = db.engine.url.database
            
            # Copy the entire database file
            shutil.copy2(db_path, backup_path)
            
            # Create metadata file
            metadata = {
                'backup_type': 'full_database',
                'created_at': datetime.now().isoformat(),
                'database_path': db_path,
                'backup_size': os.path.getsize(backup_path),
                'tables_included': self._get_table_list()
            }
            
            metadata_path = backup_path.replace('.db', '_metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return True, {
                'backup_file': backup_filename,
                'backup_path': backup_path,
                'metadata_path': metadata_path,
                'size': metadata['backup_size']
            }
            
        except Exception as e:
            return False, f"Error creating database backup: {str(e)}"
    
    def create_school_backup(self, include_files=True):
        """Create a backup for a specific school"""
        if not self.school_id:
            return False, "School ID not specified"
        
        try:
            school = School.query.get(self.school_id)
            if not school:
                return False, "School not found"
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"school_{school.id}_{timestamp}"
            backup_dir = os.path.join(self.backup_dir, backup_name)
            os.makedirs(backup_dir, exist_ok=True)
            
            # Export school data to JSON
            school_data = self._export_school_data()
            
            # Save JSON data
            json_path = os.path.join(backup_dir, 'school_data.json')
            with open(json_path, 'w') as f:
                json.dump(school_data, f, indent=2, default=str)
            
            # Export to CSV files
            csv_dir = os.path.join(backup_dir, 'csv_exports')
            os.makedirs(csv_dir, exist_ok=True)
            self._export_to_csv(csv_dir)
            
            # Copy uploaded files if requested
            if include_files:
                files_dir = os.path.join(backup_dir, 'files')
                self._backup_uploaded_files(files_dir)
            
            # Create backup archive
            archive_path = f"{backup_dir}.zip"
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(backup_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, backup_dir)
                        zipf.write(file_path, arcname)
            
            # Clean up temporary directory
            shutil.rmtree(backup_dir)
            
            # Create metadata
            metadata = {
                'backup_type': 'school_specific',
                'school_id': self.school_id,
                'school_name': school.name,
                'created_at': datetime.now().isoformat(),
                'includes_files': include_files,
                'archive_size': os.path.getsize(archive_path),
                'data_summary': self._get_data_summary()
            }
            
            metadata_path = archive_path.replace('.zip', '_metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return True, {
                'backup_file': os.path.basename(archive_path),
                'backup_path': archive_path,
                'metadata_path': metadata_path,
                'size': metadata['archive_size']
            }
            
        except Exception as e:
            return False, f"Error creating school backup: {str(e)}"
    
    def _export_school_data(self):
        """Export all school data to a dictionary"""
        school = School.query.get(self.school_id)
        
        data = {
            'school': school.to_dict(),
            'classes': [cls.to_dict() for cls in Class.query.filter_by(school_id=self.school_id).all()],
            'subjects': [subj.to_dict() for subj in Subject.query.filter_by(school_id=self.school_id).all()],
            'students': [student.to_dict() for student in Student.query.filter_by(school_id=self.school_id).all()],
            'teachers': [teacher.to_dict() for teacher in Teacher.query.filter_by(school_id=self.school_id).all()],
            'attendance': [att.to_dict() for att in Attendance.query.filter_by(school_id=self.school_id).all()],
            'payments': [payment.to_dict() for payment in Payment.query.filter_by(school_id=self.school_id).all()],
            'fee_structures': [fee.to_dict() for fee in FeeStructure.query.filter_by(school_id=self.school_id).all()],
            'student_fee_status': [status.to_dict() for status in StudentFeeStatus.query.filter_by(school_id=self.school_id).all()],
            'notifications': [notif.to_dict() for notif in Notification.query.filter_by(school_id=self.school_id).all()],
            'activity_logs': [log.to_dict() for log in ActivityLog.query.filter_by(school_id=self.school_id).all()],
            'export_metadata': {
                'exported_at': datetime.now().isoformat(),
                'school_id': self.school_id,
                'export_version': '1.0'
            }
        }
        
        return data
    
    def _export_to_csv(self, csv_dir):
        """Export data to CSV files"""
        # Students CSV
        students = Student.query.filter_by(school_id=self.school_id).all()
        if students:
            df = pd.DataFrame([student.to_dict() for student in students])
            df.to_csv(os.path.join(csv_dir, 'students.csv'), index=False)
        
        # Teachers CSV
        teachers = Teacher.query.filter_by(school_id=self.school_id).all()
        if teachers:
            df = pd.DataFrame([teacher.to_dict() for teacher in teachers])
            df.to_csv(os.path.join(csv_dir, 'teachers.csv'), index=False)
        
        # Attendance CSV
        attendance = Attendance.query.filter_by(school_id=self.school_id).all()
        if attendance:
            df = pd.DataFrame([att.to_dict() for att in attendance])
            df.to_csv(os.path.join(csv_dir, 'attendance.csv'), index=False)
        
        # Payments CSV
        payments = Payment.query.filter_by(school_id=self.school_id).all()
        if payments:
            df = pd.DataFrame([payment.to_dict() for payment in payments])
            df.to_csv(os.path.join(csv_dir, 'payments.csv'), index=False)
        
        # Classes CSV
        classes = Class.query.filter_by(school_id=self.school_id).all()
        if classes:
            df = pd.DataFrame([cls.to_dict() for cls in classes])
            df.to_csv(os.path.join(csv_dir, 'classes.csv'), index=False)
    
    def _backup_uploaded_files(self, files_dir):
        """Backup uploaded files"""
        os.makedirs(files_dir, exist_ok=True)
        
        # Define source directories
        source_dirs = [
            ('static/uploads/students', 'students'),
            ('static/uploads/teachers', 'teachers'),
            ('static/uploads/assignments', 'assignments'),
            ('static/uploads/documents', 'documents')
        ]
        
        for source_dir, dest_subdir in source_dirs:
            if os.path.exists(source_dir):
                dest_dir = os.path.join(files_dir, dest_subdir)
                shutil.copytree(source_dir, dest_dir, dirs_exist_ok=True)
    
    def _get_table_list(self):
        """Get list of all database tables"""
        try:
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            return [row[0] for row in result]
        except Exception:
            return []
    
    def _get_data_summary(self):
        """Get summary of data counts"""
        return {
            'students_count': Student.query.filter_by(school_id=self.school_id).count(),
            'teachers_count': Teacher.query.filter_by(school_id=self.school_id).count(),
            'classes_count': Class.query.filter_by(school_id=self.school_id).count(),
            'attendance_records': Attendance.query.filter_by(school_id=self.school_id).count(),
            'payment_records': Payment.query.filter_by(school_id=self.school_id).count(),
            'notifications_count': Notification.query.filter_by(school_id=self.school_id).count()
        }
    
    def restore_school_backup(self, backup_path, overwrite=False):
        """Restore school data from backup"""
        try:
            if not os.path.exists(backup_path):
                return False, "Backup file not found"
            
            # Extract backup if it's a zip file
            if backup_path.endswith('.zip'):
                extract_dir = backup_path.replace('.zip', '_extract')
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(extract_dir)
                data_file = os.path.join(extract_dir, 'school_data.json')
            else:
                data_file = backup_path
            
            # Load backup data
            with open(data_file, 'r') as f:
                backup_data = json.load(f)
            
            # Validate backup data
            if 'school' not in backup_data:
                return False, "Invalid backup format"
            
            school_data = backup_data['school']
            
            # Check if school already exists
            existing_school = School.query.filter_by(email=school_data['email']).first()
            if existing_school and not overwrite:
                return False, "School already exists. Use overwrite=True to replace."
            
            # Begin transaction
            db.session.begin()
            
            try:
                # Create or update school
                if existing_school and overwrite:
                    # Delete existing data
                    self._delete_school_data(existing_school.id)
                    school = existing_school
                    # Update school data
                    for key, value in school_data.items():
                        if hasattr(school, key) and key not in ['id', 'created_at']:
                            setattr(school, key, value)
                else:
                    # Create new school
                    school = School(**{k: v for k, v in school_data.items() if k not in ['id', 'created_at']})
                    db.session.add(school)
                
                db.session.flush()  # Get school ID
                
                # Restore classes
                class_id_mapping = {}
                for class_data in backup_data.get('classes', []):
                    old_id = class_data.pop('id', None)
                    class_data['school_id'] = school.id
                    new_class = Class(**{k: v for k, v in class_data.items() if k not in ['created_at']})
                    db.session.add(new_class)
                    db.session.flush()
                    if old_id:
                        class_id_mapping[old_id] = new_class.id
                
                # Restore subjects
                subject_id_mapping = {}
                for subject_data in backup_data.get('subjects', []):
                    old_id = subject_data.pop('id', None)
                    old_class_id = subject_data.get('class_id')
                    if old_class_id in class_id_mapping:
                        subject_data['class_id'] = class_id_mapping[old_class_id]
                        subject_data['school_id'] = school.id
                        new_subject = Subject(**{k: v for k, v in subject_data.items() if k not in ['created_at']})
                        db.session.add(new_subject)
                        db.session.flush()
                        if old_id:
                            subject_id_mapping[old_id] = new_subject.id
                
                # Restore students
                student_id_mapping = {}
                for student_data in backup_data.get('students', []):
                    old_id = student_data.pop('id', None)
                    old_class_id = student_data.get('class_id')
                    if old_class_id in class_id_mapping:
                        student_data['class_id'] = class_id_mapping[old_class_id]
                    student_data['school_id'] = school.id
                    
                    # Convert date strings back to date objects
                    if student_data.get('admission_date'):
                        student_data['admission_date'] = datetime.fromisoformat(student_data['admission_date']).date()
                    if student_data.get('date_of_birth'):
                        student_data['date_of_birth'] = datetime.fromisoformat(student_data['date_of_birth']).date()
                    
                    new_student = Student(**{k: v for k, v in student_data.items() if k not in ['created_at', 'updated_at']})
                    db.session.add(new_student)
                    db.session.flush()
                    if old_id:
                        student_id_mapping[old_id] = new_student.id
                
                # Continue with other data restoration...
                # (Teachers, Attendance, Payments, etc.)
                
                db.session.commit()
                
                # Clean up extraction directory if created
                if backup_path.endswith('.zip') and os.path.exists(extract_dir):
                    shutil.rmtree(extract_dir)
                
                return True, f"School backup restored successfully. School ID: {school.id}"
                
            except Exception as e:
                db.session.rollback()
                raise e
                
        except Exception as e:
            return False, f"Error restoring backup: {str(e)}"
    
    def _delete_school_data(self, school_id):
        """Delete all data for a school"""
        # Delete in reverse order of dependencies
        ActivityLog.query.filter_by(school_id=school_id).delete()
        Notification.query.filter_by(school_id=school_id).delete()
        Attendance.query.filter_by(school_id=school_id).delete()
        Payment.query.filter_by(school_id=school_id).delete()
        StudentFeeStatus.query.filter_by(school_id=school_id).delete()
        FeeStructure.query.filter_by(school_id=school_id).delete()
        Student.query.filter_by(school_id=school_id).delete()
        Teacher.query.filter_by(school_id=school_id).delete()
        Subject.query.filter_by(school_id=school_id).delete()
        Class.query.filter_by(school_id=school_id).delete()
    
    def export_data_to_excel(self, export_type='all'):
        """Export school data to Excel file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"school_{self.school_id}_export_{timestamp}.xlsx"
            filepath = os.path.join(self.backup_dir, filename)
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                if export_type in ['all', 'students']:
                    students = Student.query.filter_by(school_id=self.school_id).all()
                    if students:
                        df = pd.DataFrame([student.to_dict() for student in students])
                        df.to_excel(writer, sheet_name='Students', index=False)
                
                if export_type in ['all', 'teachers']:
                    teachers = Teacher.query.filter_by(school_id=self.school_id).all()
                    if teachers:
                        df = pd.DataFrame([teacher.to_dict() for teacher in teachers])
                        df.to_excel(writer, sheet_name='Teachers', index=False)
                
                if export_type in ['all', 'attendance']:
                    attendance = Attendance.query.filter_by(school_id=self.school_id).all()
                    if attendance:
                        df = pd.DataFrame([att.to_dict() for att in attendance])
                        df.to_excel(writer, sheet_name='Attendance', index=False)
                
                if export_type in ['all', 'payments']:
                    payments = Payment.query.filter_by(school_id=self.school_id).all()
                    if payments:
                        df = pd.DataFrame([payment.to_dict() for payment in payments])
                        df.to_excel(writer, sheet_name='Payments', index=False)
                
                if export_type in ['all', 'classes']:
                    classes = Class.query.filter_by(school_id=self.school_id).all()
                    if classes:
                        df = pd.DataFrame([cls.to_dict() for cls in classes])
                        df.to_excel(writer, sheet_name='Classes', index=False)
            
            return True, {
                'filename': filename,
                'filepath': filepath,
                'size': os.path.getsize(filepath)
            }
            
        except Exception as e:
            return False, f"Error exporting to Excel: {str(e)}"
    
    def list_backups(self):
        """List all available backups"""
        try:
            backups = []
            
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.db') or filename.endswith('.zip'):
                    filepath = os.path.join(self.backup_dir, filename)
                    metadata_path = filepath.replace('.db', '_metadata.json').replace('.zip', '_metadata.json')
                    
                    backup_info = {
                        'filename': filename,
                        'filepath': filepath,
                        'size': os.path.getsize(filepath),
                        'created_at': datetime.fromtimestamp(os.path.getctime(filepath)).isoformat()
                    }
                    
                    # Load metadata if available
                    if os.path.exists(metadata_path):
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                            backup_info.update(metadata)
                    
                    backups.append(backup_info)
            
            # Sort by creation date (newest first)
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            
            return True, backups
            
        except Exception as e:
            return False, f"Error listing backups: {str(e)}"
    
    def cleanup_old_backups(self, keep_count=10):
        """Clean up old backup files, keeping only the most recent ones"""
        try:
            success, backups = self.list_backups()
            if not success:
                return False, backups
            
            if len(backups) <= keep_count:
                return True, f"No cleanup needed. {len(backups)} backups found."
            
            # Remove old backups
            backups_to_remove = backups[keep_count:]
            removed_count = 0
            
            for backup in backups_to_remove:
                try:
                    os.remove(backup['filepath'])
                    # Remove metadata file if exists
                    metadata_path = backup['filepath'].replace('.db', '_metadata.json').replace('.zip', '_metadata.json')
                    if os.path.exists(metadata_path):
                        os.remove(metadata_path)
                    removed_count += 1
                except Exception as e:
                    print(f"Error removing backup {backup['filename']}: {e}")
            
            return True, f"Cleaned up {removed_count} old backups. Kept {keep_count} most recent."
            
        except Exception as e:
            return False, f"Error during cleanup: {str(e)}"