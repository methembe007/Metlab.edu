"""
Gamification services for XP calculation, achievement tracking, and rewards
"""

from django.utils import timezone
from django.db.models import Sum, F, Q, Count, Avg, Max
from django.db import models
from datetime import timedelta, date
from .models import (
    Achievement, StudentAchievement, Leaderboard, 
    VirtualCurrency, CoinTransaction, XPTransaction
)
from accounts.models import StudentProfile
from services.cache_service import (
    LeaderboardCacheService, StudentCacheService,
    CacheInvalidationService
)
from services.query_optimization import QueryOptimizer, BulkOperationOptimizer


class XPCalculationService:
    """Service for calculating and awarding XP points"""
    
    # Base XP values for different activities
    BASE_XP_VALUES = {
        'lesson_complete': 10,
        'quiz_score': 5,  # per correct answer
        'daily_goal': 20,
        'perfect_score': 50,
        'improvement': 15,
    }
    
    # Streak multipliers
    STREAK_MULTIPLIERS = {
        (1, 6): 1.0,    # Days 1-6: no bonus
        (7, 13): 1.2,   # Week 1: 20% bonus
        (14, 29): 1.5,  # Weeks 2-4: 50% bonus
        (30, 59): 1.8,  # Months 1-2: 80% bonus
        (60, float('inf')): 2.0,  # 2+ months: 100% bonus
    }
    
    @classmethod
    def calculate_lesson_xp(cls, student_profile, lesson_score=None, perfect_score=False):
        """Calculate XP for lesson completion"""
        base_xp = cls.BASE_XP_VALUES['lesson_complete']
        
        # Add bonus for lesson score if provided
        if lesson_score is not None:
            score_bonus = int(lesson_score * 0.5)  # 0.5 XP per percentage point
            base_xp += score_bonus
        
        # Perfect score bonus
        if perfect_score:
            base_xp += cls.BASE_XP_VALUES['perfect_score']
        
        # Apply streak multiplier
        multiplier = cls._get_streak_multiplier(student_profile.current_streak)
        streak_bonus = cls._calculate_streak_bonus(student_profile.current_streak)
        
        return cls._award_xp(
            student_profile, 
            'lesson_complete', 
            base_xp, 
            multiplier, 
            streak_bonus,
            f"Lesson completion (Score: {lesson_score}%)" if lesson_score else "Lesson completion"
        )
    
    @classmethod
    def calculate_quiz_xp(cls, student_profile, correct_answers, total_questions, time_bonus=False):
        """Calculate XP for quiz performance"""
        base_xp = correct_answers * cls.BASE_XP_VALUES['quiz_score']
        
        # Perfect score bonus
        perfect_score = correct_answers == total_questions
        if perfect_score:
            base_xp += cls.BASE_XP_VALUES['perfect_score']
        
        # Time bonus for quick completion
        if time_bonus:
            base_xp += 10
        
        # Apply streak multiplier
        multiplier = cls._get_streak_multiplier(student_profile.current_streak)
        streak_bonus = cls._calculate_streak_bonus(student_profile.current_streak)
        
        return cls._award_xp(
            student_profile,
            'quiz_score',
            base_xp,
            multiplier,
            streak_bonus,
            f"Quiz: {correct_answers}/{total_questions} correct"
        )
    
    @classmethod
    def award_daily_goal_xp(cls, student_profile):
        """Award XP for completing daily learning goal"""
        base_xp = cls.BASE_XP_VALUES['daily_goal']
        multiplier = cls._get_streak_multiplier(student_profile.current_streak)
        streak_bonus = cls._calculate_streak_bonus(student_profile.current_streak)
        
        return cls._award_xp(
            student_profile,
            'daily_goal',
            base_xp,
            multiplier,
            streak_bonus,
            "Daily learning goal completed"
        )
    
    @classmethod
    def award_improvement_xp(cls, student_profile, improvement_percentage):
        """Award XP for performance improvement"""
        base_xp = cls.BASE_XP_VALUES['improvement']
        
        # Scale XP based on improvement percentage
        if improvement_percentage >= 20:
            base_xp *= 2
        elif improvement_percentage >= 10:
            base_xp *= 1.5
        
        multiplier = cls._get_streak_multiplier(student_profile.current_streak)
        streak_bonus = cls._calculate_streak_bonus(student_profile.current_streak)
        
        return cls._award_xp(
            student_profile,
            'improvement',
            base_xp,
            multiplier,
            streak_bonus,
            f"Performance improvement: {improvement_percentage}%"
        )
    
    @classmethod
    def award_streak_bonus_xp(cls, student_profile, streak_days):
        """Award bonus XP for maintaining learning streaks"""
        if streak_days < 7:
            return 0
        
        # Award bonus XP for streak milestones
        bonus_xp = 0
        if streak_days == 7:
            bonus_xp = 30
        elif streak_days == 14:
            bonus_xp = 60
        elif streak_days == 30:
            bonus_xp = 150
        elif streak_days % 30 == 0:  # Every 30 days
            bonus_xp = 100
        
        if bonus_xp > 0:
            return cls._award_xp(
                student_profile,
                'streak_bonus',
                bonus_xp,
                1.0,
                0,
                f"Streak milestone: {streak_days} days"
            )
        
        return 0
    
    @classmethod
    def _get_streak_multiplier(cls, streak_days):
        """Get XP multiplier based on current streak"""
        for (min_days, max_days), multiplier in cls.STREAK_MULTIPLIERS.items():
            if min_days <= streak_days <= max_days:
                return multiplier
        return 1.0
    
    @classmethod
    def _calculate_streak_bonus(cls, streak_days):
        """Calculate additional streak bonus XP"""
        if streak_days >= 30:
            return 10
        elif streak_days >= 14:
            return 5
        elif streak_days >= 7:
            return 2
        return 0
    
    @classmethod
    def _award_xp(cls, student_profile, source, base_xp, multiplier, streak_bonus, description):
        """Award XP to student and create transaction record"""
        final_xp = int(base_xp * multiplier) + streak_bonus
        
        # Update student's total XP
        student_profile.total_xp += final_xp
        student_profile.save()
        
        # Invalidate student caches
        CacheInvalidationService.invalidate_student_caches(student_profile.id)
        
        # Create XP transaction record
        XPTransaction.objects.create(
            student=student_profile,
            source=source,
            base_xp=base_xp,
            multiplier=multiplier,
            final_xp=final_xp,
            streak_bonus=streak_bonus,
            description=description
        )
        
        return final_xp


