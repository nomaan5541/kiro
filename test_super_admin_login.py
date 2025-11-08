#!/usr/bin/env python3
"""
Test script for Super Admin login functionality
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models.user import User, UserRole

def test_super_admin_login():
    """Test super admin login functionality"""
    app = create_app()
    
    with app.app_context():
        # Check if super admin exists
        super_admin = User.query.filter_by(role=UserRole.SUPER_ADMIN).first()
        
        if super_admin:
            print("✅ Super Admin user found:")
            print(f"   Email: {super_admin.email}")
            print(f"   Name: {super_admin.name}")
            print(f"   Role: {super_admin.role.value}")
            
            # Test password verification
            from extensions import bcrypt
            test_password = "admin123"
            if bcrypt.check_password_hash(super_admin.password_hash, test_password):
                print(f"✅ Password verification successful for: {test_password}")
            else:
                print(f"❌ Password verification failed for: {test_password}")
        else:
            print("❌ No Super Admin user found in database")
            print("   Run 'python init_db.py' to create default users")
        
        print("\n🔗 Super Admin Login URL: http://localhost:5000/auth/super-login")
        print("📧 Default Email: admin@schoolsystem.com")
        print("🔑 Default Password: admin123")

if __name__ == '__main__':
    test_super_admin_login()