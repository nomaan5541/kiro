#!/usr/bin/env python3
"""Check database configuration and contents"""

from app import create_app
from extensions import db
from models.user import User, UserRole

def check_database():
    app = create_app()
    
    with app.app_context():
        print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        # Check users in database
        users = User.query.all()
        print(f"\nTotal users: {len(users)}")
        
        for user in users:
            print(f"- {user.email} ({user.role.value}) - Active: {user.is_active}")
        
        # Check for specific user
        admin_user = User.query.filter_by(email='demo@school.com', role=UserRole.SCHOOL_ADMIN).first()
        print(f"\nDemo school admin exists: {admin_user is not None}")

if __name__ == '__main__':
    check_database()