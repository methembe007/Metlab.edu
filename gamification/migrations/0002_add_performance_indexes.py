# Generated migration for adding performance indexes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gamification', '0001_initial'),
    ]

    operations = [
        # Student Achievement indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_student_achievement_student ON gamification_studentachievement(student_id, earned_at DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_student_achievement_student;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_student_achievement_notified ON gamification_studentachievement(student_id, notified) WHERE notified = false;",
            reverse_sql="DROP INDEX IF EXISTS idx_student_achievement_notified;"
        ),
        
        # Leaderboard indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_leaderboard_type_rank ON gamification_leaderboard(leaderboard_type, rank);",
            reverse_sql="DROP INDEX IF EXISTS idx_leaderboard_type_rank;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_leaderboard_student_type ON gamification_leaderboard(student_id, leaderboard_type);",
            reverse_sql="DROP INDEX IF EXISTS idx_leaderboard_student_type;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_leaderboard_subject_rank ON gamification_leaderboard(leaderboard_type, subject, rank) WHERE subject != '';",
            reverse_sql="DROP INDEX IF EXISTS idx_leaderboard_subject_rank;"
        ),
        
        # XP Transaction indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_xp_transaction_student_date ON gamification_xptransaction(student_id, created_at DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_xp_transaction_student_date;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_xp_transaction_source ON gamification_xptransaction(student_id, source, created_at DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_xp_transaction_source;"
        ),
        
        # Coin Transaction indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_coin_transaction_student_date ON gamification_cointransaction(student_id, created_at DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_coin_transaction_student_date;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_coin_transaction_type ON gamification_cointransaction(student_id, transaction_type, created_at DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_coin_transaction_type;"
        ),
        
        # Shop Item indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_shop_item_active_type ON gamification_shopitem(is_active, item_type, price);",
            reverse_sql="DROP INDEX IF EXISTS idx_shop_item_active_type;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_shop_item_stock ON gamification_shopitem(is_active, stock_quantity) WHERE stock_quantity IS NOT NULL;",
            reverse_sql="DROP INDEX IF EXISTS idx_shop_item_stock;"
        ),
        
        # Student Inventory indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_student_inventory_student ON gamification_studentinventory(student_id, is_active);",
            reverse_sql="DROP INDEX IF EXISTS idx_student_inventory_student;"
        ),
        
        # Purchase indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_purchase_student_date ON gamification_purchase(student_id, purchased_at DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_purchase_student_date;"
        ),
    ]