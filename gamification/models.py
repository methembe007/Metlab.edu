from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from accounts.models import StudentProfile
from datetime import timedelta


class Achievement(models.Model):
    """Model representing achievements that students can earn"""
    
    ACHIEVEMENT_TYPES = [
        ('streak', 'Learning Streak'),
        ('xp', 'Experience Points'),
        ('lesson', 'Lesson Completion'),
        ('quiz', 'Quiz Performance'),
        ('subject', 'Subject Mastery'),
        ('social', 'Social Interaction'),
        ('special', 'Special Event'),
    ]
    
    name = models.CharField(
        max_length=100,
        help_text="Name of the achievement"
    )
    description = models.TextField(
        help_text="Detailed description of how to earn this achievement"
    )
    badge_icon = models.CharField(
        max_length=50,
        help_text="Icon identifier for the achievement badge"
    )
    achievement_type = models.CharField(
        max_length=20,
        choices=ACHIEVEMENT_TYPES,
        help_text="Category of achievement"
    )
    xp_requirement = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="XP points required to unlock this achievement"
    )
    streak_requirement = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Streak days required to unlock this achievement"
    )
    lesson_requirement = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Number of lessons required to unlock this achievement"
    )
    xp_reward = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="XP points awarded when achievement is earned"
    )
    coin_reward = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Virtual coins awarded when achievement is earned"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this achievement is currently available"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_achievement_type_display()})"
    
    class Meta:
        verbose_name = "Achievement"
        verbose_name_plural = "Achievements"
        ordering = ['achievement_type', 'xp_requirement']


class StudentAchievement(models.Model):
    """Model tracking achievements earned by students"""
    
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='achievements'
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name='student_achievements'
    )
    earned_at = models.DateTimeField(auto_now_add=True)
    notified = models.BooleanField(
        default=False,
        help_text="Whether the student has been notified of this achievement"
    )
    
    def __str__(self):
        return f"{self.student.user.username} - {self.achievement.name}"
    
    class Meta:
        verbose_name = "Student Achievement"
        verbose_name_plural = "Student Achievements"
        unique_together = ['student', 'achievement']
        ordering = ['-earned_at']


class Leaderboard(models.Model):
    """Model for tracking student rankings and leaderboard positions"""
    
    LEADERBOARD_TYPES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('all_time', 'All Time'),
        ('subject', 'Subject Specific'),
    ]
    
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='leaderboard_entries'
    )
    leaderboard_type = models.CharField(
        max_length=20,
        choices=LEADERBOARD_TYPES,
        help_text="Type of leaderboard ranking"
    )
    subject = models.CharField(
        max_length=100,
        blank=True,
        help_text="Subject for subject-specific leaderboards"
    )
    weekly_xp = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="XP earned this week"
    )
    monthly_xp = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="XP earned this month"
    )
    all_time_xp = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total XP earned all time"
    )
    rank = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Current rank position"
    )
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        subject_str = f" - {self.subject}" if self.subject else ""
        return f"{self.student.user.username} - {self.get_leaderboard_type_display()}{subject_str} (Rank: {self.rank})"
    
    class Meta:
        verbose_name = "Leaderboard Entry"
        verbose_name_plural = "Leaderboard Entries"
        unique_together = ['student', 'leaderboard_type', 'subject']
        ordering = ['rank']


class VirtualCurrency(models.Model):
    """Model for tracking student virtual currency (coins)"""
    
    student = models.OneToOneField(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='virtual_currency'
    )
    coins = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Current coin balance"
    )
    earned_today = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Coins earned today"
    )
    earned_this_week = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Coins earned this week"
    )
    earned_this_month = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Coins earned this month"
    )
    total_earned = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total coins earned all time"
    )
    total_spent = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total coins spent all time"
    )
    last_updated = models.DateField(auto_now=True)
    
    def add_coins(self, amount, reason=""):
        """Add coins to the student's balance"""
        if amount > 0:
            self.coins += amount
            self.earned_today += amount
            self.earned_this_week += amount
            self.earned_this_month += amount
            self.total_earned += amount
            self.save()
            
            # Create transaction record
            CoinTransaction.objects.create(
                student=self.student,
                transaction_type='earned',
                amount=amount,
                reason=reason,
                balance_after=self.coins
            )
    
    def spend_coins(self, amount, reason=""):
        """Spend coins from the student's balance"""
        if amount > 0 and self.coins >= amount:
            self.coins -= amount
            self.total_spent += amount
            self.save()
            
            # Create transaction record
            CoinTransaction.objects.create(
                student=self.student,
                transaction_type='spent',
                amount=amount,
                reason=reason,
                balance_after=self.coins
            )
            return True
        return False
    
    def reset_daily_earnings(self):
        """Reset daily earnings counter"""
        self.earned_today = 0
        self.save()
    
    def reset_weekly_earnings(self):
        """Reset weekly earnings counter"""
        self.earned_this_week = 0
        self.save()
    
    def reset_monthly_earnings(self):
        """Reset monthly earnings counter"""
        self.earned_this_month = 0
        self.save()
    
    def __str__(self):
        return f"{self.student.user.username} - {self.coins} coins"
    
    class Meta:
        verbose_name = "Virtual Currency"
        verbose_name_plural = "Virtual Currencies"


