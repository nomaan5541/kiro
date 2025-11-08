#!/usr/bin/env python3
"""
Fix school status enum values in the database
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models.school import School, SchoolStatus

def fix_school_status_enum():
    """Fix school status enum values in database"""
    app = create_app()
    with app.app_context():
        try:
            # Get all schools
            schools = db.session.execute(db.text("SELECT id, status FROM schools")).fetchall()
            
            print(f"Found {len(schools)} schools to check...")
            
            # Fix status values
            for school_id, status in schools:
                if status == 'active':
                    db.session.execute(
                        db.text("UPDATE schools SET status = :new_status WHERE id = :school_id"),
                        {"new_status": SchoolStatus.ACTIVE.value, "school_id": school_id}
                    )
                    print(f"Fixed school {school_id}: 'active' -> '{SchoolStatus.ACTIVE.value}'")
                elif status == 'suspended':
                    db.session.execute(
                        db.text("UPDATE schools SET status = :new_status WHERE id = :school_id"),
                        {"new_status": SchoolStatus.SUSPENDED.value, "school_id": school_id}
                    )
                    print(f"Fixed school {school_id}: 'suspended' -> '{SchoolStatus.SUSPENDED.value}'")
                elif status == 'expired':
                    db.session.execute(
                        db.text("UPDATE schools SET status = :new_status WHERE id = :school_id"),
                        {"new_status": SchoolStatus.EXPIRED.value, "school_id": school_id}
                    )
                    print(f"Fixed school {school_id}: 'expired' -> '{SchoolStatus.EXPIRED.value}'")
                elif status == 'inactive':
                    db.session.execute(
                        db.text("UPDATE schools SET status = :new_status WHERE id = :school_id"),
                        {"new_status": SchoolStatus.INACTIVE.value, "school_id": school_id}
                    )
                    print(f"Fixed school {school_id}: 'inactive' -> '{SchoolStatus.INACTIVE.value}'")
                else:
                    print(f"School {school_id} has unknown status: {status}")
            
            db.session.commit()
            print("✅ All school status values have been fixed!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error fixing school status values: {e}")
            return False
        
        return True

if __name__ == '__main__':
    print("🔧 Fixing school status enum values...")
    success = fix_school_status_enum()
    if success:
        print("✅ Database fix completed successfully!")
    else:
        print("❌ Database fix failed!")
        sys.exit(1)