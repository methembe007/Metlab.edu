# PDF Preview Troubleshooting Guide

## Quick Diagnosis

### Step 1: Check if PDF File Exists
```bash
# In Django shell
python manage.py shell

from learning.teacher_models import TeacherContent
content = TeacherContent.objects.get(id=YOUR_CONTENT_ID)
print(content.uploaded_content.file.path)
print(content.uploaded_content.file.exists())
```

### Step 2: Check Browser Console
Open browser DevTools (F12) and look for:
- ❌ 404 errors - File not found
- ❌ 403 errors - Permission denied
- ❌ X-Frame-Options errors - Header blocking
- ✅ 200 OK - File loading successfully

### Step 3: Test Direct PDF Access
Try accessing the PDF directly:
```
http://localhost:8000/learning/content/1/pdf/
```

Should download/display the PDF directly.

## Common Problems & Solutions

### Problem 1: Blank Iframe

**Symptoms**:
- Iframe shows but is blank
- No error message
- Loading indicator disappears

**Possible Causes**:
1. PDF file is corrupted
2. Browser doesn't support PDF in iframe
3. File path is wrong

**Solutions**:
```python
# Check file integrity
from learning.teacher_models import TeacherContent
content = TeacherContent.objects.get(id=1)
with open(content.uploaded_content.file.path, 'rb') as f:
    header = f.read(5)
    print(header)  # Should be b'%PDF-'
```

**User Action**:
- Click "Open in New Tab" button
- Use "Download" button
- Click "Reload" button

### Problem 2: Loading Forever

**Symptoms**:
- Loading indicator never disappears
- PDF never shows
- No error after 10 seconds

**Possible Causes**:
1. Very large PDF file
2. Slow network
3. Server not responding

**Solutions**:
```python
# Check file size
content = TeacherContent.objects.get(id=1)
size_mb = content.uploaded_content.file_size / (1024 * 1024)
print(f"File size: {size_mb:.2f} MB")

# If > 10MB, consider compression
```

**User Action**:
- Wait for timeout (10 seconds)
- Fallback UI will appear
- Use "Open in New Tab"

### Problem 3: X-Frame-Options Error

**Symptoms**:
- Console error: "Refused to display in a frame"
- Blank iframe
- Error mentions X-Frame-Options

**Cause**:
- Server blocking iframe embedding

**Solution**:
✅ Already fixed! The view now includes:
```python
response['X-Frame-Options'] = 'SAMEORIGIN'
```

**Verify**:
```bash
curl -I http://localhost:8000/learning/content/1/pdf/
# Should see: X-Frame-Options: SAMEORIGIN
```

### Problem 4: 404 Not Found

**Symptoms**:
- Console shows 404 error
- "File not found" message
- Fallback UI appears immediately

**Possible Causes**:
1. File was deleted
2. Wrong content ID
3. File path incorrect
4. MEDIA_ROOT not configured

**Solutions**:
```python
# Check Django settings
from django.conf import settings
print(settings.MEDIA_ROOT)
print(settings.MEDIA_URL)

# Check file exists
import os
content = TeacherContent.objects.get(id=1)
print(os.path.exists(content.uploaded_content.file.path))
```

### Problem 5: Permission Denied (403)

**Symptoms**:
- Console shows 403 error
- "Access denied" message
- Student can't view PDF

**Possible Causes**:
1. Student not enrolled in class
2. Content not assigned to class
3. File permissions wrong

**Solutions**:
```python
# Check enrollment
from learning.teacher_models import ClassEnrollment
student = request.user.student_profile
enrollments = ClassEnrollment.objects.filter(
    student=student,
    is_active=True
)
print(f"Enrolled in {enrollments.count()} classes")

# Check content assignment
content = TeacherContent.objects.get(id=1)
print(f"Assigned to {content.assigned_classes.count()} classes")
```

### Problem 6: Mobile Not Working

**Symptoms**:
- Works on desktop
- Doesn't work on mobile
- Fallback appears on mobile

**Cause**:
- Mobile browsers often don't support PDF in iframe

**Solution**:
✅ This is expected behavior!
- Fallback UI provides "Open in New Tab"
- Mobile browsers will open PDF in native viewer
- Download option also available

**User Action**:
- Tap "Open in New Tab"
- PDF opens in mobile PDF viewer

### Problem 7: Slow Loading

**Symptoms**:
- Takes > 10 seconds to load
- Eventually times out
- Large file size

