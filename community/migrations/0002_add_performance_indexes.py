# Generated migration for adding performance indexes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0001_initial'),
    ]

    operations = [
        # Tutor Profile indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_tutor_profile_status_rating ON community_tutorprofile(status, rating DESC) WHERE status = 'active';",
            reverse_sql="DROP INDEX IF EXISTS idx_tutor_profile_status_rating;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_tutor_profile_verified ON community_tutorprofile(verified, status);",
            reverse_sql="DROP INDEX IF EXISTS idx_tutor_profile_verified;"
        ),
        
        # Tutor Availability indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_tutor_availability_day_time ON community_tutoravailability(tutor_id, day_of_week, start_time, is_available);",
            reverse_sql="DROP INDEX IF EXISTS idx_tutor_availability_day_time;"
        ),
        
        # Tutor Booking indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_tutor_booking_tutor_time ON community_tutorbooking(tutor_id, scheduled_time DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_tutor_booking_tutor_time;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_tutor_booking_student_status ON community_tutorbooking(student_id, status, scheduled_time DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_tutor_booking_student_status;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_tutor_booking_status_time ON community_tutorbooking(status, scheduled_time) WHERE status IN ('confirmed', 'in_progress');",
            reverse_sql="DROP INDEX IF EXISTS idx_tutor_booking_status_time;"
        ),
        
        # Study Partner Request indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_partner_request_requested_status ON community_studypartnerrequest(requested_id, status);",
            reverse_sql="DROP INDEX IF EXISTS idx_partner_request_requested_status;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_partner_request_requester ON community_studypartnerrequest(requester_id, status, created_at DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_partner_request_requester;"
        ),
        
        # Study Group indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_study_group_subject_status ON community_studygroup(subject_id, status, is_public);",
            reverse_sql="DROP INDEX IF EXISTS idx_study_group_subject_status;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_study_group_created_by ON community_studygroup(created_by_id, status);",
            reverse_sql="DROP INDEX IF EXISTS idx_study_group_created_by;"
        ),
        
        # Study Group Membership indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_group_membership_student ON community_studygroupmembership(student_id, status);",
            reverse_sql="DROP INDEX IF EXISTS idx_group_membership_student;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_group_membership_group_status ON community_studygroupmembership(study_group_id, status);",
            reverse_sql="DROP INDEX IF EXISTS idx_group_membership_group_status;"
        ),
        
        # Study Session indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_study_session_time_status ON community_studysession(scheduled_time DESC, status);",
            reverse_sql="DROP INDEX IF EXISTS idx_study_session_time_status;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_study_session_created_by ON community_studysession(created_by_id, scheduled_time DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_study_session_created_by;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_study_session_partnership ON community_studysession(partnership_id, scheduled_time DESC) WHERE partnership_id IS NOT NULL;",
            reverse_sql="DROP INDEX IF EXISTS idx_study_session_partnership;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_study_session_group ON community_studysession(study_group_id, scheduled_time DESC) WHERE study_group_id IS NOT NULL;",
            reverse_sql="DROP INDEX IF EXISTS idx_study_session_group;"
        ),
        
        # Study Session Attendance indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_session_attendance_student ON community_studysessionattendance(student_id, status, created_at DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_session_attendance_student;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_session_attendance_session ON community_studysessionattendance(session_id, status);",
            reverse_sql="DROP INDEX IF EXISTS idx_session_attendance_session;"
        ),
    ]