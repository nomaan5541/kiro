"""
Assignment and Study Material models
"""
from extensions import db
from datetime import datetime, date
from enum import Enum


class AssignmentType(Enum):
    HOMEWORK = 'homework'
    PROJECT = 'project'
    QUIZ = 'quiz'
    EXAM = 'exam'
    PRESENTATION = 'presentation'
    RESEARCH = 'research'
    PRACTICAL = 'practical'
    ASSIGNMENT = 'assignment'


class AssignmentStatus(Enum):
    DRAFT = 'draft'
    PUBLISHED = 'published'
    CLOSED = 'closed'
    ARCHIVED = 'archived'


class SubmissionStatus(Enum):
    NOT_SUBMITTED = 'not_submitted'
    SUBMITTED = 'submitted'
    LATE_SUBMITTED = 'late_submitted'
    GRADED = 'graded'
    RETURNED = 'returned'


class Assignment(db.Model):
    """Assignment model for managing homework, projects, and tasks"""
    __tablename__ = 'assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=True)
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    instructions = db.Column(db.Text)
    type = db.Column(db.Enum(AssignmentType), nullable=False, default=AssignmentType.ASSIGNMENT)
    status = db.Column(db.Enum(AssignmentStatus), nullable=False, default=AssignmentStatus.DRAFT)
    
    # Dates
    assigned_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    submission_start_date = db.Column(db.DateTime, nullable=True)
    submission_end_date = db.Column(db.DateTime, nullable=True)
    
    # Settings
    max_marks = db.Column(db.Integer, default=100)
    allow_late_submission = db.Column(db.Boolean, default=False)
    late_penalty_percent = db.Column(db.Integer, default=10)
    allow_multiple_submissions = db.Column(db.Boolean, default=False)
    show_grades_to_students = db.Column(db.Boolean, default=True)
    
    # File settings
    max_file_size_mb = db.Column(db.Integer, default=10)
    allowed_file_types = db.Column(db.String(500))  # JSON string of allowed extensions
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    school = db.relationship('School', backref='assignments')
    teacher = db.relationship('Teacher', backref='assignments')
    class_info = db.relationship('Class', backref='assignments')
    subject = db.relationship('Subject', backref='assignments')
    submissions = db.relationship('AssignmentSubmission', backref='assignment', cascade='all, delete-orphan')
    attachments = db.relationship('AssignmentAttachment', backref='assignment', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Assignment {self.title}>'
    
    def is_overdue(self):
        """Check if assignment is overdue"""
        return datetime.utcnow() > self.due_date
    
    def days_until_due(self):
        """Get days until due date"""
        if self.is_overdue():
            return 0
        return (self.due_date - datetime.utcnow()).days
    
    def get_submission_count(self):
        """Get total number of submissions"""
        return len([s for s in self.submissions if s.status != SubmissionStatus.NOT_SUBMITTED])
    
    def get_pending_count(self):
        """Get number of pending submissions"""
        return len([s for s in self.submissions if s.status == SubmissionStatus.NOT_SUBMITTED])
    
    def get_graded_count(self):
        """Get number of graded submissions"""
        return len([s for s in self.submissions if s.status == SubmissionStatus.GRADED])
    
    def publish(self):
        """Publish the assignment"""
        self.status = AssignmentStatus.PUBLISHED
        self.published_at = datetime.utcnow()
    
    def archive(self):
        """Archive the assignment"""
        self.status = AssignmentStatus.ARCHIVED
    
    def get_submission_stats(self):
        """Get submission statistics"""
        from models.student import Student
        
        # Get all students in the class
        total_students = Student.query.filter_by(class_id=self.class_id).count()
        
        # Get submissions
        submissions = AssignmentSubmission.query.filter_by(assignment_id=self.id).all()
        submitted_count = len(submissions)
        graded_count = len([s for s in submissions if s.status == SubmissionStatus.GRADED])
        late_count = len([s for s in submissions if s.status == SubmissionStatus.LATE_SUBMITTED])
        
        return {
            'total_students': total_students,
            'submitted': submitted_count,
            'pending': total_students - submitted_count,
            'graded': graded_count,
            'late': late_count,
            'submission_rate': (submitted_count / max(total_students, 1)) * 100
        }
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'type': self.type.value,
            'status': self.status.value,
            'assigned_date': self.assigned_date.isoformat() if self.assigned_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'max_marks': self.max_marks,
            'is_overdue': self.is_overdue(),
            'days_until_due': self.days_until_due(),
            'submission_count': self.get_submission_count(),
            'pending_count': self.get_pending_count(),
            'teacher_name': self.teacher.user.name if self.teacher and self.teacher.user else None,
            'class_name': self.class_info.get_display_name() if self.class_info else None,
            'subject_name': self.subject.name if self.subject else None
        }


