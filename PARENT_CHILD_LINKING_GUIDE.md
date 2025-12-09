# Parent-Child Account Linking Guide

## Overview
The parent-child account linking feature allows parents to monitor their children's learning progress, set screen time limits, and receive notifications about their educational activities.

## How It Works

### For Students (Children)

1. **Access Profile Settings**
   - Log into your student account
   - Go to Dashboard → Profile Settings (or visit `/accounts/settings/student/`)
   
2. **Get Your Link Code**
   - Your unique parent link code is displayed on the Profile Settings page
   - Format: `PARENT_{student_id}` (e.g., `PARENT_123`)
   - This code is permanent and doesn't expire
   
3. **Share with Your Parent**
   - Give your parent two pieces of information:
     - Your username
     - Your parent link code
   - They'll need both to link your account

4. **View Linked Parents**
   - See which parents are linked to your account
   - Parents can monitor your progress once linked

### For Parents

1. **Access Link Child Account Page**
   - Log into your parent account
   - Go to Dashboard → Link Child Account (or visit `/learning/link-child/`)

2. **Enter Child's Information**
   - Enter your child's username
   - Enter the parent link code they provided
   - Click "Link Account"

3. **Monitor Progress**
   - Once linked, you can:
     - View your child's learning progress
     - See their completed lessons and achievements
     - Set screen time limits
     - Receive progress notifications
     - Send encouragement messages

4. **Manage Linked Children**
   - View all linked children on your parent dashboard
   - Unlink accounts if needed

## Technical Implementation

### Backend Components

**Models** (`accounts/models.py`):
- `StudentProfile.generate_parent_link_code()` - Generates unique link code
- `ParentProfile.children` - Many-to-many relationship with students

**Views** (`accounts/views.py`):
- `student_profile_settings()` - Shows link code to students
- `link_child_account()` - Allows parents to link children (in `learning/parent_views.py`)

**URLs**:
- `/accounts/settings/student/` - Student profile settings
- `/learning/link-child/` - Parent link child page

### Frontend Components

**Templates**:
- `templates/accounts/student_profile_settings.html` - Student settings page
- `templates/learning/link_child_account.html` - Parent linking page

**Features**:
- Copy-to-clipboard functionality for link codes
- Visual display of linked parents/children
- Instructions and help sections
- Responsive design for mobile devices

## Security Considerations

1. **Link Code Format**: Simple format based on student ID
2. **Authentication Required**: Both student and parent must be logged in
3. **Verification**: System verifies student exists before linking
4. **Privacy**: Students can see which parents are linked
5. **Unlinking**: Parents can unlink children if needed

## User Flow Diagram

```
Student                          Parent
   |                               |
   |---> Login                     |
   |---> Profile Settings          |
   |---> View Link Code            |
   |---> Share Code --------------->|
   |                               |---> Login
   |                               |---> Link Child Account
   |                               |---> Enter Username + Code
   |<--- Linked! <-----------------|
   |                               |
   |                               |---> View Child Progress
```

## API Endpoints

### Student Endpoints
- `GET /accounts/settings/student/` - View profile settings and link code

### Parent Endpoints
- `GET /learning/link-child/` - Show link form
- `POST /learning/link-child/` - Process link request
- `POST /learning/unlink-child/<child_id>/` - Unlink child account

## Database Schema

```sql
-- Many-to-many relationship
ParentProfile <---> StudentProfile
    (parents)         (children)
```

## Future Enhancements

1. **Time-Limited Codes**: Add expiration to link codes for security
2. **Email Verification**: Require email confirmation for linking
3. **Multiple Link Codes**: Allow students to generate multiple codes
4. **Link Requests**: Add approval workflow for linking
5. **Notifications**: Alert students when parents link their account
6. **Link History**: Track when accounts were linked/unlinked

## Troubleshooting

### Student Can't Find Link Code
- Ensure they're logged in as a student
- Check they have a StudentProfile created
- Visit `/accounts/settings/student/` directly

### Parent Can't Link Account
- Verify student username is correct
- Ensure link code matches exactly
- Check both accounts are active
- Verify student has generated their code

### Link Code Not Working
- Confirm code format: `PARENT_{number}`
- Check for typos or extra spaces
- Ensure student account exists

## Testing

To test the feature:

1. Create a student account
2. Log in as student and visit profile settings
3. Note the link code
4. Create a parent account
5. Log in as parent and go to link child page
6. Enter student username and link code
7. Verify linking was successful
8. Check parent can view child's progress

## Support

For issues or questions:
- Check the help section on the link child page
- Contact support at support@metlab.edu
- Review this documentation
