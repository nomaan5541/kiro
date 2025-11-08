"""
Assignment Service for managing assignments and study materials
"""
import os
from datetime import datetime, date
from flask import current_app
from werkzeug.utils import secure_filename
from models.assignment import Assignment, AssignmentAttachment, StudyMaterial, StudyMaterialAttachment
from models.assignment import AssignmentSubmission, SubmissionAttachment, AssignmentType, AssignmentStatus
from models.student import Student
from models.classes import Class
from extensions import db


class AssignmentService:
    """Service for managing assignments and study materials"""
    
    def __init__(self, school_id):
        self.school_id = school_id
    
    def create_assignment(self, teacher_id, assignment_data, files=None):
        """Create a new assignment"""
        try:
            # Create assignment
            assignment = Assignment(
                school_id=self.school_id,
                teacher_id=teacher_id,
                class_id=assignment_data['class_id'],
                subject_id=assignment_data.get('subject_id'),
                title=assignment_data['title'],
                description=assignment_data.get('description'),
                instructions=assignment_data.get('instructions'),
                type=AssignmentType(assignment_data.get('type', 'assignment')),
                status=AssignmentStatus(assignment_data.get('status', 'published')),
                due_date=datetime.strptime(assignment_data['due_date'], '%Y-%m-%dT%H:%M') if assignment_data.get('due_date') else None,
                max_marks=int(assignment_data.get('max_marks', 100)),
                allow_late_submission=assignment_data.get('allow_late_submission', False),
                allow_multiple_submissions=assignment_data.get('allow_multiple_submissions', False),
                show_grades_to_students=assignment_data.get('show_grades_to_students', True),
                max_file_size_mb=int(assignment_data.get('max_file_size_mb', 10)),
                allowed_file_types=assignment_data.get('allowed_file_types', '.pdf,.doc,.docx,.txt')
            )
            
            db.session.add(assignment)
            db.session.flush()  # Get assignment ID
            
            # Handle file attachments
            if files:
                for file in files:
                    if file and file.filename:
                        attachment = self._save_assignment_attachment(assignment.id, file, teacher_id)
                        if attachment:
                            assignment.attachments.append(attachment)
            
            # Create submission records for all students in the class
            students = Student.query.filter_by(class_id=assignment.class_id, status='active').all()
            for student in students:
                submission = AssignmentSubmission(
                    assignment_id=assignment.id,
                    student_id=student.id,
                    school_id=self.school_id
                )
                db.session.add(submission)
            
            db.session.commit()
            return {'success': True, 'assignment_id': assignment.id}
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': str(e)}
    
    def update_assignment(self, assignment_id, teacher_id, assignment_data, files=None):
        """Update an existing assignment"""
        try:
            assignment = Assignment.query.filter_by(
                id=assignment_id,
                teacher_id=teacher_id,
                school_id=self.school_id
            ).first()
            
            if not assignment:
                return {'success': False, 'message': 'Assignment not found'}
            
            # Update assignment fields
            assignment.title = assignment_data.get('title', assignment.title)
            assignment.description = assignment_data.get('description', assignment.description)
            assignment.instructions = assignment_data.get('instructions', assignment.instructions)
            assignment.type = AssignmentType(assignment_data.get('type', assignment.type.value))
            assignment.status = AssignmentStatus(assignment_data.get('status', assignment.status.value))
            
            if assignment_data.get('due_date'):\n                assignment.due_date = datetime.strptime(assignment_data['due_date'], '%Y-%m-%dT%H:%M')
            
            assignment.max_marks = int(assignment_data.get('max_marks', assignment.max_marks))
            assignment.allow_late_submission = assignment_data.get('allow_late_submission', assignment.allow_late_submission)
            assignment.allow_multiple_submissions = assignment_data.get('allow_multiple_submissions', assignment.allow_multiple_submissions)
            assignment.show_grades_to_students = assignment_data.get('show_grades_to_students', assignment.show_grades_to_students)
            
            # Handle new file attachments
            if files:
                for file in files:
                    if file and file.filename:
                        attachment = self._save_assignment_attachment(assignment.id, file, teacher_id)
                        if attachment:
                            assignment.attachments.append(attachment)
            
            db.session.commit()
            return {'success': True, 'assignment_id': assignment.id}
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': str(e)}
    
    def delete_assignment(self, assignment_id, teacher_id):
        """Delete an assignment"""
        try:
            assignment = Assignment.query.filter_by(
                id=assignment_id,
                teacher_id=teacher_id,
                school_id=self.school_id
            ).first()
            
            if not assignment:
                return {'success': False, 'message': 'Assignment not found'}
            
            # Delete associated files
            for attachment in assignment.attachments:
                self._delete_file(attachment.file_path)
            
            # Delete assignment (cascades to submissions and attachments)
            db.session.delete(assignment)
            db.session.commit()
            
            return {'success': True}
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': str(e)}
    
    def get_teacher_assignments(self, teacher_id, status=None, class_id=None):
        """Get assignments for a teacher"""
        query = Assignment.query.filter_by(
            teacher_id=teacher_id,
            school_id=self.school_id
        )
        
        if status:
            query = query.filter_by(status=AssignmentStatus(status))
        
        if class_id:
            query = query.filter_by(class_id=class_id)
        
        return query.order_by(Assignment.created_at.desc()).all()
    
    def get_assignment_statistics(self, teacher_id):
        """Get assignment statistics for a teacher"""
        assignments = self.get_teacher_assignments(teacher_id)
        
        total = len(assignments)
        active = len([a for a in assignments if a.status == AssignmentStatus.PUBLISHED])
        overdue = len([a for a in assignments if a.is_overdue() and a.status == AssignmentStatus.PUBLISHED])
        
        pending_submissions = sum(a.get_pending_count() for a in assignments)
        to_grade = sum(len([s for s in a.submissions if s.status.value == 'submitted']) for a in assignments)
        
        return {
            'total': total,
            'active': active,
            'overdue': overdue,
            'pending_submissions': pending_submissions,
            'to_grade': to_grade
        }
    
    def get_assignment_submissions(self, assignment_id, teacher_id):
        """Get submissions for an assignment"""
        assignment = Assignment.query.filter_by(
            id=assignment_id,
            teacher_id=teacher_id,
            school_id=self.school_id
        ).first()
        
        if not assignment:
            return None
        
        return assignment.submissions
    
    def grade_submission(self, submission_id, teacher_id, marks, grade, feedback):
        """Grade a student submission"""
        try:
            submission = AssignmentSubmission.query.join(Assignment).filter(
                AssignmentSubmission.id == submission_id,
                Assignment.teacher_id == teacher_id,
                Assignment.school_id == self.school_id
            ).first()
            
            if not submission:
                return {'success': False, 'message': 'Submission not found'}
            
            submission.marks_obtained = int(marks) if marks else None
            submission.grade = grade
            submission.feedback = feedback
            submission.graded_at = datetime.utcnow()
            submission.graded_by = teacher_id
            submission.status = 'graded'
            
            db.session.commit()
            return {'success': True}
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': str(e)}
    
    def create_study_material(self, teacher_id, material_data, files=None):
        """Create study material"""
        try:
            material = StudyMaterial(
                school_id=self.school_id,
                teacher_id=teacher_id,
                class_id=material_data.get('class_id'),
                subject_id=material_data.get('subject_id'),
                title=material_data['title'],
                description=material_data.get('description'),
                content=material_data.get('content'),
                category=material_data.get('category', 'general'),
                tags=material_data.get('tags'),
                is_public=material_data.get('is_public', False),
                is_downloadable=material_data.get('is_downloadable', True)
            )
            
            db.session.add(material)
            db.session.flush()
            
            # Handle file attachments
            if files:
                for file in files:
                    if file and file.filename:
                        attachment = self._save_study_material_attachment(material.id, file)
                        if attachment:
                            material.attachments.append(attachment)
            
            db.session.commit()
            return {'success': True, 'material_id': material.id}
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': str(e)}
    
    def get_study_materials(self, teacher_id=None, class_id=None, subject_id=None):
        """Get study materials"""
        query = StudyMaterial.query.filter_by(school_id=self.school_id)
        
        if teacher_id:
            query = query.filter_by(teacher_id=teacher_id)
        
        if class_id:
            query = query.filter((StudyMaterial.class_id == class_id) | (StudyMaterial.is_public == True))
        
        if subject_id:
            query = query.filter_by(subject_id=subject_id)
        
        return query.order_by(StudyMaterial.created_at.desc()).all()
    
    def _save_assignment_attachment(self, assignment_id, file, teacher_id):
        """Save assignment attachment file"""
        try:
            # Create upload directory
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'assignments')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate secure filename
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{assignment_id}_{timestamp}_{filename}"
            file_path = os.path.join(upload_dir, unique_filename)
            
            # Save file
            file.save(file_path)
            
            # Create attachment record
            attachment = AssignmentAttachment(
                assignment_id=assignment_id,
                filename=unique_filename,
                original_filename=filename,
                file_path=file_path,
                file_size=os.path.getsize(file_path),
                mime_type=file.content_type or 'application/octet-stream',
                uploaded_by=teacher_id
            )
            
            return attachment
            
        except Exception as e:
            print(f"Error saving assignment attachment: {e}")
            return None
    
    def _save_study_material_attachment(self, material_id, file):
        """Save study material attachment file"""
        try:
            # Create upload directory
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'study_materials')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate secure filename
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{material_id}_{timestamp}_{filename}"
            file_path = os.path.join(upload_dir, unique_filename)
            
            # Save file
            file.save(file_path)
            
            # Create attachment record
            attachment = StudyMaterialAttachment(
                study_material_id=material_id,
                filename=unique_filename,
                original_filename=filename,
                file_path=file_path,
                file_size=os.path.getsize(file_path),
                mime_type=file.content_type or 'application/octet-stream'
            )
            
            return attachment
            
        except Exception as e:
            print(f"Error saving study material attachment: {e}")
            return None
    
    def _delete_file(self, file_path):
        """Delete a file from filesystem"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
    
    def get_student_assignments(self, student_id, class_id):
        """Get assignments for a student"""
        assignments = Assignment.query.filter_by(
            class_id=class_id,
            school_id=self.school_id,
            status=AssignmentStatus.PUBLISHED
        ).order_by(Assignment.due_date.asc()).all()
        
        # Get submission status for each assignment
        for assignment in assignments:
            submission = AssignmentSubmission.query.filter_by(
                assignment_id=assignment.id,
                student_id=student_id
            ).first()
            assignment.submission = submission
        
        return assignments
    
    def submit_assignment(self, assignment_id, student_id, submission_text=None, files=None):
        """Submit assignment by student"""
        try:
            # Get submission record
            submission = AssignmentSubmission.query.filter_by(
                assignment_id=assignment_id,
                student_id=student_id
            ).first()
            
            if not submission:
                return {'success': False, 'message': 'Submission record not found'}
            
            # Check if assignment allows multiple submissions
            assignment = Assignment.query.get(assignment_id)
            if not assignment.allow_multiple_submissions and submission.status.value != 'not_submitted':
                return {'success': False, 'message': 'Multiple submissions not allowed'}
            
            # Update submission
            submission.submission_text = submission_text
            submission.submitted_at = datetime.utcnow()
            submission.last_modified_at = datetime.utcnow()
            
            # Determine submission status
            if assignment.due_date and datetime.utcnow() > assignment.due_date:
                submission.status = 'late_submitted'
            else:
                submission.status = 'submitted'
            
            # Handle file attachments
            if files:
                for file in files:
                    if file and file.filename:
                        attachment = self._save_submission_attachment(submission.id, file)
                        if attachment:
                            submission.attachments.append(attachment)
            
            db.session.commit()
            return {'success': True}
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': str(e)}
    
    def _save_submission_attachment(self, submission_id, file):
        """Save submission attachment file"""
        try:
            # Create upload directory
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'submissions')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate secure filename
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{submission_id}_{timestamp}_{filename}"
            file_path = os.path.join(upload_dir, unique_filename)
            
            # Save file
            file.save(file_path)
            
            # Create attachment record
            attachment = SubmissionAttachment(
                submission_id=submission_id,
                filename=unique_filename,
                original_filename=filename,
                file_path=file_path,
                file_size=os.path.getsize(file_path),
                mime_type=file.content_type or 'application/octet-stream'
            )
            
            return attachment
            
        except Exception as e:
            print(f"Error saving submission attachment: {e}")
            return None