# Fix for NoReverseMatch Error

## The Problem

You're seeing this error:
```
NoReverseMatch at /accounts/dashboard/student/
Reverse for 'student_profile_settings' not found.
```

## The Cause

The Django development server was running with the old URL configuration **before** we added the new `student_profile_settings` route. Django caches URL patterns when the server starts, so it doesn't know about the new route yet.

## The Solution

**Simply restart your Django development server:**

### Step 1: Stop the Server
Press `Ctrl+C` in the terminal where the server is running

### Step 2: Start the Server Again
```bash
python manage.py runserver
```

### Step 3: Refresh Your Browser
Go back to `http://127.0.0.1:8000/accounts/dashboard/student/` and refresh

## Verification

The URL configuration is correct (we tested it):
- ✅ URL pattern exists: `path('settings/student/', views.student_profile_settings, name='student_profile_settings')`
- ✅ View function exists: `student_profile_settings()` in `accounts/views.py`
- ✅ Template exists: `templates/accounts/student_profile_settings.html`
- ✅ URL resolves correctly: `/accounts/settings/student/`

## Alternative: Direct Access

You can also test by going directly to the URL:
```
http://127.0.0.1:8000/accounts/settings/student/
```

This should work immediately after restarting the server.

## Why This Happens

Django's URL resolver caches patterns at startup for performance. When you:
1. Start the server
2. Add new URL patterns
3. Try to access them

The server still has the old cached patterns. Restarting loads the new configuration.

## Quick Test

After restarting, you should see:
1. The "Profile Settings" card on the student dashboard
2. Clicking it takes you to `/accounts/settings/student/`
3. The page shows the parent link code
4. Copy button works
5. No errors!

---

**TL;DR: Just restart your Django server with `Ctrl+C` then `python manage.py runserver`**
