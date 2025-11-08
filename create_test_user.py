#!/usr/bin/env python3
"""Create a test user with the email the Flask app is seeing"""

from app import create_app
from extensions import db, bcrypt
from models.user import User, UserRole
from models.school import School

def create_test_user():
    app = create_app()
    
    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter_by(email='virusx@gmail.com').first()
        
        if existing_user:
            print(f"User already exists: {existing_user.email}")
            # Update password to 'school123'
            existing_user.password_hash = bcrypt.generate_password_hash('school123').decode('utf-8')
            db.session.commit()
            print("Updated password to 'school123'")
        else:
            print("User not found, creating new user...")
            
            # Get or create a school
            school = School.query.first()
            if not school:
                print("No school found!")
                return
            
            # Create new user
            password_hash = bcrypt.generate_password_hash('school123').decode('utf-8')
            user = User(
                name='Test School Admin',
                email='virusx@gmail.com',
                password_hash=password_hash,
                role=UserRole.SCHOOL_ADMIN,
                school_id=school.id
            )
            db.session.add(user)
            db.session.commit()
            print("Created new user")
        
        print(f"Test user credentials: virusx@gmail.com / school123")

if __name__ == '__main__':
    create_test_user()