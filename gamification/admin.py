from django.contrib import admin
from .models import (
    Achievement, StudentAchievement, Leaderboard, 
    VirtualCurrency, CoinTransaction, XPTransaction,
    ShopItem, StudentInventory, Purchase
)


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['name', 'achievement_type', 'xp_requirement', 'xp_reward', 'coin_reward', 'is_active']
    list_filter = ['achievement_type', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['achievement_type', 'xp_requirement']


@admin.register(StudentAchievement)
class StudentAchievementAdmin(admin.ModelAdmin):
    list_display = ['student', 'achievement', 'earned_at', 'notified']
    list_filter = ['earned_at', 'notified', 'achievement__achievement_type']
    search_fields = ['student__user__username', 'achievement__name']
    ordering = ['-earned_at']
    raw_id_fields = ['student', 'achievement']


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ['student', 'leaderboard_type', 'subject', 'rank', 'weekly_xp', 'monthly_xp', 'all_time_xp']
    list_filter = ['leaderboard_type', 'subject']
    search_fields = ['student__user__username']
    ordering = ['leaderboard_type', 'rank']
    raw_id_fields = ['student']


@admin.register(VirtualCurrency)
class VirtualCurrencyAdmin(admin.ModelAdmin):
    list_display = ['student', 'coins', 'earned_today', 'earned_this_week', 'total_earned', 'total_spent']
    search_fields = ['student__user__username']
    ordering = ['-coins']
    raw_id_fields = ['student']
    readonly_fields = ['total_earned', 'total_spent']


@admin.register(CoinTransaction)
class CoinTransactionAdmin(admin.ModelAdmin):
    list_display = ['student', 'transaction_type', 'amount', 'reason', 'balance_after', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['student__user__username', 'reason']
    ordering = ['-created_at']
    raw_id_fields = ['student']


@admin.register(XPTransaction)
class XPTransactionAdmin(admin.ModelAdmin):
    list_display = ['student', 'source', 'base_xp', 'multiplier', 'final_xp', 'streak_bonus', 'created_at']
    list_filter = ['source', 'created_at']
    search_fields = ['student__user__username', 'description']
    ordering = ['-created_at']
    raw_id_fields = ['student']


@admin.register(ShopItem)
class ShopItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'item_type', 'price', 'is_active', 'is_limited', 'stock_quantity', 'level_requirement']
    list_filter = ['item_type', 'is_active', 'is_limited']
    search_fields = ['name', 'description']
    ordering = ['item_type', 'price']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'item_type', 'icon')
        }),
        ('Pricing & Availability', {
            'fields': ('price', 'is_active', 'is_limited', 'stock_quantity', 'level_requirement')
        }),
    )


@admin.register(StudentInventory)
class StudentInventoryAdmin(admin.ModelAdmin):
    list_display = ['student', 'item', 'quantity', 'is_active', 'purchased_at']
    list_filter = ['is_active', 'purchased_at', 'item__item_type']
    search_fields = ['student__user__username', 'item__name']
    ordering = ['-purchased_at']
    raw_id_fields = ['student', 'item']


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['student', 'item', 'quantity', 'total_price', 'status', 'purchased_at']
    list_filter = ['status', 'purchased_at', 'item__item_type']
    search_fields = ['student__user__username', 'item__name']
    ordering = ['-purchased_at']
    raw_id_fields = ['student', 'item']
