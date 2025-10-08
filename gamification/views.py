"""
Views for gamification features including achievements, badges, and leaderboards
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

from accounts.decorators import student_required
from .models import Achievement, StudentAchievement, Leaderboard, VirtualCurrency
from .services import AchievementService, LeaderboardService


@login_required
@student_required
def achievements_view(request):
    """Display student's achievements and progress"""
    student_profile = request.user.student_profile
    
    # Get achievement progress
    achievement_progress = AchievementService.get_student_achievements(
        student_profile, 
        include_progress=True
    )
    
    # Get achievement statistics
    stats = AchievementService.get_achievement_stats(student_profile)
    
    # Get recent achievements
    recent_achievements = AchievementService.get_recent_achievements(student_profile, days=30)
    
    context = {
        'achievement_progress': achievement_progress,
        'stats': stats,
        'recent_achievements': recent_achievements,
        'student_profile': student_profile,
    }
    
    return render(request, 'gamification/achievements.html', context)


@login_required
@student_required
def achievement_detail(request, achievement_id):
    """Display detailed information about a specific achievement"""
    achievement = get_object_or_404(Achievement, id=achievement_id, is_active=True)
    student_profile = request.user.student_profile
    
    # Check if student has earned this achievement
    try:
        student_achievement = StudentAchievement.objects.get(
            student=student_profile,
            achievement=achievement
        )
        earned = True
        earned_at = student_achievement.earned_at
    except StudentAchievement.DoesNotExist:
        earned = False
        earned_at = None
    
    # Calculate progress if not earned
    progress = 0
    if not earned:
        progress = AchievementService._calculate_achievement_progress(
            student_profile, 
            achievement
        )
    
    context = {
        'achievement': achievement,
        'earned': earned,
        'earned_at': earned_at,
        'progress': progress,
        'student_profile': student_profile,
    }
    
    return render(request, 'gamification/achievement_detail.html', context)


@login_required
@student_required
@require_http_methods(["GET"])
def check_new_achievements(request):
    """AJAX endpoint to check for new achievements and return notifications"""
    student_profile = request.user.student_profile
    
    # Get unnotified achievements
    unnotified_achievements = AchievementService.get_unnotified_achievements(student_profile)
    
    achievements_data = []
    for student_achievement in unnotified_achievements:
        achievements_data.append({
            'id': student_achievement.id,
            'name': student_achievement.achievement.name,
            'description': student_achievement.achievement.description,
            'badge_icon': student_achievement.achievement.badge_icon,
            'xp_reward': student_achievement.achievement.xp_reward,
            'coin_reward': student_achievement.achievement.coin_reward,
            'earned_at': student_achievement.earned_at.isoformat(),
        })
    
    return JsonResponse({
        'achievements': achievements_data,
        'count': len(achievements_data)
    })


@login_required
@student_required
@require_http_methods(["POST"])
def mark_achievements_notified(request):
    """AJAX endpoint to mark achievements as notified"""
    achievement_ids = request.POST.getlist('achievement_ids[]')
    
    if achievement_ids:
        # Verify these achievements belong to the current student
        valid_ids = StudentAchievement.objects.filter(
            id__in=achievement_ids,
            student=request.user.student_profile
        ).values_list('id', flat=True)
        
        AchievementService.mark_achievements_as_notified(valid_ids)
        
        return JsonResponse({
            'success': True,
            'marked_count': len(valid_ids)
        })
    
    return JsonResponse({'success': False, 'error': 'No achievement IDs provided'})


