"""
Services app configuration.
"""

from django.apps import AppConfig


class ServicesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'services'
    verbose_name = 'Monitoring and Analytics Services'
    
    def ready(self):
        """Initialize monitoring services when app is ready."""
        # Import monitoring to initialize global instances
        from . import monitoring