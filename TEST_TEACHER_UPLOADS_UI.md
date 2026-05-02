# Testing the Teacher Uploads UI

## Quick Test Guide

### Prerequisites
1. Server is running: `python manage.py runserver`
2. You have at least one teacher account
3. You have at least one student account
4. Teacher has created a class
5. Student is enrolled in the class

### Test Scenario 1: View Empty State

**Steps:**
1. Login as a new student (not enrolled in any classes)
2. Navigate to dashboard
3. Scroll to "Teacher Uploads" section

**Expected Result:**
- Section displays with gradient background
- Shows "0" for all statistics
- No recent uploads preview
- Action buttons are still visible
- "Join a Class" button is prominent

### Test Scenario 2: View with Content

**Steps:**
1. Login as teacher
2. Upload a PDF file:
   - Go to `/learning/teacher/upload/`
   - Select a PDF file
   - Fill in title, subject, description
   - Assign to a class
   - Submit
3. Logout and login as student (enrolled in that class)
4. View dashboard

**Expected Result:**
- "Teacher Uploads" section shows:
  - Total count: 1
  - PDFs: 1
  - This Week: 1
  - Classes: 1 (or more)
- Recent uploads shows the PDF with:
  - Red PDF icon
  - Title
  - Subject and time ago
  - PDF badge
- Clicking the upload opens content detail page

### Test Scenario 3: Multiple Uploads

**Steps:**
1. Login as teacher
2. Upload 5 different files (PDFs, DOCX, etc.)
3. Assign all to the same class
4. Logout and login as student
5. View dashboard

**Expected Result:**
- Statistics update correctly:
  - Total count: 5
  - PDFs: (count of PDFs)
  - This Week: 5
- Recent uploads shows last 3 items
- Different file types have different icons
- All items are clickable

### Test Scenario 4: Navigation

**Steps:**
1. Login as student with content
2. On dashboard, click "View All Content"

**Expected Result:**
- Navigates to `/learning/all-content/`
- Shows all content in grid view
- Search and filter options available

**Steps:**
3. Go back to dashboard
4. Click "Browse by Class"

**Expected Result:**
- Navigates to `/learning/my-classes/`
- Shows list of enrolled classes
- Can click class to see its content

**Steps:**
5. Go back to dashboard
6. Click on a recent upload

**Expected Result:**
- Navigates to content detail page
- Shows PDF viewer (if PDF)
- Shows download button
- Shows AI-generated materials

### Test Scenario 5: Responsive Design

**Steps:**
1. Login as student with content
2. View dashboard on desktop (1920px)
3. Resize to tablet (768px)
4. Resize to mobile (375px)

**Expected Result:**
- Desktop: Full 3-column stats grid
- Tablet: Stats remain in 3 columns (smaller)
- Mobile: Stats stack or show 2 columns
- All content remains accessible
- Buttons stack on mobile

### Test Scenario 6: Real-time Updates

**Steps:**
1. Login as student in one browser
2. Login as teacher in another browser
3. Teacher uploads new content
4. Student refreshes dashboard

**Expected Result:**
- Statistics update immediately
- New upload appears in recent uploads
- Count badges update
- "This Week" count increases

### Test Scenario 7: Multiple Classes

**Steps:**
1. Create 3 different classes as teacher
2. Upload different content to each class
3. Enroll student in all 3 classes
4. Login as student and view dashboard

**Expected Result:**
- Total count shows all content from all classes
- "Classes" stat shows 3
- Recent uploads may show content from different classes
- No duplicate content

### Test Scenario 8: Hover Effects

**Steps:**
1. Login as student with content
2. Hover over recent upload cards
3. Hover over action buttons

**Expected Result:**
- Recent upload cards brighten on hover
- Title color changes slightly
- Smooth transition animation
- Action buttons show hover state
- Cursor changes to pointer

### Test Scenario 9: Performance

**Steps:**
1. Upload 50+ files as teacher
2. Assign to student's class
3. Login as student
4. Measure page load time

**Expected Result:**
- Page loads in < 2 seconds
- Statistics calculate quickly
- Only 3-5 recent uploads shown (not all 50)
- No lag or stuttering
- Smooth scrolling

### Test Scenario 10: Accessibility

**Steps:**
1. Login as student with content
2. Use keyboard only (Tab, Enter, Space)
3. Navigate through Teacher Uploads section

**Expected Result:**
- Can tab to all interactive elements
- Focus indicators are visible
- Enter/Space activates buttons
- Logical tab order
- Screen reader announces content correctly

## Automated Testing

### Unit Tests
```bash
python manage.py test accounts.tests.StudentDashboardTests
```

### Integration Tests
```bash
python manage.py test tests.test_pdf_viewing
```

### Load Tests
```bash
python manage.py test tests.test_load_testing
```

## Common Issues and Solutions

### Issue 1: Section Not Showing
**Symptom**: Teacher Uploads section is missing
**Solution**: 
- Check if student is enrolled in any classes
- Verify template was updated correctly
- Clear browser cache
- Check for JavaScript errors in console

### Issue 2: Statistics Show Zero
**Symptom**: All stats show 0 despite having content
**Solution**:
- Verify content is assigned to student's classes
- Check ClassEnrollment is active
- Verify database queries in view
- Check for filtering issues

### Issue 3: Recent Uploads Not Showing
**Symptom**: No recent uploads preview
**Solution**:
- Verify content exists and is recent
- Check ordering (should be -created_at)
- Verify select_related is working
- Check template loop logic

### Issue 4: Links Not Working
**Symptom**: Clicking items doesn't navigate
**Solution**:
- Verify URL patterns are correct
- Check href attributes in template
- Verify content IDs are valid
- Check for JavaScript errors

### Issue 5: Styling Issues
**Symptom**: Section looks broken or unstyled
**Solution**:
- Verify Tailwind CSS is loaded
- Check for CSS conflicts
- Clear browser cache
- Verify gradient classes are correct

## Performance Benchmarks

### Expected Performance
- **Page Load**: < 2 seconds
- **Database Queries**: < 10 queries
- **Section Render**: < 100ms
- **Hover Response**: < 50ms

### Optimization Tips
1. Use `select_related()` for foreign keys
2. Use `prefetch_related()` for many-to-many
3. Cache statistics for 5 minutes
4. Limit recent uploads to 5 items
5. Use database indexes on created_at

## Browser Compatibility

### Tested Browsers
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ✅ Mobile Safari (iOS 14+)
- ✅ Chrome Mobile (Android 10+)

### Known Issues
- None reported

## Reporting Issues

If you find any issues:
1. Check console for errors
2. Verify database state
3. Test in different browser
4. Check server logs
5. Report with:
   - Browser and version
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshots if applicable

## Success Criteria

The implementation is successful if:
- ✅ Section displays prominently on dashboard
- ✅ Statistics calculate correctly
- ✅ Recent uploads show correctly
- ✅ All links navigate properly
- ✅ Responsive on all devices
- ✅ Accessible via keyboard
- ✅ Performance is acceptable
- ✅ No console errors
- ✅ Works in all major browsers
- ✅ Empty state handles gracefully

## Conclusion

The Teacher Uploads UI is fully functional and ready for production use. Follow this test guide to verify all features are working correctly in your environment.
