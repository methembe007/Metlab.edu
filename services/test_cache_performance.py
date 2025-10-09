"""
Test script to verify caching performance improvements
"""
import time
import django
import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'metlab_edu.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import StudentProfile
from learning.models import LearningSession, WeaknessAnalysis
from content.models import UploadedContent
from services.cache_service import (
    StudentCacheService, WeaknessCacheService, 
    AICacheService, CacheService
)
from learning.analytics import PerformanceAnalyticsEngine, WeaknessIdentificationEngine

User = get_user_model()


def test_student_profile_caching():
    """Test student profile caching performance"""
    print("Testing Student Profile Caching...")
    
    # Get a student profile
    student_profile = StudentProfile.objects.first()
    if not student_profile:
        print("No student profiles found. Skipping test.")
        return
    
    # Test without cache (cold)
    start_time = time.time()
    analytics_data = PerformanceAnalyticsEngine.analyze_learning_patterns(student_profile)
    cold_time = time.time() - start_time
    
    # Test with cache (warm)
    start_time = time.time()
    cached_analytics_data = PerformanceAnalyticsEngine.analyze_learning_patterns(student_profile)
    warm_time = time.time() - start_time
    
    print(f"Cold query time: {cold_time:.4f}s")
    print(f"Warm query time: {warm_time:.4f}s")
    print(f"Performance improvement: {(cold_time - warm_time) / cold_time * 100:.1f}%")
    print(f"Data consistency: {'✓' if analytics_data == cached_analytics_data else '✗'}")
    print()


def test_weakness_analysis_caching():
    """Test weakness analysis caching performance"""
    print("Testing Weakness Analysis Caching...")
    
    student_profile = StudentProfile.objects.first()
    if not student_profile:
        print("No student profiles found. Skipping test.")
        return
    
    # Clear cache first
    WeaknessCacheService.invalidate_student_weaknesses(student_profile.id)
    
    # Test without cache (cold)
    start_time = time.time()
    weaknesses = WeaknessIdentificationEngine.identify_weaknesses(student_profile)
    cold_time = time.time() - start_time
    
    # Test with cache (warm)
    start_time = time.time()
    cached_weaknesses = WeaknessIdentificationEngine.identify_weaknesses(student_profile)
    warm_time = time.time() - start_time
    
    print(f"Cold query time: {cold_time:.4f}s")
    print(f"Warm query time: {warm_time:.4f}s")
    print(f"Performance improvement: {(cold_time - warm_time) / cold_time * 100:.1f}%")
    print(f"Data consistency: {'✓' if weaknesses == cached_weaknesses else '✗'}")
    print()


def test_ai_concept_extraction_caching():
    """Test AI concept extraction caching"""
    print("Testing AI Concept Extraction Caching...")
    
    test_text = """
    Machine learning is a subset of artificial intelligence that focuses on algorithms 
    that can learn from data. Neural networks are a key component of deep learning, 
    which is used for pattern recognition and classification tasks.
    """
    
    # Clear cache first
    from content.ai_services import ConceptExtractor
    extractor = ConceptExtractor()
    
    # Test without cache (cold)
    start_time = time.time()
    concepts = extractor.extract_concepts(test_text)
    cold_time = time.time() - start_time
    
    # Test with cache (warm)
    start_time = time.time()
    cached_concepts = extractor.extract_concepts(test_text)
    warm_time = time.time() - start_time
    
    print(f"Cold extraction time: {cold_time:.4f}s")
    print(f"Warm extraction time: {warm_time:.4f}s")
    print(f"Performance improvement: {(cold_time - warm_time) / cold_time * 100:.1f}%")
    print(f"Extracted concepts: {concepts}")
    print(f"Data consistency: {'✓' if concepts == cached_concepts else '✗'}")
    print()


def test_cache_operations():
    """Test basic cache operations"""
    print("Testing Basic Cache Operations...")
    
    # Test setting and getting values
    test_key = "test_performance_key"
    test_value = {"test": "data", "number": 42, "list": [1, 2, 3]}
    
    # Set value
    start_time = time.time()
    success = CacheService.set(test_key, test_value, timeout=300)
    set_time = time.time() - start_time
    
    # Get value
    start_time = time.time()
    retrieved_value = CacheService.get(test_key)
    get_time = time.time() - start_time
    
    print(f"Cache set time: {set_time:.4f}s")
    print(f"Cache get time: {get_time:.4f}s")
    print(f"Set success: {'✓' if success else '✗'}")
    print(f"Data consistency: {'✓' if test_value == retrieved_value else '✗'}")
    
    # Clean up
    CacheService.delete(test_key)
    print()


def test_cache_invalidation():
    """Test cache invalidation"""
    print("Testing Cache Invalidation...")
    
    student_profile = StudentProfile.objects.first()
    if not student_profile:
        print("No student profiles found. Skipping test.")
        return
    
    # Cache some data
    StudentCacheService.cache_student_profile(student_profile)
    
    # Verify it's cached
    cached_data = StudentCacheService.get_cached_student_profile(student_profile.id)
    print(f"Data cached: {'✓' if cached_data else '✗'}")
    
    # Invalidate cache
    StudentCacheService.invalidate_student_profile(student_profile.id)
    
    # Verify it's invalidated
    cached_data_after = StudentCacheService.get_cached_student_profile(student_profile.id)
    print(f"Cache invalidated: {'✓' if not cached_data_after else '✗'}")
    print()


def run_performance_tests():
    """Run all performance tests"""
    print("=" * 60)
    print("CACHE PERFORMANCE TESTS")
    print("=" * 60)
    print()
    
    test_cache_operations()
    test_cache_invalidation()
    test_student_profile_caching()
    test_weakness_analysis_caching()
    test_ai_concept_extraction_caching()
    
    print("=" * 60)
    print("PERFORMANCE TESTS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    run_performance_tests()