"""
Security middleware for Metlab.edu platform
Handles file upload security, content scanning, and additional security measures
"""

import os
import hashlib
import logging
import time
from django.conf import settings
from django.http import JsonResponse, HttpResponseForbidden
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin
from django.core.exceptions import SuspiciousOperation

logger = logging.getLogger(__name__)

class SecurityMiddleware(MiddlewareMixin):
    """
    Middleware to handle various security measures including:
    - File upload security scanning
    - Content type validation
    - Malicious file detection
    - Additional security headers
    """
    
    DANGEROUS_EXTENSIONS = [
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js',
        '.jar', '.app', '.deb', '.pkg', '.dmg', '.sh', '.ps1', '.php'
    ]
    
    ALLOWED_MIME_TYPES = [
        'application/pdf',
        'text/plain',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'image/png',
        'image/jpeg',
        'image/jpg'
    ]

    def process_request(self, request):
        """Process incoming requests for security validation"""
        
        # Add security headers
        self.add_security_headers(request)
        
        # Check for file uploads
        if request.method == 'POST' and request.FILES:
            for field_name, uploaded_file in request.FILES.items():
                if not self.validate_file_upload(uploaded_file):
                    logger.warning(f"Malicious file upload attempt: {uploaded_file.name}")
                    return JsonResponse({
                        'error': 'File upload rejected for security reasons',
                        'code': 'SECURITY_VIOLATION'
                    }, status=400)
        
        return None

    def add_security_headers(self, request):
        """Add additional security headers to the request context"""
        # These will be added to the response in process_response
        request.security_headers = {
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
            'Content-Security-Policy': self.get_csp_header(),
        }

    def get_csp_header(self):
        """Generate Content Security Policy header"""
        return (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self' wss: ws:; "
            "media-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )

    def validate_file_upload(self, uploaded_file):
        """
        Comprehensive file upload validation
        Returns True if file is safe, False otherwise
        """
        try:
            # Check file size
            if uploaded_file.size > getattr(settings, 'MAX_FILE_SIZE', 25 * 1024 * 1024):
                logger.warning(f"File too large: {uploaded_file.size} bytes")
                return False
            
            # Check file extension
            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            if file_extension in self.DANGEROUS_EXTENSIONS:
                logger.warning(f"Dangerous file extension: {file_extension}")
                return False
            
            allowed_extensions = getattr(settings, 'ALLOWED_FILE_EXTENSIONS', [])
            if allowed_extensions and file_extension not in allowed_extensions:
                logger.warning(f"File extension not allowed: {file_extension}")
                return False
            
            # Check MIME type
            if hasattr(uploaded_file, 'content_type'):
                if uploaded_file.content_type not in self.ALLOWED_MIME_TYPES:
                    logger.warning(f"MIME type not allowed: {uploaded_file.content_type}")
                    return False
            
            # Basic file content validation (without python-magic for now)
            try:
                file_content = uploaded_file.read(1024)  # Read first 1KB
                uploaded_file.seek(0)  # Reset file pointer
                
                # Basic validation - check for common file signatures
                if not self.validate_file_signature(file_content, file_extension):
                    logger.warning(f"File signature doesn't match extension: {file_extension}")
                    return False
                    
            except Exception as e:
                logger.error(f"Error reading file content: {str(e)}")
                return False
            
            # Check for malicious patterns
            if self.scan_for_malicious_content(uploaded_file):
                logger.warning(f"Malicious content detected in file: {uploaded_file.name}")
                return False
            
            # Generate file hash for tracking
            file_hash = self.generate_file_hash(uploaded_file)
            
            # Check if file hash is in blacklist (you can maintain a blacklist of known bad files)
            if self.is_file_blacklisted(file_hash):
                logger.warning(f"File hash is blacklisted: {file_hash}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating file upload: {str(e)}")
            return False

    def scan_for_malicious_content(self, uploaded_file):
        """
        Scan file content for malicious patterns
        Returns True if malicious content is found
        """
        try:
            # Read file content in chunks
            uploaded_file.seek(0)
            content = uploaded_file.read()
            uploaded_file.seek(0)
            
            # Convert to string for text-based files
            try:
                text_content = content.decode('utf-8', errors='ignore').lower()
            except:
                text_content = str(content).lower()
            
            # Check for suspicious patterns
            malicious_patterns = [
                '<script',
                'javascript:',
                'vbscript:',
                'onload=',
                'onerror=',
                'eval(',
                'document.cookie',
                'window.location',
                'exec(',
                'system(',
                'shell_exec',
                'passthru',
                'base64_decode'
            ]
            
            for pattern in malicious_patterns:
                if pattern in text_content:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error scanning file content: {str(e)}")
            return True  # Err on the side of caution

    def validate_file_signature(self, file_content, file_extension):
        """
        Validate file signature against extension
        Basic validation without external libraries
        """
        if not file_content:
            return False
        
        # Common file signatures
        signatures = {
            '.pdf': [b'%PDF'],
            '.png': [b'\x89PNG\r\n\x1a\n'],
            '.jpg': [b'\xff\xd8\xff'],
            '.jpeg': [b'\xff\xd8\xff'],
            '.txt': [],  # Text files don't have specific signatures
            '.doc': [b'\xd0\xcf\x11\xe0'],
            '.docx': [b'PK\x03\x04'],  # ZIP-based format
        }
        
        expected_signatures = signatures.get(file_extension.lower(), [])
        
        # If no specific signature expected, allow it
        if not expected_signatures:
            return True
        
        # Check if file starts with any expected signature
        for signature in expected_signatures:
            if file_content.startswith(signature):
                return True
        
        return False

    def generate_file_hash(self, uploaded_file):
        """Generate SHA-256 hash of the uploaded file"""
        try:
            uploaded_file.seek(0)
            file_hash = hashlib.sha256()
            for chunk in iter(lambda: uploaded_file.read(4096), b""):
                file_hash.update(chunk)
            uploaded_file.seek(0)
            return file_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error generating file hash: {str(e)}")
            return None

    def is_file_blacklisted(self, file_hash):
        """Check if file hash is in the blacklist"""
        if not file_hash:
            return False
        
        # Check cache first
        cache_key = f"blacklist_hash_{file_hash}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # In a real implementation, you would check against a database
        # For now, we'll just return False
        blacklisted = False
        
        # Cache the result for 1 hour
        cache.set(cache_key, blacklisted, 3600)
        return blacklisted

    def process_response(self, request, response):
        """Add security headers to the response"""
        if hasattr(request, 'security_headers'):
            for header, value in request.security_headers.items():
                response[header] = value
        
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """
    Custom rate limiting middleware
    """
    
    def process_request(self, request):
        """Apply rate limiting to requests"""
        if not getattr(settings, 'RATE_LIMIT_ENABLE', True):
            return None
        
        # Get client IP
        client_ip = self.get_client_ip(request)
        
        # Check rate limits
        if self.is_rate_limited(client_ip, request):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JsonResponse({
                'error': 'Rate limit exceeded. Please try again later.',
                'code': 'RATE_LIMIT_EXCEEDED'
            }, status=429)
        
        return None

    def get_client_ip(self, request):
        """Get the client's IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def is_rate_limited(self, client_ip, request):
        """Check if the client has exceeded rate limits"""
        current_time = int(time.time())
        
        # Different limits for different endpoints
        if request.path.startswith('/api/'):
            return self.check_api_rate_limit(client_ip, current_time)
        elif request.path.startswith('/content/upload/'):
            return self.check_upload_rate_limit(client_ip, current_time)
        else:
            return self.check_general_rate_limit(client_ip, current_time)

    def check_general_rate_limit(self, client_ip, current_time):
        """Check general rate limits"""
        minute_key = f"rate_limit_{client_ip}_{current_time // 60}"
        hour_key = f"rate_limit_{client_ip}_{current_time // 3600}"
        
        minute_count = cache.get(minute_key, 0)
        hour_count = cache.get(hour_key, 0)
        
        per_minute = getattr(settings, 'RATE_LIMIT_PER_MINUTE', 60)
        per_hour = getattr(settings, 'RATE_LIMIT_PER_HOUR', 1000)
        
        if minute_count >= per_minute or hour_count >= per_hour:
            return True
        
        # Increment counters
        cache.set(minute_key, minute_count + 1, 60)
        cache.set(hour_key, hour_count + 1, 3600)
        
        return False

    def check_api_rate_limit(self, client_ip, current_time):
        """Check API-specific rate limits (more restrictive)"""
        minute_key = f"api_rate_limit_{client_ip}_{current_time // 60}"
        minute_count = cache.get(minute_key, 0)
        
        if minute_count >= 30:  # 30 API calls per minute
            return True
        
        cache.set(minute_key, minute_count + 1, 60)
        return False

    def check_upload_rate_limit(self, client_ip, current_time):
        """Check upload-specific rate limits"""
        hour_key = f"upload_rate_limit_{client_ip}_{current_time // 3600}"
        hour_count = cache.get(hour_key, 0)
        
        if hour_count >= 50:  # 50 uploads per hour
            return True
        
        cache.set(hour_key, hour_count + 1, 3600)
        return False