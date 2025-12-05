# Teacher Video Call Guide

This guide explains how teachers can create and manage video calls for their classes.

## Overview

Teachers have multiple ways to initiate video calls with their students:

1. **Class Video Sessions** - Start a video call for an entire class
2. **Quick Start** - Start an immediate one-on-one or group video call
3. **Scheduled Sessions** - Schedule video calls in advance

---

## Method 1: Class Video Sessions (Recommended)

This is the easiest way for teachers to start video calls with their entire class.

### Steps:

1. **Navigate to Class Management**
   - Go to Teacher Dashboard
   - Click on "Class Management" or navigate to `/learning/teacher/classes/`

2. **Select Your Class**
   - Click on the class you want to have a video session with
   - This takes you to the class detail page

3. **Start Video Session**
   - In the "Quick Actions" section, click the **"Start Video Session"** button
   - This button has a video camera icon

4. **Configure Session**
   - You'll be redirected to the video session scheduling page
   - The form will be pre-filled with:
     - Class name as the session title
     - All enrolled students automatically selected as participants
     - Session type set to "class"

5. **Choose Session Type**
   - **Immediate Start**: Leave scheduled time empty or set to now
   - **Scheduled**: Pick a future date and time

6. **Configure Options**
   - Duration (default: 60 minutes)
   - Allow screen sharing (recommended for teaching)
   - Recording options
   - Maximum participants

7. **Create Session**
   - Click "Schedule Session" or "Start Now"
   - Students will receive notifications
   - You'll be redirected to the session detail page

8. **Join the Session**
   - Click "Join Session" when ready
   - Students can join 10 minutes before scheduled time

### URL Path:
```
/learning/teacher/classes/<class_id>/video-session/start/
```

---

## Method 2: Quick Start Video Call

For immediate, unscheduled video calls with selected students.

### Steps:

1. **Navigate to Quick Start**
   - Go to `/video/quick-start/`
   - Or click "Quick Start" from the video chat menu

2. **Fill Out Form**
   - **Title**: Give your session a name
   - **Session Type**: Choose one-on-one, group, or class
   - **Participants**: Select specific students
   - **Allow Screen Share**: Enable for teaching

3. **Start Immediately**
   - Click "Start Session"
   - Session begins immediately
   - Participants receive instant notifications

### URL Path:
```
/video/quick-start/
```

---

## Method 3: Schedule Video Session

For planning video calls in advance.

### Steps:

1. **Navigate to Schedule**
   - Go to `/video/schedule/`
   - Or click "Schedule Session" from the video chat menu

2. **Fill Out Form**
   - **Title**: Session name
   - **Description**: Optional details about the session
   - **Session Type**: one-on-one, group, or class
   - **Scheduled Time**: Pick date and time
   - **Duration**: How long the session will last
   - **Participants**: Select students to invite
   - **Class**: Optionally link to a specific class

3. **Additional Options**
   - **Max Participants**: Set limit (default: 30)
   - **Allow Screen Share**: Enable for presentations
   - **Require Approval**: Students need approval to join
   - **Recording**: Enable session recording

4. **Schedule**
   - Click "Schedule Session"
   - Students receive email notifications
   - Calendar invites (.ics files) are sent

5. **Manage Scheduled Session**
   - View session details at `/video/session/<session_id>/`
   - Edit session before it starts
   - Cancel if needed
   - Download calendar entry

### URL Path:
```
/video/schedule/
```

---

## Managing Video Sessions

### View All Sessions

Navigate to `/video/sessions/` to see:
- **Upcoming Sessions**: Scheduled sessions not yet started
- **Active Sessions**: Currently running sessions
- **Past Sessions**: Completed or cancelled sessions

### Session Actions

For each session, you can:
- **View Details**: See participants, schedule, settings
- **Edit**: Modify scheduled sessions (before they start)
- **Cancel**: Cancel scheduled sessions with reason
- **Join**: Enter the video call room
- **Download Calendar**: Get .ics file for calendar apps
- **View Statistics**: See analytics after completion

### Class Video Session History

View all video sessions for a specific class:
```
/learning/teacher/classes/<class_id>/video-sessions/
```

This shows:
- All past video sessions for the class
- Attendance records
- Session recordings (if enabled)
- Student participation statistics

---

## Video Call Features for Teachers

### During a Video Call

As the host, teachers have special controls:

1. **Participant Management**
   - See all participants
   - Remove disruptive participants
   - Mute participants (if needed)

2. **Screen Sharing**
   - Share your screen for presentations
   - Share specific application windows
   - Stop sharing anytime

3. **Recording**
   - Start/stop recording
   - Recordings saved automatically
   - Access recordings after session ends

4. **Chat**
   - Send messages to all participants
   - Receive questions from students

