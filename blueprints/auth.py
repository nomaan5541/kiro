"""
Authentication Blueprint - Handles login, logout, and authentication
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from extensions import db, bcrypt
from models.user import User, UserRole
from models.school import School
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Main login page with role-based tabs"""
    if request.method == 'POST':
        role = request.form.get('role', 'student')
        
        if role == 'student':
            return handle_student_login()
        elif role == 'teacher':
            return handle_teacher_login()
        elif role == 'admin':
            return handle_admin_login()
    
    return render_template('auth/login.html')


@auth_bp.route('/super-login', methods=['GET', 'POST'])
def super_login():
    """Hidden super admin login page"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('auth/super_login.html')
        
        # Find super admin user
        user = User.query.filter_by(email=email, role=UserRole.SUPER_ADMIN).first()
        
        if user and bcrypt.check_password_hash(user.password_hash, password):
            # Store user in session
            session['user_id'] = user.id
            session['user_role'] = user.role.value
            return redirect(url_for('super_admin.dashboard'))
        else:
            flash('Invalid super admin credentials', 'error')
    
    return render_template('auth/super_login.html')


def handle_student_login():
    """Handle student login with admission number, phone, and DOB"""
    admission_no = request.form.get('admission_no')
    phone = request.form.get('phone')
    dob = request.form.get('dob')
    
    if not all([admission_no, phone, dob]):
        flash('All fields are required for student login', 'error')
        return render_template('auth/login.html')
    
    # For demo purposes, accept specific test credentials
    if admission_no == 'STU001' and phone == '9876543210' and dob == '2010-01-15':
        # Find student user
        user = User.query.filter_by(role=UserRole.STUDENT).first()
        if user:
            # Store user in session
            session['user_id'] = user.id
            session['user_role'] = user.role.value
            return redirect(url_for('student.dashboard'))
    
    flash('Invalid student credentials. Use: Admission: STU001, Phone: 9876543210, DOB: 2010-01-15', 'error')
    return render_template('auth/login.html')


def handle_teacher_login():
    """Handle teacher login with email and password"""
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not email or not password:
        flash('Email and password are required', 'error')
        return render_template('auth/login.html')
    
    user = User.query.filter_by(email=email, role=UserRole.TEACHER).first()
    
    if user and bcrypt.check_password_hash(user.password_hash, password):
        # Store user in session
        session['user_id'] = user.id
        session['user_role'] = user.role.value
        return redirect(url_for('teacher.dashboard'))
    else:
        flash('Invalid teacher credentials', 'error')
        return render_template('auth/login.html')


def handle_admin_login():
    """Handle school admin login with email and password"""
    email = request.form.get('email')
    password = request.form.get('password')
    
    print(f"DEBUG: Admin login attempt - Email: {email}, Password provided: {bool(password)}")
    print(f"DEBUG: Database URI: {db.engine.url}")
    
    if not email or not password:
        print("DEBUG: Missing email or password")
        flash('Email and password are required', 'error')
        return render_template('auth/login.html')
    
    user = User.query.filter_by(email=email, role=UserRole.SCHOOL_ADMIN).first()
    print(f"DEBUG: User found: {bool(user)}")
    
    # Debug: Check all users in database
    all_users = User.query.all()
    print(f"DEBUG: Total users in database: {len(all_users)}")
    for u in all_users:
        print(f"DEBUG: User - Email: {u.email}, Role: {u.role.value}")
    
    # Debug: Check specific email query
    email_users = User.query.filter_by(email=email).all()
    print(f"DEBUG: Users with email {email}: {len(email_users)}")
    for u in email_users:
        print(f"DEBUG: Found user - Email: {u.email}, Role: {u.role.value}")
    
    if user:
        print(f"DEBUG: User password hash: {user.password_hash}")
        print(f"DEBUG: Provided password: {password}")
        password_check = bcrypt.check_password_hash(user.password_hash, password)
        print(f"DEBUG: Password check result: {password_check}")
        
        # Test with a fresh hash
        test_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        test_check = bcrypt.check_password_hash(test_hash, password)
        print(f"DEBUG: Fresh hash test: {test_check}")
        
        if password_check:
            # Store user in session
            session['user_id'] = user.id
            session['user_role'] = user.role.value
            print(f"DEBUG: Login successful, redirecting to dashboard")
            return redirect(url_for('school_admin.dashboard'))
    
    print("DEBUG: Login failed - invalid credentials")
    flash('Invalid admin credentials', 'error')
    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('auth.login'))


# Removed temporary bypass routes for production


@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    """API endpoint for login"""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if user and bcrypt.check_password_hash(user.password_hash, data['password']):
        access_token = create_access_token(identity=user.id)
        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role
            }
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401