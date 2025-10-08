"""
Utility functions for gamification integration
"""

from django.db import transaction
from .services import (
    XPCalculationService, CoinRewardService, 
    AchievementService, LeaderboardService, StreakService
)


def process_lesson_completion(student_profile, lesson_score=None, perfect_score=False):
    """
    Process all gamification aspects when a student completes a lesson
    
    Args:
        student_profile: StudentProfile instance
        lesson_score: Score percentage (0-100) if available
        perfect_score: Boolean indicating if student got perfect score
    
    Returns:
        dict: Summary of rewards awarded
    """
    rewards = {
        'xp_awarded': 0,
        'coins_awarded': 0,
        'achievements_earned': [],
        'streak_updated': False,
        'streak_days': 0
    }
    
    with transaction.atomic():
        # Update learning streak first
        streak_days = StreakService.update_streak(student_profile)
        rewards['streak_updated'] = True
        rewards['streak_days'] = streak_days
        
        # Award XP for lesson completion
        xp_awarded = XPCalculationService.calculate_lesson_xp(
            student_profile, 
            lesson_score, 
            perfect_score
        )
        rewards['xp_awarded'] = xp_awarded
        
        # Award coins for lesson completion
        coins_awarded = CoinRewardService.award_lesson_coins(
            student_profile, 
            perfect_score
        )
        rewards['coins_awarded'] = coins_awarded
        
        # Check for new achievements
        new_achievements = AchievementService.check_and_award_achievements(student_profile)
        rewards['achievements_earned'] = [
            {
                'name': sa.achievement.name,
                'description': sa.achievement.description,
                'badge_icon': sa.achievement.badge_icon,
                'xp_reward': sa.achievement.xp_reward,
                'coin_reward': sa.achievement.coin_reward
            }
            for sa in new_achievements
        ]
        
        # Update leaderboard
        LeaderboardService.update_student_leaderboard(student_profile)
    
    return rewards


def process_quiz_completion(student_profile, correct_answers, total_questions, time_bonus=False):
    """
    Process gamification for quiz completion
    
    Args:
        student_profile: StudentProfile instance
        correct_answers: Number of correct answers
        total_questions: Total number of questions
        time_bonus: Whether student completed quickly for bonus
    
    Returns:
        dict: Summary of rewards awarded
    """
    rewards = {
        'xp_awarded': 0,
        'coins_awarded': 0,
        'achievements_earned': [],
        'perfect_score': False
    }
    
    perfect_score = correct_answers == total_questions
    rewards['perfect_score'] = perfect_score
    
    with transaction.atomic():
        # Award XP for quiz performance
        xp_awarded = XPCalculationService.calculate_quiz_xp(
            student_profile, 
            correct_answers, 
            total_questions, 
            time_bonus
        )
        rewards['xp_awarded'] = xp_awarded
        
        # Award coins if perfect score
        if perfect_score:
            coins_awarded = CoinRewardService.BASE_COIN_VALUES['quiz_perfect']
            currency = CoinRewardService.get_or_create_currency(student_profile)
            currency.add_coins(coins_awarded, "Perfect quiz score")
            rewards['coins_awarded'] = coins_awarded
        
        # Check for new achievements
        new_achievements = AchievementService.check_and_award_achievements(student_profile)
        rewards['achievements_earned'] = [
            {
                'name': sa.achievement.name,
                'description': sa.achievement.description,
                'badge_icon': sa.achievement.badge_icon,
                'xp_reward': sa.achievement.xp_reward,
                'coin_reward': sa.achievement.coin_reward
            }
            for sa in new_achievements
        ]
        
        # Update leaderboard
        LeaderboardService.update_student_leaderboard(student_profile)
    
    return rewards