5. **Session Control**
   - End session for everyone
   - Extend session duration

### After a Video Call

1. **View Statistics**
   - Total participants
   - Attendance duration per student
   - Connection quality metrics
   - Engagement data

2. **Access Recordings**
   - Download or stream recordings
   - Share recording links with students
   - Recordings linked to class

3. **Attendance Records**
   - Automatic attendance tracking
   - Export attendance data
   - Integration with class analytics

---

## Integration with Class Management

### Automatic Features

When starting a video session from a class:

1. **Auto-Enrollment**
   - All enrolled students automatically invited
   - Students receive notifications

2. **Attendance Tracking**
   - Attendance automatically recorded when students join
   - Integrated with class attendance records

3. **Class Context**
   - Session linked to specific class
   - Appears in class video session history
   - Included in class analytics

### Class Detail Page Integration

The class detail page (`/learning/teacher/classes/<class_id>/`) includes:

- **"Start Video Session"** button in Quick Actions
- **"View Video Sessions"** button to see history
- Video session statistics in class overview

---

## API Access for Teachers

Teachers can also use the REST API to manage video sessions programmatically:

### Create Session
```http
POST /video/api/sessions/create/
Content-Type: application/json

{
  "session_type": "class",
  "title": "Math Class - Algebra Review",
  "scheduled_time": "2025-12-06T14:00:00Z",
  "duration_minutes": 60,
  "participant_ids": [1, 2, 3, 4, 5],
  "allow_screen_share": true
}
```

### List Sessions
```http
GET /video/api/sessions/?status=scheduled
```

### Start Session
```http
POST /video/api/sessions/<session_id>/start/
```

See `API_ENDPOINTS.md` for complete API documentation.

---

## Best Practices for Teachers

### Before the Session

1. **Test Your Setup**
   - Check camera and microphone
   - Test screen sharing
   - Ensure stable internet connection

2. **Schedule in Advance**
   - Give students 24-48 hours notice
   - Send calendar invites
   - Include session agenda in description

3. **Prepare Materials**
   - Have presentation ready
   - Test screen sharing with materials
   - Prepare backup activities

### During the Session

1. **Start Early**
   - Join 5-10 minutes before scheduled time
   - Test audio/video before students join
   - Greet students as they arrive

2. **Engage Students**
   - Use screen sharing for visual aids
   - Ask questions via chat
   - Monitor participant list

3. **Manage Disruptions**
   - Mute disruptive participants if needed
   - Use chat for questions
   - Record session for absent students

### After the Session

1. **Review Statistics**
   - Check attendance records
   - Review participation metrics
   - Identify students who had issues

2. **Share Resources**
   - Share recording link with class
   - Post session notes
   - Follow up with absent students

3. **Gather Feedback**
   - Ask students about experience
   - Note technical issues
   - Improve for next session

---

## Troubleshooting

### Common Issues

**Students Can't Join**
- Check if session is active
- Verify students are invited
- Ensure early join window is open (10 min before)

**Poor Video Quality**
- Check internet connection
- Reduce number of participants with video on
- Lower video quality settings

**Screen Share Not Working**
- Verify screen share is enabled for session
- Check browser permissions
- Try sharing specific window instead of entire screen

**Recording Failed**
- Check storage space
- Verify recording permissions
- Contact support if issue persists

### Getting Help

- Check video chat documentation
- Contact technical support
- Review session logs for errors

---

## Quick Reference

### Key URLs

| Action | URL |
|--------|-----|
| Start Class Video | `/learning/teacher/classes/<class_id>/video-session/start/` |
| Quick Start | `/video/quick-start/` |
| Schedule Session | `/video/schedule/` |
| View All Sessions | `/video/sessions/` |
| Class Video History | `/learning/teacher/classes/<class_id>/video-sessions/` |
| Join Session | `/video/session/<session_id>/join/` |

### Keyboard Shortcuts (During Call)

- **M**: Toggle microphone
- **V**: Toggle video
- **S**: Start/stop screen share
- **C**: Open chat
- **E**: End session (host only)

---

## Security & Privacy

### Teacher Responsibilities

1. **Protect Session Links**
   - Don't share session IDs publicly
   - Only invite enrolled students
   - Use require approval for sensitive sessions

2. **Recording Consent**
   - Inform students when recording
   - Follow school/district policies
   - Secure recording storage

3. **Student Privacy**
   - Monitor chat for inappropriate content
   - Protect student information
   - Follow FERPA/COPPA guidelines

### Platform Security

- All video calls encrypted end-to-end
- Session access controlled by permissions
- Rate limiting prevents abuse
- Automatic session timeout after inactivity

---

## Support

For additional help:
- Email: support@metlab.edu
- Documentation: `/video/help/`
- Technical Support: Available during school hours
