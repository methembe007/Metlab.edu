# Session Scheduling and Notifications Implementation

## Overview

This document describes the implementation of video session scheduling and notification features for the MetLab Education video chat system.

## Features Implemented

### 1. Session Scheduling Interface (Task 7.1)

#### Forms
- **VideoSessionScheduleForm**: Full scheduling form with all options
  - Date/time picker with timezone support (HTML5 datetime-local input)
  - Participant selection with checkboxes
  - Session type selection (one-on-one, group, class)
  - Duration and max participants configuration
  - Optional linking to TeacherClass or TutorBooking
  - Settings for screen sharing and approval requirements

- **VideoSessionQuickStartForm**: Simplified form for immediate sessions
  - Quick title and type selection
  - Participant invitation
  - Screen sharing toggle

- **VideoSessionEditForm**: Form for editing scheduled sessions
  - Update title, description, time, duration
  - Modify participant limits and settings

#### Views
- `schedule_session`: Create and schedule new video sessions
- `quick_start_session`: Start immediate video sessions
- `session_list`: View all user's sessions (upcoming, active, past)
- `session_detail`: View detailed session information
- `edit_session`: Edit scheduled sessions (host only)
- `cancel_session`: Cancel scheduled sessions with reason
- `join_session`: Join active or scheduled sessions
- `download_calendar`: Download session as .ics calendar file

#### Templates
- `schedule_session.html`: Full scheduling interface
- `quick_start.html`: Quick start interface
- `session_list.html`: List of all sessions with filters
- `session_detail.html`: Detailed session view with actions
- `edit_session.html`: Session editing form
- `cancel_session.html`: Cancellation confirmation

### 2. Notification System (Task 7.2)

#### VideoSessionNotificationService

The notification service handles all email notifications for video sessions:

**Methods:**
- `send_session_scheduled_notification(session, participants)`: Notify participants when session is scheduled
- `send_session_reminder(session)`: Send 15-minute reminder before session
- `send_session_started_notification(session)`: Notify when session starts
- `send_session_cancelled_notification(session, reason)`: Notify of cancellation
- `send_session_updated_notification(session)`: Notify of schedule changes
- `generate_calendar_entry(session)`: Generate iCalendar (.ics) format
- `can_join_early(session)`: Check if early join is allowed (10 minutes before)
- `get_time_until_early_join(session)`: Calculate time until early join
- `get_sessions_needing_reminders()`: Find sessions needing reminders

#### Email Templates

Text and HTML versions for all notification types:
- `session_scheduled`: Initial invitation with calendar entry
- `session_reminder`: 15-minute reminder with join button
- `session_started`: Notification when session goes live
- `session_cancelled`: Cancellation notice with reason
- `session_updated`: Schedule change notification

#### Management Command

**send_session_reminders**: Periodic command to send reminders
```bash
python manage.py send_session_reminders
```

This should be run every 5 minutes via cron or Windows Task Scheduler:
```
*/5 * * * * cd /path/to/project && python manage.py send_session_reminders
```

## Requirements Mapping

### Requirement 5.1: Session Scheduling
✅ Teachers can schedule video sessions with date, time, and duration
- Implemented in `VideoSessionScheduleForm` and `schedule_session` view
- Supports all session types (one-on-one, group, class)

### Requirement 5.2: Calendar Entries
✅ Calendar entries created for all invited participants
- `generate_calendar_entry()` creates iCalendar format
- `download_calendar` view provides .ics download
- Email notifications include session details

### Requirement 5.3: Reminder Notifications
✅ Reminder notifications sent 15 minutes before session
- `send_session_reminder()` sends email reminders
- `send_session_reminders` management command for automation
- Includes join button in email

### Requirement 5.4: Join Button at Scheduled Time
✅ Join button displayed when session is ready
- `can_join` logic in `session_detail` view
- Join button shown for active sessions
- Join button shown 10 minutes before scheduled time

### Requirement 5.5: Early Join (10 minutes before)
✅ Participants can join 10 minutes before scheduled time
- `can_join_early()` method checks eligibility
- `join_session` view enforces early join window
- UI shows countdown until early join available

## Usage

### Scheduling a Session

1. Navigate to `/video/schedule/`
2. Fill in session details:
   - Title and description
   - Session type
   - Scheduled date/time
   - Duration (15-240 minutes)
   - Select participants
3. Configure settings (screen sharing, approval)
4. Submit form
5. Participants receive email invitations with calendar entries

### Quick Start Session

1. Navigate to `/video/quick-start/`
2. Enter title and select type
3. Choose participants
4. Click "Start Session Now"
5. Session starts immediately and participants are notified

### Joining a Session

1. Receive email notification with join link
2. Click link or navigate to session detail page
3. For scheduled sessions:
   - Join button appears 10 minutes before scheduled time
   - Can join immediately if session is active
4. Click "Join Session" to enter video call room

### Managing Sessions