class CoinRewardService:
    """Service for managing virtual currency rewards"""
    
    # Base coin values for different activities
    BASE_COIN_VALUES = {
        'lesson_complete': 5,
        'quiz_perfect': 10,
        'daily_goal': 15,
        'streak_milestone': 25,
        'achievement': 20,
        'improvement': 10,
    }
    
    @classmethod
    def get_or_create_currency(cls, student_profile):
        """Get or create virtual currency record for student"""
        currency, created = VirtualCurrency.objects.get_or_create(
            student=student_profile,
            defaults={'coins': 0}
        )
        return currency
    
    @classmethod
    def award_lesson_coins(cls, student_profile, perfect_score=False):
        """Award coins for lesson completion"""
        currency = cls.get_or_create_currency(student_profile)
        coins = cls.BASE_COIN_VALUES['lesson_complete']
        
        if perfect_score:
            coins += cls.BASE_COIN_VALUES['quiz_perfect']
        
        # Streak bonus
        if student_profile.current_streak >= 7:
            coins += 2
        
        currency.add_coins(coins, "Lesson completion")
        return coins
    
    @classmethod
    def award_daily_goal_coins(cls, student_profile):
        """Award coins for completing daily goal"""
        currency = cls.get_or_create_currency(student_profile)
        coins = cls.BASE_COIN_VALUES['daily_goal']
        
        currency.add_coins(coins, "Daily goal completed")
        return coins
    
    @classmethod
    def award_streak_milestone_coins(cls, student_profile, streak_days):
        """Award coins for streak milestones"""
        currency = cls.get_or_create_currency(student_profile)
        
        # Award coins for specific milestones
        coins = 0
        if streak_days == 7:
            coins = 25
        elif streak_days == 14:
            coins = 50
        elif streak_days == 30:
            coins = 100
        elif streak_days % 30 == 0:  # Every 30 days
            coins = 75
        
        if coins > 0:
            currency.add_coins(coins, f"Streak milestone: {streak_days} days")
        
        return coins
    
    @classmethod
    def award_achievement_coins(cls, student_profile, achievement):
        """Award coins for earning an achievement"""
        if achievement.coin_reward > 0:
            currency = cls.get_or_create_currency(student_profile)
            currency.add_coins(
                achievement.coin_reward, 
                f"Achievement: {achievement.name}"
            )
            return achievement.coin_reward
        return 0


