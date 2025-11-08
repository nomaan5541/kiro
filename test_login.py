#!/usr/bin/env python3
"""Test script to check login credentials"""

from app import create_app
from extensions import db, bcrypt
from models.user import User, UserRole

def test_school_admin_login():
    app = create_app()
    
    with app.app_context():
        # Find the school admin user
        user = User.query.filter_by(email='demo@school.com', role=UserRole.SCHOOL_ADMIN).first()
        
        if not user:
            print("❌ School admin user not found!")
            return False
        
        print(f"✅ User found: {user.name} ({user.email})")
        print(f"   Role: {user.role.value}")
        print(f"   School ID: {user.school_id}")
        print(f"   Active: {user.is_active}")
        
        # Test password
        password_correct = bcrypt.check_password_hash(user.password_hash, 'school123')
        print(f"   Password check: {'✅ CORRECT' if password_correct else '❌ INCORRECT'}")
        
        return password_correct

if __name__ == '__main__':
    test_school_admin_login()