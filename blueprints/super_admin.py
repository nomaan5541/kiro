"""
Super Admin Blueprint - Handles school registration and management
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from extensions import db, bcrypt
from models.user import User, UserRole
from models.school import School, SchoolStatus
from utils.auth import login_required, role_required
from datetime import datetime, timedelta

super_admin_bp = Blueprint('super_admin', __name__)


@super_admin_bp.route('/dashboard')
@role_required('super_admin')
def dashboard():
    """Super admin dashboard"""
    user = User.query.get(session['user_id'])
    
    # Calculate KPIs
    total_schools = School.query.count()
    active_subscriptions = School.query.filter(
        School.subscription_end > datetime.utcnow(),
        School.status == SchoolStatus.ACTIVE
    ).count()
    expired_subscriptions = School.query.filter(
        School.subscription_end <= datetime.utcnow()
    ).count()
    suspended_accounts = School.query.filter_by(status=SchoolStatus.SUSPENDED).count()
    
    # Get recent schools
    recent_schools = School.query.order_by(School.created_at.desc()).limit(10).all()
    
    return render_template('super_admin/dashboard.html',
                         user=user,
                         total_schools=total_schools,
                         active_subscriptions=active_subscriptions,
                         expired_subscriptions=expired_subscriptions,
                         suspended_accounts=suspended_accounts,
                         recent_schools=recent_schools)


@super_admin_bp.route('/register-school', methods=['GET', 'POST'])
@role_required('super_admin')
def register_school():
    """Register a new school"""
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        # Get form data
        school_name = request.form.get('school_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address', '')
        
        # Admin account data
        admin_name = request.form.get('admin_name')
        admin_email = request.form.get('admin_email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Subscription data
        subscription_start = request.form.get('subscription_start')
        subscription_end = request.form.get('subscription_end')
        
        # Calculate dates for template
        today = datetime.utcnow().date()
        one_year_later = today + timedelta(days=365)
        
        # Validation
        if not all([school_name, email, phone, admin_name, admin_email, password, confirm_password]):
            flash('All required fields must be filled', 'error')
            return render_template('super_admin/register_school.html', 
                                 user=user, today=today, one_year_later=one_year_later)
        
        # Password confirmation
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('super_admin/register_school.html', 
                                 user=user, today=today, one_year_later=one_year_later)
        
        # Check if emails already exist
        if User.query.filter_by(email=admin_email).first():
            flash('Admin email already exists', 'error')
            return render_template('super_admin/register_school.html', 
                                 user=user, today=today, one_year_later=one_year_later)
        
        if School.query.filter_by(email=email).first():
            flash('School email already exists', 'error')
            return render_template('super_admin/register_school.html', 
                                 user=user, today=today, one_year_later=one_year_later)
        
        try:
            # Parse subscription dates
            start_date = datetime.strptime(subscription_start, '%Y-%m-%d').date() if subscription_start else today
            end_date = datetime.strptime(subscription_end, '%Y-%m-%d').date() if subscription_end else (today + timedelta(days=365))
            
            # Create school record
            school = School(
                name=school_name,
                email=email,
                phone=phone,
                address=address,
                subscription_start=start_date,
                subscription_end=end_date,
                status=SchoolStatus.ACTIVE
            )
            db.session.add(school)
            db.session.flush()  # Get school ID
            
            # Create school admin user
            password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
            school_admin = User(
                name=admin_name,
                email=admin_email,
                password_hash=password_hash,
                role=UserRole.SCHOOL_ADMIN,
                school_id=school.id
            )
            db.session.add(school_admin)
            db.session.commit()
            
            flash(f'School "{school_name}" registered successfully with admin account for {admin_name}', 'success')
            return redirect(url_for('super_admin.schools'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error registering school: {str(e)}', 'error')
    
    # Calculate dates for template
    today = datetime.utcnow().date()
    one_year_later = today + timedelta(days=365)
    
    return render_template('super_admin/register_school.html', 
                         user=user,
                         today=today,
                         one_year_later=one_year_later)


@super_admin_bp.route('/schools')
@role_required('super_admin')
def schools():
    """List all schools"""
    user = User.query.get(session['user_id'])
    
    page = request.args.get('page', 1, type=int)
    schools = School.query.order_by(School.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Calculate statistics for the template
    active_schools = School.query.filter_by(status=SchoolStatus.ACTIVE).count()
    expiring_soon = School.query.filter(
        School.subscription_end <= datetime.utcnow() + timedelta(days=30),
        School.subscription_end > datetime.utcnow()
    ).count()
    total_revenue = 0  # Placeholder - calculate from payments if needed
    
    return render_template('super_admin/schools.html', 
                         user=user, 
                         schools=schools,
                         active_schools=active_schools,
                         expiring_soon=expiring_soon,
                         total_revenue=total_revenue,
                         today=datetime.utcnow().date())


@super_admin_bp.route('/users')
@role_required('super_admin')
def users():
    """User management dashboard"""
    user = User.query.get(session['user_id'])
    
    # Get search and filter parameters
    search = request.args.get('search', '')
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    
    # Build query
    query = User.query
    
    # Apply filters
    if search:
        query = query.filter(
            db.or_(
                User.name.contains(search),
                User.email.contains(search)
            )
        )
    
    if role_filter:
        query = query.filter_by(role=UserRole(role_filter))
    
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)
    
    # Paginate results
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=25, error_out=False
    )
    
    # Get schools for display
    schools = {school.id: school for school in School.query.all()}
    
    return render_template('super_admin/users.html', 
                         user=user,
                         users=users, 
                         schools=schools,
                         search=search,
                         role_filter=role_filter,
                         status_filter=status_filter)


@super_admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@role_required('super_admin')
def toggle_user_status(user_id):
    """Toggle user active status"""
    try:
        target_user = User.query.get_or_404(user_id)
        target_user.is_active = not target_user.is_active
        db.session.commit()
        
        status = "activated" if target_user.is_active else "deactivated"
        flash(f'User {target_user.name} has been {status}', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating user status: {str(e)}', 'error')
    
    return redirect(url_for('super_admin.users'))


@super_admin_bp.route('/settings')
@role_required('super_admin')
def settings():
    """System settings management"""
    user = User.query.get(session['user_id'])
    
    # Get system statistics
    stats = {
        'total_users': User.query.count(),
        'total_schools': School.query.count(),
        'active_schools': School.query.filter_by(status=SchoolStatus.ACTIVE).count(),
        'total_students': 0,  # Will be calculated from all schools
        'database_size': '2.3 GB',  # Placeholder
        'uptime': '15 days, 3 hours',  # Placeholder
    }
    
    # Calculate total students across all schools
    from models.student import Student
    stats['total_students'] = Student.query.count()
    
    return render_template('super_admin/settings.html', user=user, stats=stats)


@super_admin_bp.route('/reports')
@role_required('super_admin')
def reports():
    """System reports dashboard"""
    user = User.query.get(session['user_id'])
    
    # Calculate comprehensive statistics
    from models.student import Student
    from models.teacher import Teacher
    from models.fee import Payment
    from decimal import Decimal
    
    stats = {
        'total_schools': School.query.count(),
        'active_schools': School.query.filter_by(status=SchoolStatus.ACTIVE).count(),
        'total_users': User.query.count(),
        'total_students': Student.query.count(),
        'total_teachers': Teacher.query.count(),
        'total_revenue': Decimal('0.00'),
        'monthly_growth': 12.5,  # Placeholder percentage
        'subscription_renewal_rate': 85.2,  # Placeholder percentage
    }
    
    # Calculate total revenue
    payments = Payment.query.all()
    stats['total_revenue'] = sum(payment.amount for payment in payments)
    
    # Get recent activity data
    recent_schools = School.query.order_by(School.created_at.desc()).limit(5).all()
    
    # School growth data (placeholder)
    growth_data = [
        {'month': 'Jan', 'schools': 45, 'revenue': 125000},
        {'month': 'Feb', 'schools': 52, 'revenue': 142000},
        {'month': 'Mar', 'schools': 58, 'revenue': 158000},
        {'month': 'Apr', 'schools': 63, 'revenue': 172000},
        {'month': 'May', 'schools': 71, 'revenue': 195000},
        {'month': 'Jun', 'schools': 78, 'revenue': 215000},
    ]
    
    return render_template('super_admin/reports.html', 
                         user=user,
                         stats=stats,
                         recent_schools=recent_schools,
                         growth_data=growth_data,
                         now=datetime.utcnow())


@super_admin_bp.route('/activity-logs')
@role_required('super_admin')
def activity_logs():
    """System activity logs"""
    user = User.query.get(session['user_id'])
    
    # Get filter parameters
    date_filter = request.args.get('date', '')
    user_filter = request.args.get('user', '')
    action_filter = request.args.get('action', '')
    page = request.args.get('page', 1, type=int)
    
    # Build query for activity logs
    from models.activity import ActivityLog
    query = ActivityLog.query
    
    # Apply filters
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter(db.func.date(ActivityLog.created_at) == filter_date)
        except ValueError:
            pass
    
    if user_filter:
        query = query.filter(ActivityLog.user_id == user_filter)
    
    if action_filter:
        query = query.filter(ActivityLog.activity_type.contains(action_filter))
    
    # Paginate results
    activities = query.order_by(ActivityLog.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    # Get users for filter dropdown
    users_list = User.query.all()
    
    return render_template('super_admin/activity_logs.html',
                         user=user,
                         activities=activities,
                         users_list=users_list,
                         date_filter=date_filter,
                         user_filter=user_filter,
                         action_filter=action_filter)


@super_admin_bp.route('/schools/<int:school_id>/toggle-status', methods=['POST'])
@role_required('super_admin')
def toggle_school_status(school_id):
    """Toggle school status"""
    try:
        school = School.query.get_or_404(school_id)
        
        if school.status == SchoolStatus.ACTIVE:
            school.status = SchoolStatus.SUSPENDED
            status_msg = 'suspended'
        else:
            school.status = SchoolStatus.ACTIVE
            status_msg = 'activated'
        
        db.session.commit()
        flash(f'School {school.name} has been {status_msg}', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating school status: {str(e)}', 'error')
    
    return redirect(url_for('super_admin.schools'))


@super_admin_bp.route('/schools/<int:school_id>/extend-subscription', methods=['POST'])
@role_required('super_admin')
def extend_subscription(school_id):
    """Extend school subscription"""
    try:
        school = School.query.get_or_404(school_id)
        months = int(request.form.get('months', 12))
        
        # Extend subscription
        if school.subscription_end > datetime.utcnow():
            # Extend from current end date
            school.subscription_end += timedelta(days=months * 30)
        else:
            # Extend from now
            school.subscription_end = datetime.utcnow() + timedelta(days=months * 30)
        
        db.session.commit()
        flash(f'Subscription extended for {school.name} by {months} months', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error extending subscription: {str(e)}', 'error')
    
    return redirect(url_for('super_admin.schools'))