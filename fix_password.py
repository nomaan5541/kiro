#!/usr/bin/env python3
"""Fix the password for the virusx user"""

from app import create_app
from extensions import db, bcrypt
from models.user import User

def fix_password():
    app = create_app()
    
    with app.app_context():
        # Find the user
        user = User.query.filter_by(email='virusx@gmail.com').first()
        
        if user:
            print(f"Found user: {user.email}")
            print(f"Current password hash: {user.password_hash}")
            
            # Update password to 'school123'
            new_password_hash = bcrypt.generate_password_hash('school123').decode('utf-8')
            user.password_hash = new_password_hash
            db.session.commit()
            
            print(f"Updated password hash: {user.password_hash}")
            
            # Test the new password
            test_result = bcrypt.check_password_hash(user.password_hash, 'school123')
            print(f"Password test result: {test_result}")
            
        else:
            print("User not found!")

if __name__ == '__main__':
    fix_password()