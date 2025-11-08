#!/usr/bin/env python3
"""
Script to fix duplicate Assignment class definitions
"""
import re

def fix_teacher_model():
    """Remove duplicate Assignment classes from teacher.py"""
    with open('models/teacher.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the start of AssignmentStatus enum
    start_pattern = r'class AssignmentStatus\(Enum\):'
    start_match = re.search(start_pattern, content)
    
    if not start_match:
        print("AssignmentStatus enum not found")
        return
    
    start_pos = start_match.start()
    
    # Find the end of the Assignment class (look for the next class or end of file)
    # We'll look for the end of the to_dict method
    end_pattern = r'(\n        }\n)'
    end_matches = list(re.finditer(end_pattern, content[start_pos:]))
    
    if not end_matches:
        print("Could not find end of Assignment class")
        return
    
    # Take the first match after the start position
    end_pos = start_pos + end_matches[0].end()
    
    # Replace the duplicate classes with a comment
    new_content = (
        content[:start_pos] + 
        "# Assignment-related classes moved to models/assignment.py\n" +
        content[end_pos:]
    )
    
    # Write back the fixed content
    with open('models/teacher.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("Removed duplicate Assignment classes from models/teacher.py")

def update_imports():
    """Update imports to use Assignment from models.assignment"""
    files_to_update = [
        'utils/file_helpers.py',
        'blueprints/files.py', 
        'blueprints/teacher.py',
        'create_enhanced_models.py'
    ]
    
    for file_path in files_to_update:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace imports
            content = re.sub(
                r'from models\.teacher import (.*?)Assignment(.*?)$',
                r'from models.teacher import \1\2',
                content,
                flags=re.MULTILINE
            )
            
            # Add import from assignment model if Assignment is used
            if 'Assignment' in content and 'from models.assignment import' not in content:
                # Find the import section and add the assignment import
                import_pattern = r'(from models\.teacher import.*?\n)'
                if re.search(import_pattern, content):
                    content = re.sub(
                        import_pattern,
                        r'\1from models.assignment import Assignment, AssignmentStatus, AssignmentType\n',
                        content
                    )
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"Updated imports in {file_path}")
            
        except Exception as e:
            print(f"Error updating {file_path}: {e}")

if __name__ == '__main__':
    fix_teacher_model()
    update_imports()
    print("Fixed duplicate Assignment class definitions")