class CoinTransaction(models.Model):
    """Model for tracking coin transaction history"""
    
    TRANSACTION_TYPES = [
        ('earned', 'Earned'),
        ('spent', 'Spent'),
        ('bonus', 'Bonus'),
        ('refund', 'Refund'),
    ]
    
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='coin_transactions'
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES,
        help_text="Type of coin transaction"
    )
    amount = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Amount of coins in transaction"
    )
    reason = models.CharField(
        max_length=200,
        help_text="Reason for the transaction"
    )
    balance_after = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Coin balance after this transaction"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student.user.username} - {self.get_transaction_type_display()} {self.amount} coins"
    
    class Meta:
        verbose_name = "Coin Transaction"
        verbose_name_plural = "Coin Transactions"
        ordering = ['-created_at']


class XPTransaction(models.Model):
    """Model for tracking XP earning history and calculations"""
    
    XP_SOURCES = [
        ('lesson_complete', 'Lesson Completion'),
        ('quiz_score', 'Quiz Performance'),
        ('streak_bonus', 'Streak Bonus'),
        ('achievement', 'Achievement Reward'),
        ('daily_goal', 'Daily Goal'),
        ('perfect_score', 'Perfect Score Bonus'),
        ('improvement', 'Improvement Bonus'),
    ]
    
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='xp_transactions'
    )
    source = models.CharField(
        max_length=20,
        choices=XP_SOURCES,
        help_text="Source of XP earning"
    )
    base_xp = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Base XP amount before multipliers"
    )
    multiplier = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.1), MaxValueValidator(10.0)],
        help_text="Multiplier applied to base XP"
    )
    final_xp = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Final XP amount after multipliers"
    )
    streak_bonus = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Additional XP from streak bonus"
    )
    description = models.CharField(
        max_length=200,
        help_text="Description of XP earning activity"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        """Calculate final XP including streak bonus"""
        self.final_xp = int(self.base_xp * self.multiplier) + self.streak_bonus
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.student.user.username} - {self.final_xp} XP from {self.get_source_display()}"
    
    class Meta:
        verbose_name = "XP Transaction"
        verbose_name_plural = "XP Transactions"
        ordering = ['-created_at']


class ShopItem(models.Model):
    """Model representing items available in the rewards shop"""
    
    ITEM_TYPES = [
        ('theme', 'Dashboard Theme'),
        ('hint', 'Quiz Hint'),
        ('customization', 'Profile Customization'),
        ('power_up', 'Learning Power-up'),
        ('avatar', 'Avatar Item'),
        ('badge', 'Special Badge'),
    ]
    
    name = models.CharField(
        max_length=100,
        help_text="Name of the shop item"
    )
    description = models.TextField(
        help_text="Description of what the item does"
    )
    item_type = models.CharField(
        max_length=20,
        choices=ITEM_TYPES,
        help_text="Category of shop item"
    )
    price = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Price in coins"
    )
    icon = models.CharField(
        max_length=50,
        help_text="Icon identifier for the item"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this item is available for purchase"
    )
    is_limited = models.BooleanField(
        default=False,
        help_text="Whether this is a limited-time item"
    )
    stock_quantity = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Available stock (null for unlimited)"
    )
    level_requirement = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Minimum student level required to purchase"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def is_available(self):
        """Check if item is available for purchase"""
        if not self.is_active:
            return False
        if self.stock_quantity is not None and self.stock_quantity <= 0:
            return False
        return True
    
    def can_purchase(self, student):
        """Check if a specific student can purchase this item"""
        if not self.is_available():
            return False, "Item not available"
        
        # Check if student has enough coins
        currency = getattr(student, 'virtual_currency', None)
        if not currency or currency.coins < self.price:
            return False, "Insufficient coins"
        
        # Check level requirement
        if student.level < self.level_requirement:
            return False, f"Level {self.level_requirement} required"
        
        # Check if already owned (for non-consumable items)
        if self.item_type in ['theme', 'customization', 'avatar', 'badge']:
            if StudentInventory.objects.filter(student=student, item=self).exists():
                return False, "Already owned"
        
        return True, "Can purchase"
    
    def __str__(self):
        return f"{self.name} ({self.price} coins)"
    
    class Meta:
        verbose_name = "Shop Item"
        verbose_name_plural = "Shop Items"
        ordering = ['item_type', 'price']


class StudentInventory(models.Model):
    """Model tracking items owned by students"""
    
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='inventory'
    )
    item = models.ForeignKey(
        ShopItem,
        on_delete=models.CASCADE,
        related_name='owners'
    )
    quantity = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Quantity owned (for consumable items)"
    )
    is_active = models.BooleanField(
        default=False,
        help_text="Whether this item is currently active/equipped"
    )
    purchased_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student.user.username} - {self.item.name} (x{self.quantity})"
    
    class Meta:
        verbose_name = "Student Inventory"
        verbose_name_plural = "Student Inventories"
        unique_together = ['student', 'item']
        ordering = ['-purchased_at']


class Purchase(models.Model):
    """Model tracking purchase transactions"""
    
    PURCHASE_STATUS = [
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='purchases'
    )
    item = models.ForeignKey(
        ShopItem,
        on_delete=models.CASCADE,
        related_name='purchases'
    )
    quantity = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Quantity purchased"
    )
    total_price = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Total price paid in coins"
    )
    status = models.CharField(
        max_length=20,
        choices=PURCHASE_STATUS,
        default='completed',
        help_text="Status of the purchase"
    )
    purchased_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student.user.username} - {self.item.name} x{self.quantity} ({self.status})"
    
    class Meta:
        verbose_name = "Purchase"
        verbose_name_plural = "Purchases"
        ordering = ['-purchased_at']
