#!/usr/bin/env python3
"""Fix enum values in database"""

import sqlite3
import os

def fix_enum_values():
    # Fix both database files
    db_files = [
        os.path.join('instance', 'school_management.db'),
        os.path.join('instance', 'school_management_dev.db')
    ]
    
    for db_path in db_files:
        if not os.path.exists(db_path):
            print(f"Skipping {db_path} - not found")
            continue
            
        print(f"Fixing {db_path}...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Fix SchoolStatus enum values
            cursor.execute("UPDATE schools SET status = 'ACTIVE' WHERE status = 'active'")
            cursor.execute("UPDATE schools SET status = 'SUSPENDED' WHERE status = 'suspended'")
            cursor.execute("UPDATE schools SET status = 'EXPIRED' WHERE status = 'expired'")
            cursor.execute("UPDATE schools SET status = 'INACTIVE' WHERE status = 'inactive'")
            
            # Fix UserRole enum values (if needed)
            cursor.execute("UPDATE users SET role = 'SUPER_ADMIN' WHERE role = 'super_admin'")
            cursor.execute("UPDATE users SET role = 'SCHOOL_ADMIN' WHERE role = 'school_admin'")
            cursor.execute("UPDATE users SET role = 'TEACHER' WHERE role = 'teacher'")
            cursor.execute("UPDATE users SET role = 'STUDENT' WHERE role = 'student'")
            cursor.execute("UPDATE users SET role = 'PARENT' WHERE role = 'parent'")
            
            # Fix StudentStatus enum values (if needed)
            cursor.execute("UPDATE students SET status = 'ACTIVE' WHERE status = 'active'")
            cursor.execute("UPDATE students SET status = 'INACTIVE' WHERE status = 'inactive'")
            cursor.execute("UPDATE students SET status = 'GRADUATED' WHERE status = 'graduated'")
            cursor.execute("UPDATE students SET status = 'TRANSFERRED' WHERE status = 'transferred'")
            
            conn.commit()
            print(f"✅ Fixed enum values in {db_path}")
            
            # Show current values
            cursor.execute("SELECT email, status FROM schools")
            schools = cursor.fetchall()
            print(f"Schools: {schools}")
            
        except Exception as e:
            print(f"❌ Error fixing {db_path}: {e}")
        
        conn.close()

if __name__ == '__main__':
    fix_enum_values()