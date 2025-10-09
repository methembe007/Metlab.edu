# Generated migration for adding performance indexes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0001_initial'),
    ]

    operations = [
        # Learning Session indexes for performance-critical queries
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_learning_session_student_status ON learning_learningsession(student_id, status);",
            reverse_sql="DROP INDEX IF EXISTS idx_learning_session_student_status;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_learning_session_student_start_time ON learning_learningsession(student_id, start_time DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_learning_session_student_start_time;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_learning_session_content_student ON learning_learningsession(content_id, student_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_learning_session_content_student;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_learning_session_performance ON learning_learningsession(student_id, performance_score) WHERE performance_score IS NOT NULL;",
            reverse_sql="DROP INDEX IF EXISTS idx_learning_session_performance;"
        ),
        
        # Weakness Analysis indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_weakness_student_priority ON learning_weaknessanalysis(student_id, priority_level DESC, weakness_score DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_weakness_student_priority;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_weakness_student_subject ON learning_weaknessanalysis(student_id, subject);",
            reverse_sql="DROP INDEX IF EXISTS idx_weakness_student_subject;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_weakness_level ON learning_weaknessanalysis(weakness_level, priority_level DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_weakness_level;"
        ),
        
        # Personalized Recommendation indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_recommendation_student_status ON learning_personalizedrecommendation(student_id, status, priority DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_recommendation_student_status;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_recommendation_expires ON learning_personalizedrecommendation(expires_at) WHERE expires_at IS NOT NULL;",
            reverse_sql="DROP INDEX IF EXISTS idx_recommendation_expires;"
        ),
        
        # Daily Lesson indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_daily_lesson_student_date ON learning_dailylesson(student_id, lesson_date DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_daily_lesson_student_date;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_daily_lesson_status ON learning_dailylesson(student_id, status);",
            reverse_sql="DROP INDEX IF EXISTS idx_daily_lesson_status;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_daily_lesson_completed ON learning_dailylesson(student_id, completed_at DESC) WHERE completed_at IS NOT NULL;",
            reverse_sql="DROP INDEX IF EXISTS idx_daily_lesson_completed;"
        ),
        
        # Lesson Progress indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_lesson_progress_lesson ON learning_lessonprogress(lesson_id, activity_index);",
            reverse_sql="DROP INDEX IF EXISTS idx_lesson_progress_lesson;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_lesson_progress_concept ON learning_lessonprogress(concept, completed_at DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_lesson_progress_concept;"
        ),
    ]