class AssignmentSubmission(db.Model):
    """Student submissions for assignments"""
    __tablename__ = 'assignment_submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    
    # Submission details
    status = db.Column(db.Enum(SubmissionStatus), nullable=False, default=SubmissionStatus.NOT_SUBMITTED)
    submission_text = db.Column(db.Text, nullable=True)  # Text submission
    
    # Grading
    marks_obtained = db.Column(db.Integer, nullable=True)
    grade = db.Column(db.String(10), nullable=True)  # A+, A, B+, etc.
    teacher_feedback = db.Column(db.Text, nullable=True)
    
    # Timestamps
    submitted_at = db.Column(db.DateTime, nullable=True)
    graded_at = db.Column(db.DateTime, nullable=True)
    returned_at = db.Column(db.DateTime, nullable=True)
    graded_by = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=True)
    
    # Metadata
    submission_count = db.Column(db.Integer, default=1)  # Number of times resubmitted
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = db.relationship('Student', backref='assignment_submissions', lazy=True)
    grader = db.relationship('Teacher', foreign_keys=[graded_by])
    attachments = db.relationship('SubmissionAttachment', backref='submission', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<AssignmentSubmission {self.assignment.title} by {self.student.name}>'
    
    def submit(self):
        """Mark submission as submitted"""
        self.status = SubmissionStatus.LATE_SUBMITTED if self.assignment.is_overdue() else SubmissionStatus.SUBMITTED
        self.submitted_at = datetime.utcnow()
    
    def grade(self, marks, grade, feedback=None):
        """Grade the submission"""
        self.marks_obtained = marks
        self.grade = grade
        self.teacher_feedback = feedback
        self.status = SubmissionStatus.GRADED
        self.graded_at = datetime.utcnow()
    
    def return_to_student(self):
        """Return graded submission to student"""
        self.status = SubmissionStatus.RETURNED
        self.returned_at = datetime.utcnow()
    
    @property
    def is_late(self):
        """Check if submission was late"""
        return self.status == SubmissionStatus.LATE_SUBMITTED
    
    @property
    def percentage(self):
        """Get percentage score"""
        if self.marks_obtained is not None and self.assignment.max_marks:
            return (self.marks_obtained / self.assignment.max_marks) * 100
        return None
    
    def to_dict(self):
        """Convert submission to dictionary"""
        return {
            'id': self.id,
            'assignment_id': self.assignment_id,
            'student_id': self.student_id,
            'status': self.status.value,
            'submission_text': self.submission_text,
            'marks_obtained': self.marks_obtained,
            'grade': self.grade,
            'teacher_feedback': self.teacher_feedback,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'graded_at': self.graded_at.isoformat() if self.graded_at else None,
            'returned_at': self.returned_at.isoformat() if self.returned_at else None,
            'submission_count': self.submission_count,
            'is_late': self.is_late,
            'percentage': self.percentage,
            'student_name': self.student.name if self.student else None,
            'assignment_title': self.assignment.title if self.assignment else None
        }


class AssignmentAttachment(db.Model):
    """Files attached to assignments by teachers"""
    __tablename__ = 'assignment_attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'), nullable=False)
    
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # in bytes
    mime_type = db.Column(db.String(100), nullable=False)
    
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    
    # Relationships
    uploader = db.relationship('Teacher', foreign_keys=[uploaded_by])
    
    def __repr__(self):
        return f'<AssignmentAttachment {self.original_filename}>'
    
    def get_file_size_mb(self):
        """Get file size in MB"""
        return round(self.file_size / (1024 * 1024), 2)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'file_size_mb': self.get_file_size_mb(),
            'mime_type': self.mime_type,
            'uploaded_at': self.uploaded_at.isoformat()
        }


class SubmissionAttachment(db.Model):
    """Files attached to submissions by students"""
    __tablename__ = 'submission_attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('assignment_submissions.id'), nullable=False)
    
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # in bytes
    mime_type = db.Column(db.String(100), nullable=False)
    
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SubmissionAttachment {self.original_filename}>'
    
    def get_file_size_mb(self):
        """Get file size in MB"""
        return round(self.file_size / (1024 * 1024), 2)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'file_size_mb': self.get_file_size_mb(),
            'mime_type': self.mime_type,
            'uploaded_at': self.uploaded_at.isoformat()
        }


class StudyMaterial(db.Model):
    """Study materials shared by teachers"""
    __tablename__ = 'study_materials'
    
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=True)
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    content = db.Column(db.Text)  # For text-based materials
    
    # Categories
    category = db.Column(db.String(50), default='general')  # notes, slides, videos, books, etc.
    tags = db.Column(db.String(500))  # JSON string of tags
    
    # Access control
    is_public = db.Column(db.Boolean, default=False)  # Visible to all classes
    is_downloadable = db.Column(db.Boolean, default=True)
    
    # Metadata
    view_count = db.Column(db.Integer, default=0)
    download_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    school = db.relationship('School', backref='study_materials')
    teacher = db.relationship('Teacher', backref='study_materials')
    class_info = db.relationship('Class', backref='study_materials')
    subject = db.relationship('Subject', backref='study_materials')
    attachments = db.relationship('StudyMaterialAttachment', backref='study_material', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<StudyMaterial {self.title}>'
    
    def get_tags_list(self):
        """Get tags as list"""
        if not self.tags:
            return []
        try:
            import json
            return json.loads(self.tags)
        except:
            return []
    
    def increment_view_count(self):
        """Increment view count"""
        self.view_count += 1
        db.session.commit()
    
    def increment_download_count(self):
        """Increment download count"""
        self.download_count += 1
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'tags': self.get_tags_list(),
            'is_public': self.is_public,
            'is_downloadable': self.is_downloadable,
            'created_at': self.created_at.isoformat(),
            'teacher_name': self.teacher.user.name if self.teacher and self.teacher.user else None,
            'class_name': self.class_info.get_display_name() if self.class_info else None,
            'subject_name': self.subject.name if self.subject else 'General',
            'attachment_count': len(self.attachments)
        }


class StudyMaterialAttachment(db.Model):
    """Files attached to study materials"""
    __tablename__ = 'study_material_attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    study_material_id = db.Column(db.Integer, db.ForeignKey('study_materials.id'), nullable=False)
    
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # in bytes
    mime_type = db.Column(db.String(100), nullable=False)
    
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<StudyMaterialAttachment {self.original_filename}>'
    
    def get_file_size_mb(self):
        """Get file size in MB"""
        return round(self.file_size / (1024 * 1024), 2)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'file_size_mb': self.get_file_size_mb(),
            'mime_type': self.mime_type,
            'uploaded_at': self.uploaded_at.isoformat()
        }