class AchievementService:
    """Service for managing student achievements"""
    
    @classmethod
    def check_and_award_achievements(cls, student_profile):
        """Check and award any new achievements for a student"""
        awarded_achievements = []
        
        # Get all active achievements the student hasn't earned yet
        earned_achievement_ids = StudentAchievement.objects.filter(
            student=student_profile
        ).values_list('achievement_id', flat=True)
        
        available_achievements = Achievement.objects.filter(
            is_active=True
        ).exclude(id__in=earned_achievement_ids)
        
        for achievement in available_achievements:
            if cls._check_achievement_criteria(student_profile, achievement):
                # Award the achievement
                student_achievement = StudentAchievement.objects.create(
                    student=student_profile,
                    achievement=achievement
                )
                
                # Award XP and coins
                if achievement.xp_reward > 0:
                    XPCalculationService._award_xp(
                        student_profile,
                        'achievement',
                        achievement.xp_reward,
                        1.0,
                        0,
                        f"Achievement: {achievement.name}"
                    )
                
                if achievement.coin_reward > 0:
                    CoinRewardService.award_achievement_coins(student_profile, achievement)
                
                awarded_achievements.append(student_achievement)
        
        return awarded_achievements
    
    @classmethod
    def get_student_achievements(cls, student_profile, include_progress=False):
        """Get all achievements for a student with optional progress information"""
        earned_achievements = StudentAchievement.objects.filter(
            student=student_profile
        ).select_related('achievement').order_by('-earned_at')
        
        if not include_progress:
            return earned_achievements
        
        # Get progress towards unearned achievements
        earned_achievement_ids = earned_achievements.values_list('achievement_id', flat=True)
        available_achievements = Achievement.objects.filter(
            is_active=True
        ).exclude(id__in=earned_achievement_ids)
        
        achievement_progress = []
        for achievement in available_achievements:
            progress = cls._calculate_achievement_progress(student_profile, achievement)
            achievement_progress.append({
                'achievement': achievement,
                'progress': progress,
                'earned': False
            })
        
        # Add earned achievements to the list
        for earned in earned_achievements:
            achievement_progress.append({
                'achievement': earned.achievement,
                'progress': 100,
                'earned': True,
                'earned_at': earned.earned_at
            })
        
        # Sort by achievement type and progress
        achievement_progress.sort(key=lambda x: (x['achievement'].achievement_type, -x['progress']))
        
        return achievement_progress
    
    @classmethod
    def get_recent_achievements(cls, student_profile, days=7):
        """Get achievements earned in the last N days"""
        cutoff_date = timezone.now() - timedelta(days=days)
        return StudentAchievement.objects.filter(
            student=student_profile,
            earned_at__gte=cutoff_date
        ).select_related('achievement').order_by('-earned_at')
    
    @classmethod
    def get_unnotified_achievements(cls, student_profile):
        """Get achievements that haven't been shown to the student yet"""
        return StudentAchievement.objects.filter(
            student=student_profile,
            notified=False
        ).select_related('achievement').order_by('-earned_at')
    
    @classmethod
    def mark_achievements_as_notified(cls, achievement_ids):
        """Mark achievements as notified"""
        StudentAchievement.objects.filter(
            id__in=achievement_ids
        ).update(notified=True)
    
    @classmethod
    def get_achievement_stats(cls, student_profile):
        """Get achievement statistics for a student"""
        total_achievements = Achievement.objects.filter(is_active=True).count()
        earned_achievements = StudentAchievement.objects.filter(
            student=student_profile
        ).count()
        
        # Get achievements by type
        achievements_by_type = {}
        for achievement_type, display_name in Achievement.ACHIEVEMENT_TYPES:
            total_type = Achievement.objects.filter(
                is_active=True,
                achievement_type=achievement_type
            ).count()
            earned_type = StudentAchievement.objects.filter(
                student=student_profile,
                achievement__achievement_type=achievement_type
            ).count()
            
            achievements_by_type[achievement_type] = {
                'display_name': display_name,
                'earned': earned_type,
                'total': total_type,
                'percentage': (earned_type / total_type * 100) if total_type > 0 else 0
            }
        
        return {
            'total_earned': earned_achievements,
            'total_available': total_achievements,
            'completion_percentage': (earned_achievements / total_achievements * 100) if total_achievements > 0 else 0,
            'by_type': achievements_by_type
        }
    
    @classmethod
    def _calculate_achievement_progress(cls, student_profile, achievement):
        """Calculate progress percentage towards an achievement"""
        progress = 0
        
        # XP-based achievements
        if achievement.xp_requirement > 0:
            progress = max(progress, (student_profile.total_xp / achievement.xp_requirement) * 100)
        
        # Streak-based achievements
        if achievement.streak_requirement > 0:
            progress = max(progress, (student_profile.current_streak / achievement.streak_requirement) * 100)
        
        # Lesson-based achievements
        if achievement.lesson_requirement > 0:
            from learning.models import DailyLesson
            completed_lessons = DailyLesson.objects.filter(
                student=student_profile,
                status='completed'
            ).count()
            progress = max(progress, (completed_lessons / achievement.lesson_requirement) * 100)
        
        # Quiz-based achievements (perfect score)
        if achievement.achievement_type == 'quiz':
            # For quiz achievements, we'll check if they've ever gotten a perfect score
            # This is a binary achievement, so progress is either 0 or 100
            from learning.models import DailyLesson
            perfect_scores = DailyLesson.objects.filter(
                student=student_profile,
                status='completed',
                score=100
            ).exists()
            progress = 100 if perfect_scores else 0
        
        return min(progress, 100)
    
    @classmethod
    def _check_achievement_criteria(cls, student_profile, achievement):
        """Check if student meets criteria for an achievement"""
        # Check XP requirement
        if achievement.xp_requirement > 0 and student_profile.total_xp < achievement.xp_requirement:
            return False
        
        # Check streak requirement
        if achievement.streak_requirement > 0 and student_profile.current_streak < achievement.streak_requirement:
            return False
        
        # Check lesson requirement
        if achievement.lesson_requirement > 0:
            from learning.models import DailyLesson
            completed_lessons = DailyLesson.objects.filter(
                student=student_profile,
                status='completed'
            ).count()
            if completed_lessons < achievement.lesson_requirement:
                return False
        
        return True