@login_required
@student_required
def leaderboard_view(request):
    """Display leaderboards for different time periods"""
    student_profile = request.user.student_profile
    leaderboard_type = request.GET.get('type', 'weekly')
    subject = request.GET.get('subject', '')
    
    # Validate leaderboard type
    valid_types = ['weekly', 'monthly', 'all_time']
    if leaderboard_type not in valid_types:
        leaderboard_type = 'weekly'
    
    # Get top students
    top_students = LeaderboardService.get_top_students(
        leaderboard_type=leaderboard_type,
        limit=50,
        subject=subject
    )
    
    # Get current student's rank
    student_rank = LeaderboardService.get_student_rank(
        student_profile,
        leaderboard_type=leaderboard_type,
        subject=subject
    )
    
    # Get student's leaderboard entry
    try:
        student_entry = Leaderboard.objects.get(
            student=student_profile,
            leaderboard_type=leaderboard_type,
            subject=subject
        )
    except Leaderboard.DoesNotExist:
        student_entry = None
    
    # Get competitors (students ranked around current student)
    competitors = LeaderboardService.get_student_competitors(
        student_profile,
        leaderboard_type=leaderboard_type,
        subject=subject,
        range_size=3
    )
    
    # Get leaderboard statistics
    stats = LeaderboardService.get_leaderboard_stats(
        leaderboard_type=leaderboard_type,
        subject=subject
    )
    
    # Get available subjects for subject filter
    available_subjects = LeaderboardService.get_available_subjects()
    
    context = {
        'top_students': top_students,
        'student_rank': student_rank,
        'student_entry': student_entry,
        'competitors': competitors,
        'stats': stats,
        'leaderboard_type': leaderboard_type,
        'subject': subject,
        'valid_types': valid_types,
        'available_subjects': available_subjects,
        'student_profile': student_profile,
    }
    
    return render(request, 'gamification/leaderboard.html', context)


@login_required
@student_required
def badges_view(request):
    """Display student's earned badges in a visual gallery"""
    student_profile = request.user.student_profile
    
    # Get all achievements grouped by type
    earned_achievements = StudentAchievement.objects.filter(
        student=student_profile
    ).select_related('achievement').order_by('-earned_at')
    
    # Group achievements by type
    achievements_by_type = {}
    for student_achievement in earned_achievements:
        achievement_type = student_achievement.achievement.achievement_type
        if achievement_type not in achievements_by_type:
            achievements_by_type[achievement_type] = {
                'display_name': student_achievement.achievement.get_achievement_type_display(),
                'achievements': []
            }
        achievements_by_type[achievement_type]['achievements'].append(student_achievement)
    
    # Get total badge count
    total_badges = earned_achievements.count()
    total_possible = Achievement.objects.filter(is_active=True).count()
    
    context = {
        'achievements_by_type': achievements_by_type,
        'total_badges': total_badges,
        'total_possible': total_possible,
        'completion_percentage': (total_badges / total_possible * 100) if total_possible > 0 else 0,
        'student_profile': student_profile,
    }
    
    return render(request, 'gamification/badges.html', context)


@login_required
@student_required
def profile_achievements(request):
    """Display achievements in user profile context"""
    student_profile = request.user.student_profile
    
    # Get recent achievements (last 5)
    recent_achievements = AchievementService.get_recent_achievements(
        student_profile, 
        days=30
    )[:5]
    
    # Get achievement stats
    stats = AchievementService.get_achievement_stats(student_profile)
    
    # Get virtual currency info
    try:
        currency = VirtualCurrency.objects.get(student=student_profile)
    except VirtualCurrency.DoesNotExist:
        currency = None
    
    context = {
        'recent_achievements': recent_achievements,
        'stats': stats,
        'currency': currency,
        'student_profile': student_profile,
    }
    
    return render(request, 'gamification/profile_achievements.html', context)


@login_required
@student_required
def privacy_settings(request):
    """Handle leaderboard privacy settings"""
    student_profile = request.user.student_profile
    
    if request.method == 'POST':
        # Update privacy settings
        leaderboard_visible = request.POST.get('leaderboard_visible') == 'on'
        show_real_name = request.POST.get('show_real_name') == 'on'
        
        student_profile.leaderboard_visible = leaderboard_visible
        student_profile.show_real_name = show_real_name
        student_profile.save()
        
        messages.success(request, 'Privacy settings updated successfully!')
        return redirect('gamification:privacy_settings')
    
    context = {
        'student_profile': student_profile,
    }
    
    return render(request, 'gamification/privacy_settings.html', context)


