# Generated migration for adding performance indexes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0001_initial'),
    ]

    operations = [
        # UploadedContent indexes for performance-critical queries
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_uploaded_content_user_status ON content_uploadedcontent(user_id, processing_status);",
            reverse_sql="DROP INDEX IF EXISTS idx_uploaded_content_user_status;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_uploaded_content_subject ON content_uploadedcontent(subject) WHERE subject != '';",
            reverse_sql="DROP INDEX IF EXISTS idx_uploaded_content_subject;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_uploaded_content_type_status ON content_uploadedcontent(content_type, processing_status);",
            reverse_sql="DROP INDEX IF EXISTS idx_uploaded_content_type_status;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_uploaded_content_created ON content_uploadedcontent(created_at DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_uploaded_content_created;"
        ),
        
        # Generated Summary indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_generated_summary_content_type ON content_generatedsummary(content_id, summary_type);",
            reverse_sql="DROP INDEX IF EXISTS idx_generated_summary_content_type;"
        ),
        
        # Generated Quiz indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_generated_quiz_content ON content_generatedquiz(content_id, difficulty_level);",
            reverse_sql="DROP INDEX IF EXISTS idx_generated_quiz_content;"
        ),
        
        # Flashcard indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_flashcard_content_concept ON content_flashcard(content_id, concept_tag);",
            reverse_sql="DROP INDEX IF EXISTS idx_flashcard_content_concept;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_flashcard_difficulty ON content_flashcard(difficulty_level, order_index);",
            reverse_sql="DROP INDEX IF EXISTS idx_flashcard_difficulty;"
        ),
    ]