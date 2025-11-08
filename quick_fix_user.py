#!/usr/bin/env python3
"""Quick fix to create/update user in main database"""

import sqlite3
import os
from extensions import bcrypt

def quick_fix():
    # Connect to the main database
    db_path = os.path.join('instance', 'school_management.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if demo@school.com exists
    cursor.execute("SELECT id, email FROM users WHERE email = ?", ('demo@school.com',))
    user = cursor.fetchone()
    
    if user:
        print(f"Found user: {user[1]}")
        # Update password
        new_hash = bcrypt.generate_password_hash('school123').decode('utf-8')
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user[0]))
        conn.commit()
        print("✅ Updated password for demo@school.com")
        print("🔑 Login with: demo@school.com / school123")
    else:
        print("❌ User demo@school.com not found")
        # Show all users
        cursor.execute("SELECT email, role FROM users")
        users = cursor.fetchall()
        print("Available users:")
        for u in users:
            print(f"  - {u[0]} ({u[1]})")
    
    conn.close()

if __name__ == '__main__':
    quick_fix()