class LeaderboardService:
    """
    Service for managing leaderboards and rankings with privacy controls.
    
    Features:
    - Weekly, monthly, and all-time leaderboards
    - Subject-specific leaderboards
    - Privacy controls (students can opt out of public leaderboards)
    - Name display preferences (real name vs username)
    - Friendly competition features (nearby competitors)
    - Leaderboard statistics and analytics
    """
    
    @classmethod
    def update_student_leaderboard(cls, student_profile):
        """Update leaderboard entries for a student"""
        now = timezone.now()
        
        # Calculate XP for different time periods
        weekly_xp = cls._calculate_period_xp(student_profile, days=7)
        monthly_xp = cls._calculate_period_xp(student_profile, days=30)
        all_time_xp = student_profile.total_xp
        
        # Update or create leaderboard entries
        for leaderboard_type in ['weekly', 'monthly', 'all_time']:
            leaderboard, created = Leaderboard.objects.get_or_create(
                student=student_profile,
                leaderboard_type=leaderboard_type,
                subject='',  # General leaderboard
                defaults={
                    'weekly_xp': weekly_xp,
                    'monthly_xp': monthly_xp,
                    'all_time_xp': all_time_xp,
                    'rank': 0
                }
            )
            
            if not created:
                leaderboard.weekly_xp = weekly_xp
                leaderboard.monthly_xp = monthly_xp
                leaderboard.all_time_xp = all_time_xp
                leaderboard.save()
        
        # Update rankings
        cls._update_rankings()
    
    @classmethod
    def update_subject_leaderboard(cls, student_profile, subject):
        """Update subject-specific leaderboard for a student"""
        # Calculate subject-specific XP
        weekly_xp = cls._calculate_subject_period_xp(student_profile, subject, days=7)
        monthly_xp = cls._calculate_subject_period_xp(student_profile, subject, days=30)
        all_time_xp = cls._calculate_subject_period_xp(student_profile, subject, days=None)
        
        # Update or create subject leaderboard entry
        leaderboard, created = Leaderboard.objects.get_or_create(
            student=student_profile,
            leaderboard_type='subject',
            subject=subject,
            defaults={
                'weekly_xp': weekly_xp,
                'monthly_xp': monthly_xp,
                'all_time_xp': all_time_xp,
                'rank': 0
            }
        )
        
        if not created:
            leaderboard.weekly_xp = weekly_xp
            leaderboard.monthly_xp = monthly_xp
            leaderboard.all_time_xp = all_time_xp
            leaderboard.save()
        
        # Update subject rankings
        cls._update_subject_rankings(subject)
    
    @classmethod
    def _calculate_period_xp(cls, student_profile, days):
        """Calculate XP earned in the last N days"""
        cutoff_date = timezone.now() - timedelta(days=days)
        
        period_xp = XPTransaction.objects.filter(
            student=student_profile,
            created_at__gte=cutoff_date
        ).aggregate(total=Sum('final_xp'))['total'] or 0
        
        return period_xp
    
    @classmethod
    def _update_rankings(cls):
        """Update rankings for all leaderboard types"""
        for leaderboard_type in ['weekly', 'monthly', 'all_time']:
            xp_field = f'{leaderboard_type}_xp'
            
            # Get all entries for this leaderboard type, ordered by XP
            entries = Leaderboard.objects.filter(
                leaderboard_type=leaderboard_type,
                subject=''
            ).order_by(f'-{xp_field}')
            
            # Update ranks
            for rank, entry in enumerate(entries, 1):
                entry.rank = rank
                entry.save(update_fields=['rank'])
    
    @classmethod
    def get_top_students(cls, leaderboard_type='weekly', limit=10, subject='', include_private=False):
        """Get top students from leaderboard with privacy controls"""
        # Check cache first
        cached_leaderboard = LeaderboardCacheService.get_cached_leaderboard(
            leaderboard_type, subject, limit
        )
        if cached_leaderboard and not include_private:
            return cached_leaderboard
        
        # Use optimized query
        queryset = QueryOptimizer.optimize_leaderboard_query(
            leaderboard_type, subject, limit
        )
        
        # Filter out students who don't want to appear on leaderboards
        if not include_private:
            queryset = queryset.filter(student__leaderboard_visible=True)
        
        results = list(queryset)
        
        # Cache the results
        if not include_private:
            LeaderboardCacheService.cache_leaderboard(
                leaderboard_type, results, subject, limit
            )
        
        return results
    
    @classmethod
    def get_student_rank(cls, student_profile, leaderboard_type='weekly', subject=''):
        """Get a student's current rank"""
        try:
            leaderboard = Leaderboard.objects.get(
                student=student_profile,
                leaderboard_type=leaderboard_type,
                subject=subject
            )
            return leaderboard.rank
        except Leaderboard.DoesNotExist:
            return None
    
    @classmethod
    def get_student_competitors(cls, student_profile, leaderboard_type='weekly', subject='', range_size=5):
        """Get students ranked around the current student for friendly competition"""
        student_rank = cls.get_student_rank(student_profile, leaderboard_type, subject)
        
        if not student_rank:
            return []
        
        # Get students within range of current student's rank
        min_rank = max(1, student_rank - range_size)
        max_rank = student_rank + range_size
        
        competitors = Leaderboard.objects.filter(
            leaderboard_type=leaderboard_type,
            subject=subject,
            rank__gte=min_rank,
            rank__lte=max_rank,
            student__leaderboard_visible=True
        ).select_related('student__user').order_by('rank')
        
        return competitors
    
    @classmethod
    def get_leaderboard_stats(cls, leaderboard_type='weekly', subject=''):
        """Get statistics about the leaderboard"""
        queryset = Leaderboard.objects.filter(
            leaderboard_type=leaderboard_type,
            subject=subject,
            student__leaderboard_visible=True
        )
        
        if not queryset.exists():
            return {
                'total_participants': 0,
                'average_xp': 0,
                'top_xp': 0,
                'active_learners': 0
            }
        
        xp_field = f'{leaderboard_type}_xp' if leaderboard_type != 'all_time' else 'all_time_xp'
        
        stats = queryset.aggregate(
            total_participants=models.Count('id'),
            average_xp=models.Avg(xp_field),
            top_xp=models.Max(xp_field)
        )
        
        # Count active learners (those with XP > 0 in the period)
        active_learners = queryset.filter(**{f'{xp_field}__gt': 0}).count()
        
        return {
            'total_participants': stats['total_participants'],
            'average_xp': round(stats['average_xp'] or 0),
            'top_xp': stats['top_xp'] or 0,
            'active_learners': active_learners
        }
    
    @classmethod
    def get_available_subjects(cls):
        """Get list of subjects that have leaderboard entries"""
        subjects = Leaderboard.objects.filter(
            leaderboard_type='subject',
            student__leaderboard_visible=True
        ).values_list('subject', flat=True).distinct()
        
        return sorted([s for s in subjects if s])
    
    @classmethod
    def _calculate_subject_period_xp(cls, student_profile, subject, days=None):
        """Calculate XP earned for a specific subject in a time period"""
        from learning.models import DailyLesson
        
        queryset = DailyLesson.objects.filter(
            student=student_profile,
            status='completed'
        )
        
        # Filter by subject if we can determine it from lesson content
        # This is a simplified approach - in a real implementation, you'd want
        # to track subject information more explicitly
        if subject:
            queryset = queryset.filter(content__icontains=subject)
        
        if days:
            cutoff_date = timezone.now() - timedelta(days=days)
            queryset = queryset.filter(completed_at__gte=cutoff_date)
        
        # Calculate XP based on lesson scores
        total_xp = 0
        for lesson in queryset:
            if lesson.score:
                total_xp += int(lesson.score * 0.1)  # Convert score to XP
        
        return total_xp
    
    @classmethod
    def _update_subject_rankings(cls, subject):
        """Update rankings for a specific subject leaderboard"""
        entries = Leaderboard.objects.filter(
            leaderboard_type='subject',
            subject=subject
        ).order_by('-all_time_xp')
        
        for rank, entry in enumerate(entries, 1):
            entry.rank = rank
            entry.save(update_fields=['rank'])


