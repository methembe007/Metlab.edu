"""
Management command to optimize database performance
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.core.cache import cache
from services.query_optimization import DatabaseHealthMonitor
from services.cache_service import CacheService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Optimize database performance and analyze query patterns'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--analyze-only',
            action='store_true',
            help='Only analyze database performance without making changes',
        )
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Clear all application caches',
        )
        parser.add_argument(
            '--vacuum',
            action='store_true',
            help='Run VACUUM on SQLite database to reclaim space',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting database optimization...')
        )
        
        # Analyze database performance
        self.analyze_database_performance()
        
        if not options['analyze_only']:
            # Run optimizations
            self.optimize_database()
        
        if options['clear_cache']:
            self.clear_application_caches()
        
        if options['vacuum']:
            self.vacuum_database()
        
        self.stdout.write(
            self.style.SUCCESS('Database optimization completed!')
        )
    
    def analyze_database_performance(self):
        """Analyze current database performance"""
        self.stdout.write('Analyzing database performance...')
        
        # Get database health metrics
        health_metrics = DatabaseHealthMonitor.check_database_performance()
        
        self.stdout.write(f"Database size: {health_metrics['database_size_mb']} MB")
        self.stdout.write(f"Total tables: {health_metrics['total_tables']}")
        
        # Show table statistics
        self.stdout.write('\nTable row counts:')
        for table, count in health_metrics['table_statistics'].items():
            self.stdout.write(f"  {table}: {count:,} rows")
        
        # Get index usage statistics
        index_stats = DatabaseHealthMonitor.get_index_usage_stats()
        self.stdout.write(f"\nTotal indexes: {index_stats['total_indexes']}")
        
        # Show optimization recommendations
        query_analysis = DatabaseHealthMonitor.analyze_query_patterns()
        self.stdout.write('\nOptimization recommendations:')
        for recommendation in query_analysis['recommendations']:
            self.stdout.write(f"  • {recommendation}")
    
    def optimize_database(self):
        """Run database optimizations"""
        self.stdout.write('Running database optimizations...')
        
        with connection.cursor() as cursor:
            # Analyze tables for SQLite
            cursor.execute("ANALYZE;")
            self.stdout.write('  ✓ Database statistics updated')
            
            # Update table statistics
            cursor.execute("PRAGMA optimize;")
            self.stdout.write('  ✓ Query planner optimized')
    
    def clear_application_caches(self):
        """Clear all application caches"""
        self.stdout.write('Clearing application caches...')
        
        try:
            # Clear default cache
            cache.clear()
            self.stdout.write('  ✓ Default cache cleared')
            
            # Clear specific cache aliases
            for cache_alias in ['ai_cache', 'analytics', 'sessions']:
                try:
                    specific_cache = CacheService.get_cache(cache_alias)
                    specific_cache.clear()
                    self.stdout.write(f'  ✓ {cache_alias} cache cleared')
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠ Failed to clear {cache_alias}: {e}')
                    )
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to clear caches: {e}')
            )
    
    def vacuum_database(self):
        """Run VACUUM on SQLite database"""
        self.stdout.write('Running database VACUUM...')
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("VACUUM;")
                self.stdout.write('  ✓ Database vacuumed successfully')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to vacuum database: {e}')
            )
    
    def show_cache_statistics(self):
        """Show cache usage statistics"""
        self.stdout.write('\nCache statistics:')
        
        # This would require Redis-specific commands in a real implementation
        # For now, just show that caching is configured
        cache_aliases = ['default', 'ai_cache', 'analytics', 'sessions']
        
        for alias in cache_aliases:
            try:
                cache_instance = CacheService.get_cache(alias)
                self.stdout.write(f"  {alias}: Configured and available")
            except Exception as e:
                self.stdout.write(f"  {alias}: Error - {e}")