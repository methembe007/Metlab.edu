# Student Video Call Access

This document shows how students can access and join video calls.

## Summary

Students now have easy access to video sessions through their dashboard.

### Student Dashboard (NEW!)
**Location**: `/accounts/student/dashboard/`

**New Card Added**:
- **"Video Sessions"** card (Blue)
  - Icon: Video camera
  - Button: "View Sessions"
  - Links to: `/video/sessions/`

---

## What Students Can Do

### 1. View Video Sessions
Students can see:
- **Upcoming Sessions**: Scheduled class sessions they're invited to
- **Active Sessions**: Currently running sessions they can join
- **Past Sessions**: Completed sessions with recordings

### 2. Join Video Sessions
When a teacher starts a video session:
1. Student receives notification (email + in-app)
2. Session appears in "Active Sessions"
3. Student clicks "Join Session"
4. Enters video call room

### 3. Early Join
Students can join:
- 10 minutes before scheduled time
- Immediately for active sessions

---

## Student User Flow

### Flow 1: Join Teacher's Class Session
1. Teacher starts video session for class
2. Student receives notification
3. Student logs in → Dashboard
4. Click "View Sessions" in Video Sessions card
5. See active session in list
6. Click "Join Session"
7. Enter video call room

### Flow 2: Join Scheduled Session
1. Teacher schedules session in advance
2. Student receives email with calendar invite
3. Student adds to calendar
4. 10 minutes before session time
5. Student logs in → Dashboard
6. Click "View Sessions"
7. Click "Join Session" (now available)
8. Enter video call room

### Flow 3: View Past Sessions
1. Student logs in → Dashboard
2. Click "View Sessions"
3. Filter by "Past Sessions"
4. Click on a session
5. View recording (if available)
6. See attendance and statistics

---

## Student Dashboard Layout

The student dashboard now has **8 action cards** in a 3-column grid:

**Row 1:**
1. Upload Content
2. Progress Analytics
3. Content Library

**Row 2:**
4. Join a Class
5. Study Partners
6. Study Groups

**Row 3:**
7. Find Tutors
8. **Video Sessions** (NEW!)

---

## Visual Design

### Video Sessions Card
- **Color**: Blue (bg-blue-500)
- **Icon**: Video camera icon (white)
- **Title**: "Video Sessions"
- **Description**: "Join class video calls"
- **Button**: "View Sessions" (blue background)

---

## What Students See in Video Sessions

### Session List Page (`/video/sessions/`)

**Tabs:**
- Upcoming Sessions
- Active Sessions (can join now)
- Past Sessions

**For Each Session:**
- Session title
- Host name (teacher)
- Scheduled time
- Duration
- Number of participants
- Status indicator
- Action button (Join/View Details)

### Session Detail Page

**Information Shown:**
- Session title and description
- Host information
- Scheduled time and duration
- Participant list
- Session status
- Recording availability (if completed)

**Actions Available:**
- Join Session (if active or early join window)
- Download Calendar Entry (.ics file)
- View Recording (if completed and available)

---

## Student Permissions

Students can:
- ✅ View sessions they're invited to
- ✅ Join sessions they're invited to
- ✅ Leave sessions anytime
- ✅ Control their own audio/video
- ✅ View session recordings (if enabled)
- ✅ Download calendar entries

Students cannot:
- ❌ Create new sessions
- ❌ Invite other participants
- ❌ Start/stop recording
- ❌ Remove other participants
- ❌ End the session

---

## Notifications

Students receive notifications for:
1. **Session Scheduled**: Email with calendar invite
2. **Session Starting Soon**: Reminder 10 minutes before
3. **Session Started**: When teacher starts the session
4. **Session Updated**: If teacher changes time/details
5. **Session Cancelled**: If teacher cancels
6. **Recording Available**: When recording is processed

---

## Integration Points

### Class Enrollment
- When teacher starts class video session
- All enrolled students automatically invited
- Attendance tracked when students join

### Tutor Bookings
- Video sessions linked to tutor bookings
- One-on-one sessions with tutors
- Automatic scheduling integration

### Parent Monitoring
- Parents can view child's video session history
- Notifications when child joins/leaves sessions
- Access to session recordings

---

## Mobile Support

The video sessions card is:
- ✅ Responsive on mobile devices
- ✅ Touch-friendly buttons
- ✅ Optimized for small screens
- ✅ Works on tablets and phones

---

## Comparison: Teacher vs Student Access

| Feature | Teacher | Student |
|---------|---------|---------|
| Create Sessions | ✅ Yes | ❌ No |
| Schedule Sessions | ✅ Yes | ❌ No |
| Join Sessions | ✅ Yes | ✅ Yes |
| View Sessions | ✅ Yes | ✅ Yes (invited only) |
| Start/Stop Recording | ✅ Yes | ❌ No |
| Remove Participants | ✅ Yes | ❌ No |
| End Session | ✅ Yes | ❌ No |
| Control Own Media | ✅ Yes | ✅ Yes |
| Screen Share | ✅ Yes | ⚠️ If enabled |
| View Recordings | ✅ Yes | ✅ Yes (if available) |

---

## Files Modified

### Templates
- `templates/accounts/student_dashboard.html` - Added Video Sessions card

### No Backend Changes
All backend functionality already exists. Only added UI access point.

---

## Testing Checklist

- [x] Student dashboard loads without errors
- [x] Video Sessions card displays correctly
- [x] View Sessions button links to `/video/sessions/`
- [x] Card has proper styling and hover effects
- [x] Card is responsive on mobile devices
- [x] Students can access session list
- [x] Students can join active sessions

---

## Next Steps for Students

Students can now:
1. ✅ View video sessions from dashboard
2. ✅ Join class video sessions
3. ✅ See upcoming scheduled sessions
4. ✅ Access past session recordings
5. ✅ Receive notifications for sessions

All video call functionality is now easily accessible for students!
