#!/usr/bin/env python3
"""Check file paths and database location"""

import os
from app import create_app

def check_paths():
    print(f"Current working directory: {os.getcwd()}")
    print(f"Database file path (relative): school_management.db")
    print(f"Database file path (absolute): {os.path.abspath('school_management.db')}")
    
    # Check if database files exist
    db_files = [
        'school_management.db',
        'instance/school_management.db',
        'instance/school_management_dev.db'
    ]
    
    for db_file in db_files:
        exists = os.path.exists(db_file)
        size = os.path.getsize(db_file) if exists else 0
        print(f"{db_file}: {'EXISTS' if exists else 'NOT FOUND'} ({size} bytes)")
    
    # Check Flask app config
    app = create_app()
    print(f"\nFlask database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

if __name__ == '__main__':
    check_paths()