def process_daily_goal_completion(student_profile):
    """
    Process gamification for daily goal completion
    
    Args:
        student_profile: StudentProfile instance
    
    Returns:
        dict: Summary of rewards awarded
    """
    rewards = {
        'xp_awarded': 0,
        'coins_awarded': 0,
        'achievements_earned': []
    }
    
    with transaction.atomic():
        # Award XP for daily goal
        xp_awarded = XPCalculationService.award_daily_goal_xp(student_profile)
        rewards['xp_awarded'] = xp_awarded
        
        # Award coins for daily goal
        coins_awarded = CoinRewardService.award_daily_goal_coins(student_profile)
        rewards['coins_awarded'] = coins_awarded
        
        # Check for new achievements
        new_achievements = AchievementService.check_and_award_achievements(student_profile)
        rewards['achievements_earned'] = [
            {
                'name': sa.achievement.name,
                'description': sa.achievement.description,
                'badge_icon': sa.achievement.badge_icon,
                'xp_reward': sa.achievement.xp_reward,
                'coin_reward': sa.achievement.coin_reward
            }
            for sa in new_achievements
        ]
        
        # Update leaderboard
        LeaderboardService.update_student_leaderboard(student_profile)
    
    return rewards


def get_student_gamification_summary(student_profile):
    """
    Get comprehensive gamification summary for a student
    
    Args:
        student_profile: StudentProfile instance
    
    Returns:
        dict: Complete gamification status
    """
    from .models import VirtualCurrency, StudentAchievement, Leaderboard
    
    # Get virtual currency
    try:
        currency = VirtualCurrency.objects.get(student=student_profile)
    except VirtualCurrency.DoesNotExist:
        currency = CoinRewardService.get_or_create_currency(student_profile)
    
    # Get achievements
    achievements = StudentAchievement.objects.filter(
        student=student_profile
    ).select_related('achievement').order_by('-earned_at')
    
    # Get leaderboard position
    weekly_rank = LeaderboardService.get_student_rank(
        student_profile, 'weekly'
    )
    monthly_rank = LeaderboardService.get_student_rank(
        student_profile, 'monthly'
    )
    all_time_rank = LeaderboardService.get_student_rank(
        student_profile, 'all_time'
    )
    
    return {
        'total_xp': student_profile.total_xp,
        'current_streak': student_profile.current_streak,
        'coins': currency.coins,
        'coins_earned_today': currency.earned_today,
        'coins_earned_this_week': currency.earned_this_week,
        'total_coins_earned': currency.total_earned,
        'achievements_count': achievements.count(),
        'recent_achievements': [
            {
                'name': sa.achievement.name,
                'description': sa.achievement.description,
                'badge_icon': sa.achievement.badge_icon,
                'earned_at': sa.earned_at
            }
            for sa in achievements[:5]  # Last 5 achievements
        ],
        'leaderboard_ranks': {
            'weekly': weekly_rank,
            'monthly': monthly_rank,
            'all_time': all_time_rank
        },
        'streak_multiplier': StreakService.get_streak_multiplier(
            student_profile.current_streak
        )
    }


def get_available_achievements(student_profile):
    """
    Get achievements that student can still earn
    
    Args:
        student_profile: StudentProfile instance
    
    Returns:
        QuerySet: Available achievements
    """
    from .models import Achievement, StudentAchievement
    
    earned_achievement_ids = StudentAchievement.objects.filter(
        student=student_profile
    ).values_list('achievement_id', flat=True)
    
    return Achievement.objects.filter(
        is_active=True
    ).exclude(id__in=earned_achievement_ids).order_by('xp_requirement')


def get_leaderboard_data(leaderboard_type='weekly', limit=10):
    """
    Get leaderboard data for display
    
    Args:
        leaderboard_type: Type of leaderboard ('weekly', 'monthly', 'all_time')
        limit: Number of top students to return
    
    Returns:
        list: Leaderboard data
    """
    top_students = LeaderboardService.get_top_students(
        leaderboard_type, limit
    )
    
    return [
        {
            'rank': entry.rank,
            'username': entry.student.user.username,
            'xp': getattr(entry, f'{leaderboard_type}_xp'),
            'streak': entry.student.current_streak
        }
        for entry in top_students
    ]