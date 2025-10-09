# Generated migration for adding performance indexes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        # User indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_user_role_active ON accounts_user(role, is_active);",
            reverse_sql="DROP INDEX IF EXISTS idx_user_role_active;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_user_email_verified ON accounts_user(email_verified, is_active);",
            reverse_sql="DROP INDEX IF EXISTS idx_user_email_verified;"
        ),
        
        # Student Profile indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_student_profile_xp ON accounts_studentprofile(total_xp DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_student_profile_xp;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_student_profile_streak ON accounts_studentprofile(current_streak DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_student_profile_streak;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_student_profile_leaderboard ON accounts_studentprofile(leaderboard_visible, total_xp DESC) WHERE leaderboard_visible = true;",
            reverse_sql="DROP INDEX IF EXISTS idx_student_profile_leaderboard;"
        ),
        
        # Privacy Consent indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_privacy_consent_user_type ON accounts_privacyconsent(user_id, consent_type, granted);",
            reverse_sql="DROP INDEX IF EXISTS idx_privacy_consent_user_type;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_privacy_consent_granted_at ON accounts_privacyconsent(granted_at DESC) WHERE granted_at IS NOT NULL;",
            reverse_sql="DROP INDEX IF EXISTS idx_privacy_consent_granted_at;"
        ),
        
        # Data Deletion Request indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_deletion_request_status ON accounts_datadeletionrequest(status, requested_at DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_deletion_request_status;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_deletion_request_user ON accounts_datadeletionrequest(user_id, status);",
            reverse_sql="DROP INDEX IF EXISTS idx_deletion_request_user;"
        ),
        
        # Data Export Request indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_export_request_status ON accounts_dataexportrequest(status, requested_at DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_export_request_status;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_export_request_expires ON accounts_dataexportrequest(expires_at) WHERE expires_at IS NOT NULL;",
            reverse_sql="DROP INDEX IF EXISTS idx_export_request_expires;"
        ),
        
        # Audit Log indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_audit_log_user_timestamp ON accounts_auditlog(user_id, timestamp DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_audit_log_user_timestamp;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_audit_log_action_timestamp ON accounts_auditlog(action, timestamp DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_audit_log_action_timestamp;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_audit_log_resource ON accounts_auditlog(resource_type, resource_id, timestamp DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_audit_log_resource;"
        ),
    ]