"""
URL patterns for gamification features
"""

from django.urls import path
from . import views

app_name = 'gamification'

urlpatterns = [
    # Achievement views
    path('achievements/', views.achievements_view, name='achievements'),
    path('achievements/<int:achievement_id>/', views.achievement_detail, name='achievement_detail'),
    path('badges/', views.badges_view, name='badges'),
    
    # AJAX endpoints
    path('api/check-achievements/', views.check_new_achievements, name='check_achievements'),
    path('api/mark-notified/', views.mark_achievements_notified, name='mark_notified'),
    path('api/leaderboard/', views.leaderboard_api, name='leaderboard_api'),
    
    # Leaderboard and competition
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('competition/', views.competition_view, name='competition'),
    path('privacy/', views.privacy_settings, name='privacy_settings'),
    
    # Profile integration
    path('profile/achievements/', views.profile_achievements, name='profile_achievements'),
    
    # Shop and virtual currency
    path('shop/', views.shop_view, name='shop'),
    path('shop/purchase/', views.purchase_item, name='purchase_item'),
    path('inventory/', views.inventory_view, name='inventory'),
    path('inventory/activate/', views.activate_item, name='activate_item'),
    path('inventory/use/', views.use_item, name='use_item'),
    path('coins/history/', views.coin_history_view, name='coin_history'),
]