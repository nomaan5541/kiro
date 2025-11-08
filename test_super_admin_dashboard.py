#!/usr/bin/env python3
"""
Test script for Super Admin dashboard functionality
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models.user import User, UserRole
from models.school import School

def test_super_admin_dashboard():
    """Test super admin dashboard functionality"""
    app = create_app()
    
    with app.app_context():
        # Check if super admin exists
        super_admin = User.query.filter_by(role=UserRole.SUPER_ADMIN).first()
        
        if super_admin:
            print("✅ Super Admin user found:")
            print(f"   ID: {super_admin.id}")
            print(f"   Email: {super_admin.email}")
            print(f"   Name: {super_admin.name}")
            print(f"   Role: {super_admin.role.value}")
            
            # Check dashboard data
            total_schools = School.query.count()
            print(f"\n📊 Dashboard Statistics:")
            print(f"   Total Schools: {total_schools}")
            
            # Test template variables
            template_vars = {
                'user': super_admin,
                'total_schools': total_schools,
                'active_subscriptions': 0,
                'expired_subscriptions': 0,
                'suspended_accounts': 0,
                'recent_schools': []
            }
            
            print(f"\n✅ Template variables ready:")
            for key, value in template_vars.items():
                if key == 'user':
                    print(f"   {key}: {value.name} ({value.email})")
                else:
                    print(f"   {key}: {value}")
            
        else:
            print("❌ No Super Admin user found in database")
            print("   Run 'python init_db.py' to create default users")
        
        print("\n🔗 Super Admin Dashboard URL: http://localhost:5000/super-admin/dashboard")
        print("📧 Login first at: http://localhost:5000/auth/super-login")

if __name__ == '__main__':
    test_super_admin_dashboard()