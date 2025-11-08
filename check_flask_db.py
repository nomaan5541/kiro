#!/usr/bin/env python3
"""Check Flask app database configuration"""

from app import create_app
from extensions import db
from models.user import User

def check_flask_database():
    app = create_app()
    
    with app.app_context():
        print(f"Flask Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print(f"Database engine URL: {db.engine.url}")
        
        # Check users
        users = User.query.all()
        print(f"\nUsers in Flask database: {len(users)}")
        for user in users:
            print(f"- {user.email} ({user.role.value})")

if __name__ == '__main__':
    check_flask_database()