class StreakService:
    """Service for managing learning streaks and bonuses"""
    
    @classmethod
    def update_streak(cls, student_profile):
        """Update student's learning streak"""
        student_profile.update_learning_streak()
        student_profile.save()
        
        # Check for streak milestone rewards
        streak_days = student_profile.current_streak
        
        # Award streak milestone XP
        if streak_days in [7, 14, 30] or (streak_days > 30 and streak_days % 30 == 0):
            XPCalculationService.award_streak_bonus_xp(student_profile, streak_days)
            CoinRewardService.award_streak_milestone_coins(student_profile, streak_days)
        
        return streak_days
    
    @classmethod
    def get_streak_multiplier(cls, streak_days):
        """Get the current streak multiplier for rewards"""
        return XPCalculationService._get_streak_multiplier(streak_days)


class ShopService:
    """Service for managing the virtual currency shop and purchases"""
    
    @classmethod
    def get_shop_items(cls, student_profile=None, item_type=None, available_only=True):
        """Get shop items, optionally filtered by type and availability"""
        from .models import ShopItem
        
        queryset = ShopItem.objects.all()
        
        if item_type:
            queryset = queryset.filter(item_type=item_type)
        
        if available_only:
            queryset = queryset.filter(is_active=True)
            # Filter out items with no stock
            queryset = queryset.filter(
                models.Q(stock_quantity__isnull=True) | models.Q(stock_quantity__gt=0)
            )
        
        # If student provided, add purchase status and availability info
        if student_profile:
            items = []
            for item in queryset:
                can_purchase, reason = item.can_purchase(student_profile)
                items.append({
                    'item': item,
                    'can_purchase': can_purchase,
                    'reason': reason,
                    'owned': cls.student_owns_item(student_profile, item)
                })
            return items
        
        return queryset.order_by('item_type', 'price')
    
    @classmethod
    def get_shop_items_by_category(cls, student_profile=None):
        """Get shop items organized by category"""
        from .models import ShopItem
        
        categories = {}
        for item_type, display_name in ShopItem.ITEM_TYPES:
            items = cls.get_shop_items(student_profile, item_type)
            if items:
                categories[item_type] = {
                    'display_name': display_name,
                    'items': items
                }
        
        return categories
    
    @classmethod
    def purchase_item(cls, student_profile, item_id, quantity=1):
        """Purchase an item from the shop"""
        from .models import ShopItem, StudentInventory, Purchase
        from django.db import transaction
        
        try:
            item = ShopItem.objects.get(id=item_id)
        except ShopItem.DoesNotExist:
            return False, "Item not found"
        
        # Check if student can purchase
        can_purchase, reason = item.can_purchase(student_profile)
        if not can_purchase:
            return False, reason
        
        # Check quantity
        if quantity < 1:
            return False, "Invalid quantity"
        
        # Check stock for multiple quantities
        if item.stock_quantity is not None and item.stock_quantity < quantity:
            return False, f"Only {item.stock_quantity} items available"
        
        total_price = item.price * quantity
        currency = CoinRewardService.get_or_create_currency(student_profile)
        
        if currency.coins < total_price:
            return False, "Insufficient coins"
        
        # Process purchase in transaction
        with transaction.atomic():
            # Deduct coins
            success = currency.spend_coins(total_price, f"Purchased {item.name} x{quantity}")
            if not success:
                return False, "Failed to process payment"
            
            # Update stock
            if item.stock_quantity is not None:
                item.stock_quantity -= quantity
                item.save()
            
            # Add to inventory
            inventory_item, created = StudentInventory.objects.get_or_create(
                student=student_profile,
                item=item,
                defaults={'quantity': quantity}
            )
            
            if not created:
                inventory_item.quantity += quantity
                inventory_item.save()
            
            # Create purchase record
            Purchase.objects.create(
                student=student_profile,
                item=item,
                quantity=quantity,
                total_price=total_price,
                status='completed'
            )
        
        return True, f"Successfully purchased {item.name} x{quantity}"
    
    @classmethod
    def get_student_inventory(cls, student_profile, item_type=None):
        """Get student's inventory items"""
        from .models import StudentInventory
        
        queryset = StudentInventory.objects.filter(
            student=student_profile
        ).select_related('item').order_by('-purchased_at')
        
        if item_type:
            queryset = queryset.filter(item__item_type=item_type)
        
        return queryset
    
    @classmethod
    def student_owns_item(cls, student_profile, item):
        """Check if student owns a specific item"""
        from .models import StudentInventory
        
        return StudentInventory.objects.filter(
            student=student_profile,
            item=item
        ).exists()
    
    @classmethod
    def activate_item(cls, student_profile, item_id):
        """Activate/equip an item from inventory"""
        from .models import StudentInventory
        
        try:
            inventory_item = StudentInventory.objects.get(
                student=student_profile,
                item_id=item_id
            )
        except StudentInventory.DoesNotExist:
            return False, "Item not found in inventory"
        
        # For items that can only have one active (themes, customizations)
        if inventory_item.item.item_type in ['theme', 'customization', 'avatar']:
            # Deactivate other items of the same type
            StudentInventory.objects.filter(
                student=student_profile,
                item__item_type=inventory_item.item.item_type,
                is_active=True
            ).update(is_active=False)
        
        # Activate this item
        inventory_item.is_active = True
        inventory_item.save()
        
        return True, f"Activated {inventory_item.item.name}"
    
    @classmethod
    def use_consumable_item(cls, student_profile, item_id, quantity=1):
        """Use a consumable item from inventory"""
        from .models import StudentInventory
        
        try:
            inventory_item = StudentInventory.objects.get(
                student=student_profile,
                item_id=item_id
            )
        except StudentInventory.DoesNotExist:
            return False, "Item not found in inventory"
        
        if inventory_item.quantity < quantity:
            return False, "Insufficient quantity"
        
        # Use the item
        inventory_item.quantity -= quantity
        if inventory_item.quantity <= 0:
            inventory_item.delete()
        else:
            inventory_item.save()
        
        # Apply item effects (this would be expanded based on item types)
        effect_message = cls._apply_item_effects(student_profile, inventory_item.item, quantity)
        
        return True, effect_message
    
    @classmethod
    def get_purchase_history(cls, student_profile, limit=20):
        """Get student's purchase history"""
        from .models import Purchase
        
        return Purchase.objects.filter(
            student=student_profile
        ).select_related('item').order_by('-purchased_at')[:limit]
    
    @classmethod
    def get_coin_transaction_history(cls, student_profile, limit=50):
        """Get student's coin transaction history"""
        from .models import CoinTransaction
        
        return CoinTransaction.objects.filter(
            student=student_profile
        ).order_by('-created_at')[:limit]
    
    @classmethod
    def get_shop_stats(cls, student_profile):
        """Get shop statistics for a student"""
        from .models import Purchase, CoinTransaction
        
        currency = CoinRewardService.get_or_create_currency(student_profile)
        
        # Purchase stats
        total_purchases = Purchase.objects.filter(
            student=student_profile,
            status='completed'
        ).count()
        
        total_spent = currency.total_spent
        
        # Most purchased item type
        from django.db.models import Count
        popular_type = Purchase.objects.filter(
            student=student_profile,
            status='completed'
        ).values('item__item_type').annotate(
            count=Count('id')
        ).order_by('-count').first()
        
        return {
            'current_balance': currency.coins,
            'total_earned': currency.total_earned,
            'total_spent': total_spent,
            'total_purchases': total_purchases,
            'most_popular_type': popular_type['item__item_type'] if popular_type else None,
            'coins_earned_today': currency.earned_today,
            'coins_earned_this_week': currency.earned_this_week,
            'coins_earned_this_month': currency.earned_this_month
        }
    
    @classmethod
    def _apply_item_effects(cls, student_profile, item, quantity):
        """Apply effects when using consumable items"""
        effects = []
        
        if item.item_type == 'hint':
            effects.append(f"Used {quantity} quiz hint(s)")
        elif item.item_type == 'power_up':
            # Example: XP boost for next lesson
            effects.append(f"Applied {quantity} learning power-up(s)")
        
        return "; ".join(effects) if effects else f"Used {item.name} x{quantity}"