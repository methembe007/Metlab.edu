/**
 * Achievement Notification System
 * Handles real-time achievement notifications and badge unlocks
 */

class AchievementNotificationSystem {
    constructor() {
        this.checkInterval = 30000; // Check every 30 seconds
        this.notificationQueue = [];
        this.isShowingNotification = false;
        this.init();
    }

    init() {
        // Check for achievements on page load
        this.checkForNewAchievements();
        
        // Set up periodic checking
        setInterval(() => {
            this.checkForNewAchievements();
        }, this.checkInterval);
        
        // Create notification container if it doesn't exist
        this.createNotificationContainer();
    }

    createNotificationContainer() {
        if (!document.getElementById('achievement-notifications')) {
            const container = document.createElement('div');
            container.id = 'achievement-notifications';
            container.className = 'fixed top-4 right-4 z-50 space-y-2';
            document.body.appendChild(container);
        }
    }

    async checkForNewAchievements() {
        try {
            const response = await fetch('/gamification/api/check-achievements/');
            const data = await response.json();
            
            if (data.achievements && data.achievements.length > 0) {
                this.queueNotifications(data.achievements);
            }
        } catch (error) {
            console.error('Error checking for achievements:', error);
        }
    }

    queueNotifications(achievements) {
        achievements.forEach(achievement => {
            this.notificationQueue.push(achievement);
        });
        
        if (!this.isShowingNotification) {
            this.showNextNotification();
        }
    }

    showNextNotification() {
        if (this.notificationQueue.length === 0) {
            this.isShowingNotification = false;
            return;
        }

        this.isShowingNotification = true;
        const achievement = this.notificationQueue.shift();
        
        // Create notification element
        const notification = this.createNotificationElement(achievement);
        const container = document.getElementById('achievement-notifications');
        container.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-x-full', 'opacity-0');
        }, 100);

        // Auto-hide after 5 seconds
        setTimeout(() => {
            this.hideNotification(notification, achievement.id);
        }, 5000);
    }

    createNotificationElement(achievement) {
        const notification = document.createElement('div');
        notification.className = 'bg-white rounded-lg shadow-lg border-l-4 border-green-500 p-4 max-w-sm transform translate-x-full opacity-0 transition-all duration-300 cursor-pointer';
        notification.onclick = () => this.hideNotification(notification, achievement.id);
        
        notification.innerHTML = `
            <div class="flex items-start">
                <div class="flex-shrink-0">
                    <div class="text-3xl animate-bounce">${achievement.badge_icon}</div>
                </div>
                <div class="ml-3 flex-1">
                    <div class="flex items-center">
                        <h3 class="text-sm font-semibold text-gray-900">Achievement Unlocked!</h3>
                        <button class="ml-auto text-gray-400 hover:text-gray-600" onclick="event.stopPropagation(); this.parentElement.parentElement.parentElement.parentElement.remove();">
                            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                            </svg>
                        </button>
                    </div>
                    <p class="text-sm font-medium text-blue-600 mt-1">${achievement.name}</p>
                    <p class="text-xs text-gray-600 mt-1">${achievement.description}</p>
                    ${this.createRewardBadges(achievement)}
                </div>
            </div>
        `;
        
        return notification;
    }

    createRewardBadges(achievement) {
        let badges = '';
        
        if (achievement.xp_reward > 0) {
            badges += `<span class="inline-block bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded mr-2 mt-2">+${achievement.xp_reward} XP</span>`;
        }
        
        if (achievement.coin_reward > 0) {
            badges += `<span class="inline-block bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded mt-2">+${achievement.coin_reward} coins</span>`;
        }
        
        return badges ? `<div class="mt-2">${badges}</div>` : '';
    }

    hideNotification(notification, achievementId) {
        // Animate out
        notification.classList.add('translate-x-full', 'opacity-0');
        
        // Remove from DOM after animation
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
        
        // Mark as notified
        this.markAsNotified([achievementId]);
        
        // Show next notification after a brief delay
        setTimeout(() => {
            this.showNextNotification();
        }, 500);
    }

    async markAsNotified(achievementIds) {
        try {
            const formData = new FormData();
            achievementIds.forEach(id => formData.append('achievement_ids[]', id));
            
            // Get CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                             document.querySelector('meta[name=csrf-token]')?.getAttribute('content');
            
            if (csrfToken) {
                formData.append('csrfmiddlewaretoken', csrfToken);
            }
            
            await fetch('/gamification/api/mark-notified/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrfToken
                }
            });
        } catch (error) {
            console.error('Error marking achievements as notified:', error);
        }
    }

    // Public method to manually trigger achievement check
    checkNow() {
        this.checkForNewAchievements();
    }

    // Public method to show a custom achievement notification
    showCustomNotification(achievement) {
        this.queueNotifications([achievement]);
    }
}

// Initialize the notification system when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize for authenticated users
    if (document.body.dataset.userAuthenticated === 'true') {
        window.achievementNotifications = new AchievementNotificationSystem();
    }
});

// Expose utility functions globally
window.checkAchievements = function() {
    if (window.achievementNotifications) {
        window.achievementNotifications.checkNow();
    }
};

// Listen for custom events that might trigger achievements
document.addEventListener('lessonCompleted', function(event) {
    // Delay check to allow server to process the achievement
    setTimeout(() => {
        if (window.achievementNotifications) {
            window.achievementNotifications.checkNow();
        }
    }, 1000);
});

document.addEventListener('quizCompleted', function(event) {
    setTimeout(() => {
        if (window.achievementNotifications) {
            window.achievementNotifications.checkNow();
        }
    }, 1000);
});

document.addEventListener('streakUpdated', function(event) {
    setTimeout(() => {
        if (window.achievementNotifications) {
            window.achievementNotifications.checkNow();
        }
    }, 1000);
});