**Edit Session:**
- Only host can edit
- Only scheduled sessions can be edited
- Changes trigger update notifications

**Cancel Session:**
- Only host can cancel
- Provide optional cancellation reason
- All participants notified via email

**Download Calendar:**
- Click "Add to Calendar" button on session detail page
- Downloads .ics file compatible with all calendar apps
- Includes 15-minute reminder alarm

## Configuration

### Email Settings

Ensure email is configured in `settings.py`:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'MetLab Education <noreply@metlab.edu>'
```

### Site URL

Set the site URL for generating absolute URLs in emails:
```python
SITE_URL = 'https://your-domain.com'
```

Or via environment variable:
```bash
export SITE_URL=https://your-domain.com
```

### Automated Reminders

Set up periodic execution of reminder command:

**Linux/Mac (crontab):**
```bash
*/5 * * * * cd /path/to/metlab && /path/to/venv/bin/python manage.py send_session_reminders >> /var/log/session_reminders.log 2>&1
```

**Windows (Task Scheduler):**
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily, repeat every 5 minutes
4. Action: Start a program
5. Program: `python.exe`
6. Arguments: `manage.py send_session_reminders`
7. Start in: Project directory

**Alternative: Celery Beat (Recommended for Production)**
```python
# celery.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    'send-session-reminders': {
        'task': 'video_chat.tasks.send_session_reminders',
        'schedule': crontab(minute='*/5'),
    },
}
```

## Testing

### Manual Testing

1. **Schedule a session 20 minutes in the future**
   - Verify email notification received
   - Check calendar entry downloads correctly
   - Confirm early join works 10 minutes before

2. **Run reminder command**
   ```bash
   python manage.py send_session_reminders
   ```
   - Verify reminder emails sent for sessions starting in 15 minutes

3. **Edit a scheduled session**
   - Change time
   - Verify update notification sent to participants

4. **Cancel a session**
   - Provide cancellation reason
   - Verify cancellation emails sent

5. **Join session early**
   - Try joining 15 minutes before (should be blocked)
   - Try joining 10 minutes before (should work)
   - Try joining after scheduled time (should work)

### Automated Testing

Run the video chat tests:
```bash
python manage.py test video_chat
```

## Integration Points

### Learning Module
- Sessions can be linked to `TeacherClass`
- Auto-invite all enrolled students
- Track attendance via session participation

### Community Module
- Sessions can be linked to `TutorBooking`
- One-on-one tutoring sessions
- Update booking status when session starts

### Accounts Module
- Uses existing User model
- Respects parent monitoring settings
- Logs session activity for parent dashboard

## Future Enhancements

1. **SMS Notifications**: Add SMS reminders via Twilio
2. **Push Notifications**: Browser push notifications for reminders
3. **Recurring Sessions**: Support for weekly/daily recurring sessions
4. **Waiting Room**: Hold participants until host admits them
5. **Session Templates**: Save session configurations as templates
6. **Bulk Scheduling**: Schedule multiple sessions at once
7. **Timezone Display**: Show times in participant's local timezone
8. **Calendar Integration**: Direct integration with Google Calendar, Outlook

## Troubleshooting

### Emails Not Sending
- Check email configuration in settings
- Verify SMTP credentials
- Check spam folder
- Review Django logs for errors

### Reminders Not Working
- Verify management command runs successfully
- Check cron/task scheduler configuration
- Ensure system time is correct
- Review command output logs

### Calendar Files Not Downloading
- Check SITE_URL is configured correctly
- Verify session has scheduled_time set
- Ensure user has permission to access session

### Early Join Not Working
- Verify scheduled_time is set correctly
- Check system timezone configuration
- Ensure session status is 'scheduled'

## API Reference

### VideoSessionNotificationService

```python
from video_chat.notifications import VideoSessionNotificationService

# Send scheduled notification
VideoSessionNotificationService.send_session_scheduled_notification(
    session=session,
    participants=[user1, user2]
)

# Send reminder
VideoSessionNotificationService.send_session_reminder(session)

# Check early join eligibility
can_join = VideoSessionNotificationService.can_join_early(session)

# Generate calendar entry
ical = VideoSessionNotificationService.generate_calendar_entry(session)
```

### Views

```python
# Schedule session
POST /video/schedule/

# Quick start
POST /video/quick-start/

# List sessions
GET /video/sessions/

# Session detail
GET /video/session/<uuid>/

# Edit session
GET/POST /video/session/<uuid>/edit/

# Cancel session
GET/POST /video/session/<uuid>/cancel/

# Join session
GET /video/session/<uuid>/join/

# Download calendar
GET /video/session/<uuid>/calendar/
```

## Conclusion

The session scheduling and notification system provides a complete solution for managing video sessions with:
- Flexible scheduling options
- Comprehensive email notifications
- Calendar integration
- Early join capability
- Automated reminders

All requirements (5.1-5.5) have been successfully implemented and tested.
