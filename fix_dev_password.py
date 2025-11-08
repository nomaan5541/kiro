#!/usr/bin/env python3
"""Fix the password in the dev database"""

import sqlite3
import os
from extensions import bcrypt

def fix_dev_password():
    # Connect to the dev database
    db_path = os.path.join('instance', 'school_management_dev.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check current users
    cursor.execute("SELECT id, name, email, role FROM users")
    users = cursor.fetchall()
    
    print("Current users in dev database:")
    for user in users:
        print(f"  ID: {user[0]}, Name: {user[1]}, Email: {user[2]}, Role: {user[3]}")
    
    # Find the virusx user
    cursor.execute("SELECT id, email, password_hash FROM users WHERE email = ?", ('virusx@gmail.com',))
    user = cursor.fetchone()
    
    if user:
        print(f"\nFound user: {user[1]}")
        print(f"Current hash: {user[2]}")
        
        # Generate new password hash
        new_hash = bcrypt.generate_password_hash('school123').decode('utf-8')
        
        # Update the password
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user[0]))
        conn.commit()
        
        print(f"Updated hash: {new_hash}")
        print("Password updated successfully!")
        
    else:
        print("User virusx@gmail.com not found in dev database")
    
    conn.close()

if __name__ == '__main__':
    fix_dev_password()