@login_required
@student_required
def competition_view(request):
    """Display friendly competition features"""
    student_profile = request.user.student_profile
    leaderboard_type = request.GET.get('type', 'weekly')
    
    # Validate leaderboard type
    valid_types = ['weekly', 'monthly', 'all_time']
    if leaderboard_type not in valid_types:
        leaderboard_type = 'weekly'
    
    # Get competitors (students ranked around current student)
    competitors = LeaderboardService.get_student_competitors(
        student_profile,
        leaderboard_type=leaderboard_type,
        range_size=5
    )
    
    # Get student's current rank and entry
    student_rank = LeaderboardService.get_student_rank(
        student_profile,
        leaderboard_type=leaderboard_type
    )
    
    try:
        student_entry = Leaderboard.objects.get(
            student=student_profile,
            leaderboard_type=leaderboard_type,
            subject=''
        )
    except Leaderboard.DoesNotExist:
        student_entry = None
    
    # Calculate XP needed to advance
    xp_to_next_rank = 0
    next_rank_student = None
    
    if student_rank and student_rank > 1:
        try:
            next_rank_entry = Leaderboard.objects.get(
                leaderboard_type=leaderboard_type,
                subject='',
                rank=student_rank - 1
            )
            next_rank_student = next_rank_entry.student
            
            current_xp = getattr(student_entry, f'{leaderboard_type}_xp', 0)
            next_rank_xp = getattr(next_rank_entry, f'{leaderboard_type}_xp', 0)
            xp_to_next_rank = max(0, next_rank_xp - current_xp + 1)
            
        except Leaderboard.DoesNotExist:
            pass
    
    # Get recent achievements for motivation
    recent_achievements = AchievementService.get_recent_achievements(
        student_profile, 
        days=7
    )[:3]
    
    context = {
        'competitors': competitors,
        'student_rank': student_rank,
        'student_entry': student_entry,
        'xp_to_next_rank': xp_to_next_rank,
        'next_rank_student': next_rank_student,
        'recent_achievements': recent_achievements,
        'leaderboard_type': leaderboard_type,
        'valid_types': valid_types,
        'student_profile': student_profile,
    }
    
    return render(request, 'gamification/competition.html', context)


@login_required
@student_required
@require_http_methods(["GET"])
def leaderboard_api(request):
    """API endpoint for leaderboard data"""
    leaderboard_type = request.GET.get('type', 'weekly')
    subject = request.GET.get('subject', '')
    limit = min(int(request.GET.get('limit', 10)), 100)  # Max 100 entries
    
    # Validate leaderboard type
    valid_types = ['weekly', 'monthly', 'all_time']
    if leaderboard_type not in valid_types:
        leaderboard_type = 'weekly'
    
    # Get top students
    top_students = LeaderboardService.get_top_students(
        leaderboard_type=leaderboard_type,
        limit=limit,
        subject=subject
    )
    
    # Get current student's rank
    student_rank = LeaderboardService.get_student_rank(
        request.user.student_profile,
        leaderboard_type=leaderboard_type,
        subject=subject
    )
    
    # Format data for JSON response
    students_data = []
    for entry in top_students:
        display_name = entry.student.user.first_name if entry.student.show_real_name and entry.student.user.first_name else entry.student.user.username
        
        students_data.append({
            'rank': entry.rank,
            'name': display_name,
            'xp': getattr(entry, f'{leaderboard_type}_xp', 0),
            'total_xp': entry.student.total_xp,
            'streak': entry.student.current_streak,
            'is_current_user': entry.student == request.user.student_profile
        })
    
    return JsonResponse({
        'students': students_data,
        'current_user_rank': student_rank,
        'leaderboard_type': leaderboard_type,
        'subject': subject
    })


# Shop Views

@login_required
@student_required
def shop_view(request):
    """Display the virtual currency shop"""
    from .services import ShopService, CoinRewardService
    
    student_profile = request.user.student_profile
    category = request.GET.get('category', 'all')
    
    # Get shop items by category
    if category == 'all':
        shop_items = ShopService.get_shop_items(student_profile)
        categories = ShopService.get_shop_items_by_category(student_profile)
    else:
        shop_items = ShopService.get_shop_items(student_profile, item_type=category)
        categories = ShopService.get_shop_items_by_category(student_profile)
    
    # Get student's currency info
    currency = CoinRewardService.get_or_create_currency(student_profile)
    
    # Get shop statistics
    shop_stats = ShopService.get_shop_stats(student_profile)
    
    context = {
        'shop_items': shop_items,
        'categories': categories,
        'current_category': category,
        'currency': currency,
        'shop_stats': shop_stats,
        'student_profile': student_profile,
    }
    
    return render(request, 'gamification/shop.html', context)