**Solutions**:
```python
# Compress PDF before upload
# Or increase timeout in template:

# In template JavaScript:
pdfLoadTimeout = setTimeout(function() {
    // Change 10000 to 30000 for 30 seconds
}, 30000);
```

**Better Solution**:
- Compress PDFs before upload
- Use PDF optimization tools
- Limit file size to < 10MB

## Browser-Specific Issues

### Chrome
**Usually works well**
- Full PDF support in iframe
- Fast rendering
- Good performance

**If not working**:
- Check Chrome version (need 90+)
- Disable extensions
- Clear cache

### Firefox
**May require plugin**
- Built-in PDF viewer sometimes disabled
- May show fallback more often

**Solution**:
- Enable built-in PDF viewer in Firefox settings
- Or use "Open in New Tab"

### Safari (macOS)
**Generally works**
- Native PDF support
- Good performance

**If not working**:
- Update to Safari 14+
- Check security settings

### Safari (iOS)
**Often uses fallback**
- iOS prefers native PDF viewer
- Automatically opens in new tab

**Expected Behavior**:
- Fallback UI appears
- "Open in New Tab" works perfectly
- This is normal!

### Edge
**Works like Chrome**
- Chromium-based
- Full support
- Good performance

## Testing Commands

### Test 1: Check URL Resolution
```python
from django.urls import reverse
url = reverse('learning:view_pdf', kwargs={'content_id': 1})
print(url)  # Should be: /learning/content/1/pdf/
```

### Test 2: Test View Directly
```python
from django.test import Client
client = Client()
client.login(username='student', password='password')
response = client.get('/learning/content/1/pdf/')
print(response.status_code)  # Should be 200
print(response['Content-Type'])  # Should be application/pdf
```

### Test 3: Check File Permissions
```bash
# On Linux/Mac
ls -la media/uploads/

# Should show readable files
# If not: chmod 644 media/uploads/*
```

### Test 4: Check MEDIA Configuration
```python
# In Django shell
from django.conf import settings
import os

print("MEDIA_ROOT:", settings.MEDIA_ROOT)
print("MEDIA_URL:", settings.MEDIA_URL)
print("Exists:", os.path.exists(settings.MEDIA_ROOT))
```

## Performance Optimization

### For Large PDFs
```python
# Add to view
response['Accept-Ranges'] = 'bytes'  # Enable range requests
response['Cache-Control'] = 'public, max-age=86400'  # Cache for 24 hours
```

### For Many Users
```python
# Use CDN for media files
# Or use cloud storage (S3, etc.)
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
```

## Monitoring

### Log PDF Access
```python
# Add to view
logger.info(f"PDF accessed: {content_id} by {request.user.username}")
```

### Track Failures
```python
# Add to handlePdfError() in template
fetch('/api/log-pdf-error/', {
    method: 'POST',
    body: JSON.stringify({
        content_id: {{ teacher_content.id }},
        error: 'Failed to load'
    })
});
```

## Quick Fixes

### Fix 1: Restart Server
```bash
# Sometimes helps with file path issues
python manage.py runserver
```

### Fix 2: Clear Browser Cache
```
Chrome: Ctrl+Shift+Delete
Firefox: Ctrl+Shift+Delete
Safari: Cmd+Option+E
```

### Fix 3: Check File Upload
```python
# Re-upload the PDF
# Make sure it's a valid PDF file
# Check file size < 50MB
```

### Fix 4: Verify Student Access
```python
# Ensure student is enrolled
# Ensure content is assigned
# Check enrollment is active
```

## Success Indicators

✅ **Working Correctly**:
- Loading indicator appears briefly
- PDF displays in iframe
- Can scroll through PDF
- No console errors

✅ **Fallback Working**:
- Fallback UI appears after timeout
- "Open in New Tab" works
- "Download" works
- Clear error message shown

❌ **Not Working**:
- Blank page, no fallback
- Console errors
- Buttons don't work
- Infinite loading

## Getting Help

If still not working:

1. **Check all diagnostics above**
2. **Collect information**:
   - Browser and version
   - Console errors
   - Network tab errors
   - Server logs
3. **Test with different PDF**
4. **Test with different browser**
5. **Check server configuration**

## Summary

The PDF preview system now has:
- ✅ Robust error handling
- ✅ Automatic fallback
- ✅ Multiple access methods
- ✅ Clear user feedback
- ✅ Cross-browser support
- ✅ Mobile compatibility

Most issues are now handled automatically with the fallback system!
