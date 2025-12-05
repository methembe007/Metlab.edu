#!/usr/bin/env python
"""
Script to fix URL references in learning templates
"""

import os
import re

# Define the templates directory
templates_dir = 'templates/learning'

# URL patterns to fix (without namespace)
url_patterns = [
    'class_management',
    'class_detail',
    'student_progress',
    'class_analytics',
    'teacher_content_dashboard',
    'upload_content',
    'teacher_content_list',
    'teacher_content_detail',
    'bulk_assign_content',
    'enroll_in_class',
    'customize_quiz',
    'teacher_quiz_list',
    'remove_student',
    'toggle_quiz_status',
    'quiz_analytics'
]

def fix_urls_in_file(filepath):
    """Fix URL references in a single file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes = []
    
    # Fix each URL pattern
    for pattern in url_patterns:
        # Match {% url 'pattern' ... %} but not {% url 'learning:pattern' ... %}
        old_pattern = r"{{% url '" + pattern + r"'"
        new_pattern = "{% url 'learning:" + pattern + "'"
        
        if old_pattern in content and new_pattern not in content:
            content = content.replace(old_pattern, new_pattern)
            changes.append(pattern)
    
    # Only write if content changed
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return changes
    
    return []

def main():
    """Main function to process all templates"""
    print("Fixing URL references in learning templates...")
    print("=" * 60)
    
    total_files = 0
    total_changes = 0
    
    # Process each HTML file
    for filename in os.listdir(templates_dir):
        if filename.endswith('.html'):
            filepath = os.path.join(templates_dir, filename)
            changes = fix_urls_in_file(filepath)
            
            if changes:
                total_files += 1
                total_changes += len(changes)
                print(f"\n✓ Fixed {filename}:")
                for change in changes:
                    print(f"  - {change}")
    
    print("\n" + "=" * 60)
    print(f"Summary: Fixed {total_changes} URL references in {total_files} files")

if __name__ == '__main__':
    main()