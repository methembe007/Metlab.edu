#!/usr/bin/env python
"""
Comprehensive script to fix all URL references in learning templates
"""

import os
import glob

# Define replacements
replacements = {
    "{% url 'upload_content'": "{% url 'learning:upload_content'",
    "{% url 'teacher_quiz_list'": "{% url 'learning:teacher_quiz_list'",
    "{% url 'teacher_content_list'": "{% url 'learning:teacher_content_list'",
    "{% url 'teacher_content_detail'": "{% url 'learning:teacher_content_detail'",
    "{% url 'teacher_content_dashboard'": "{% url 'learning:teacher_content_dashboard'",python 
    "{% url 'class_detail'": "{% url 'learning:class_detail'",
    "{% url 'student_progress'": "{% url 'learning:student_progress'",
    "{% url 'class_analytics'": "{% url 'learning:class_analytics'",
    "{% url 'class_management'": "{% url 'learning:class_management'",
    "{% url 'customize_quiz'": "{% url 'learning:customize_quiz'",
    "{% url 'toggle_quiz_status'": "{% url 'learning:toggle_quiz_status'",
    "{% url 'quiz_analytics'": "{% url 'learning:quiz_analytics'",
    "{% url 'remove_student'": "{% url 'learning:remove_student'",
    "{% url 'enroll_in_class'": "{% url 'learning:enroll_in_class'",
}

def fix_file(filepath):
    """Fix URL references in a file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    changes = []
    
    for old, new in replacements.items():
        if old in content and new not in content:
            count = content.count(old)
            content = content.replace(old, new)
            changes.append((old, count))
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return changes
    
    return []

def main():
    """Process all HTML files in learning templates"""
    print("Fixing URL references in learning templates...")
    print("=" * 70)
    
    total_files = 0
    total_changes = 0
    
    # Find all HTML files
    pattern = os.path.join('templates', 'learning', '*.html')
    files = glob.glob(pattern)
    
    for filepath in files:
        changes = fix_file(filepath)
        
        if changes:
            total_files += 1
            filename = os.path.basename(filepath)
            print(f"\n✓ Fixed {filename}:")
            for old_url, count in changes:
                total_changes += count
                print(f"  - {old_url} ({count} occurrences)")
    
    print("\n" + "=" * 70)
    print(f"Summary: Fixed {total_changes} URL references in {total_files} files")

if __name__ == '__main__':
    main()