@login_required
@student_required
@require_http_methods(["POST"])
def purchase_item(request):
    """Handle item purchase from the shop"""
    from .services import ShopService
    import json
    
    student_profile = request.user.student_profile
    
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        quantity = data.get('quantity', 1)
        
        if not item_id:
            return JsonResponse({
                'success': False,
                'error': 'Item ID is required'
            })
        
        # Attempt purchase
        success, message = ShopService.purchase_item(
            student_profile, 
            item_id, 
            quantity
        )
        
        if success:
            # Get updated currency balance
            from .services import CoinRewardService
            currency = CoinRewardService.get_or_create_currency(student_profile)
            
            return JsonResponse({
                'success': True,
                'message': message,
                'new_balance': currency.coins
            })
        else:
            return JsonResponse({
                'success': False,
                'error': message
            })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'An error occurred during purchase'
        })


@login_required
@student_required
def inventory_view(request):
    """Display student's inventory"""
    from .services import ShopService
    
    student_profile = request.user.student_profile
    category = request.GET.get('category', 'all')
    
    # Get inventory items
    if category == 'all':
        inventory_items = ShopService.get_student_inventory(student_profile)
    else:
        inventory_items = ShopService.get_student_inventory(student_profile, item_type=category)
    
    # Group items by category
    items_by_category = {}
    for inventory_item in inventory_items:
        item_type = inventory_item.item.item_type
        if item_type not in items_by_category:
            items_by_category[item_type] = {
                'display_name': inventory_item.item.get_item_type_display(),
                'items': []
            }
        items_by_category[item_type]['items'].append(inventory_item)
    
    context = {
        'inventory_items': inventory_items,
        'items_by_category': items_by_category,
        'current_category': category,
        'student_profile': student_profile,
    }
    
    return render(request, 'gamification/inventory.html', context)


@login_required
@student_required
@require_http_methods(["POST"])
def activate_item(request):
    """Activate/equip an item from inventory"""
    from .services import ShopService
    import json
    
    student_profile = request.user.student_profile
    
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        
        if not item_id:
            return JsonResponse({
                'success': False,
                'error': 'Item ID is required'
            })
        
        success, message = ShopService.activate_item(student_profile, item_id)
        
        return JsonResponse({
            'success': success,
            'message': message
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'An error occurred'
        })


@login_required
@student_required
@require_http_methods(["POST"])
def use_item(request):
    """Use a consumable item from inventory"""
    from .services import ShopService
    import json
    
    student_profile = request.user.student_profile
    
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        quantity = data.get('quantity', 1)
        
        if not item_id:
            return JsonResponse({
                'success': False,
                'error': 'Item ID is required'
            })
        
        success, message = ShopService.use_consumable_item(
            student_profile, 
            item_id, 
            quantity
        )
        
        return JsonResponse({
            'success': success,
            'message': message
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'An error occurred'
        })


@login_required
@student_required
def coin_history_view(request):
    """Display coin transaction history"""
    from .services import ShopService, CoinRewardService
    
    student_profile = request.user.student_profile
    
    # Get transaction history
    transactions = ShopService.get_coin_transaction_history(student_profile, limit=100)
    
    # Get purchase history
    purchases = ShopService.get_purchase_history(student_profile, limit=50)
    
    # Get current currency info
    currency = CoinRewardService.get_or_create_currency(student_profile)
    
    # Get shop statistics
    shop_stats = ShopService.get_shop_stats(student_profile)
    
    context = {
        'transactions': transactions,
        'purchases': purchases,
        'currency': currency,
        'shop_stats': shop_stats,
        'student_profile': student_profile,
    }
    
    return render(request, 'gamification/coin_history.html', context)