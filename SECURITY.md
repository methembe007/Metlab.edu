# Security Implementation - Metlab.edu

This document outlines the security measures implemented in the Metlab.edu AI learning platform.

## Security Features Implemented

### 1. CSRF Protection and Secure Headers

- **CSRF Protection**: Django's built-in CSRF protection is enabled with custom failure handling
- **Security Headers**: 
  - `X-Frame-Options: DENY` - Prevents clickjacking
  - `X-Content-Type-Options: nosniff` - Prevents MIME type sniffing
  - `X-XSS-Protection: 1; mode=block` - XSS protection
  - `Strict-Transport-Security` - HTTPS enforcement (production)
  - `Content-Security-Policy` - Controls resource loading
  - `Referrer-Policy` - Controls referrer information

### 2. File Upload Security

- **File Extension Validation**: Only allows specific file types (.pdf, .txt, .doc, .docx, .png, .jpg, .jpeg)
- **File Size Limits**: Maximum 25MB per file
- **MIME Type Validation**: Validates actual file content against declared type
- **File Signature Validation**: Checks file headers to prevent disguised malicious files
- **Malicious Content Scanning**: Scans for suspicious patterns in file content
- **File Hash Tracking**: Generates SHA-256 hashes for uploaded files

### 3. Rate Limiting

- **Login Rate Limiting**: 5 attempts per minute per IP
- **API Rate Limiting**: 30 requests per minute per IP for API endpoints
- **Upload Rate Limiting**: 20 file uploads per hour per user
- **General Rate Limiting**: 60 requests per minute, 1000 per hour per IP
- **Privacy Action Rate Limiting**: Limited consent updates, deletion/export requests

### 4. Data Privacy Compliance (GDPR/COPPA)

#### GDPR Compliance Features:
- **Privacy Consent Management**: Track and manage user consents for different data processing types
- **Right to be Forgotten**: Users can request complete data deletion
- **Right to Data Portability**: Users can export their personal data
- **Audit Logging**: Complete audit trail of data access and modifications
- **Data Retention Policies**: Configurable retention periods for different data types

#### COPPA Compliance Features:
- **Age Verification**: Special handling for users under 13
- **Parental Consent**: Email verification system for parent consent
- **Enhanced Privacy Controls**: Additional restrictions for child accounts

### 5. Session Security

- **Secure Session Configuration**:
  - `SESSION_COOKIE_HTTPONLY = True` - Prevents JavaScript access to session cookies
  - `SESSION_COOKIE_SECURE = True` - HTTPS-only cookies (production)
  - `SESSION_COOKIE_SAMESITE = 'Lax'` - CSRF protection
  - `SESSION_EXPIRE_AT_BROWSER_CLOSE = True` - Sessions expire when browser closes
  - `SESSION_COOKIE_AGE = 3600` - 1-hour session timeout

### 6. Password Security

- **Strong Password Validation**: Django's built-in validators
- **Password Hashing**: PBKDF2 with SHA256 (Django default)
- **Account Lockout**: Rate limiting prevents brute force attacks

## Security Middleware

### SecurityMiddleware
- Validates file uploads
- Adds security headers
- Scans for malicious content
- Generates file hashes

### RateLimitMiddleware
- Implements rate limiting across the application
- Different limits for different endpoint types
- IP-based and user-based limiting

## Privacy Models

### PrivacyConsent
- Tracks user consent for different data processing types
- Records IP address and user agent for audit purposes
- Supports consent withdrawal

### DataRetentionPolicy
- Defines retention periods for different data types
- Configurable and manageable through admin interface

### DataDeletionRequest
- Handles "Right to be Forgotten" requests
- Workflow for processing deletion requests

### DataExportRequest
- Handles "Right to Data Portability" requests
- Secure file generation and download

### AuditLog
- Complete audit trail of user actions
- Tracks data access and modifications
- Immutable logging for compliance

### COPPACompliance
- Special handling for users under 13
- Parent verification workflow
- Enhanced privacy controls

## Management Commands

### cleanup_old_data
```bash
python manage.py cleanup_old_data [--dry-run] [--data-type TYPE]
```
Cleans up old data based on retention policies.

### initialize_privacy_policies
```bash
python manage.py initialize_privacy_policies
```
Sets up default data retention policies.

## Configuration

### Security Settings (settings.py)
```python
# Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# File Security
ALLOWED_FILE_EXTENSIONS = ['.pdf', '.txt', '.doc', '.docx', '.png', '.jpg', '.jpeg']
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB
VIRUS_SCAN_ENABLED = True

# Rate Limiting
RATE_LIMIT_ENABLE = True
RATE_LIMIT_PER_MINUTE = 60
RATE_LIMIT_PER_HOUR = 1000
RATE_LIMIT_PER_DAY = 10000

# Privacy Compliance
DATA_RETENTION_DAYS = 365 * 2  # 2 years
GDPR_COMPLIANCE = True
COPPA_COMPLIANCE = True
PRIVACY_POLICY_VERSION = '1.0'
```

## Testing

Security tests are included in `accounts/tests_security.py`:
- CSRF protection tests
- Rate limiting tests
- Privacy compliance tests
- File upload security tests

Run tests with:
```bash
python manage.py test accounts.tests_security
```

## Production Deployment Notes

1. **HTTPS Configuration**: Set `SECURE_SSL_REDIRECT = True` and configure proper SSL certificates
2. **Environment Variables**: Store sensitive settings in environment variables
3. **Database Security**: Use encrypted connections and proper access controls
4. **Regular Updates**: Keep Django and dependencies updated
5. **Monitoring**: Set up security monitoring and alerting
6. **Backup Security**: Encrypt backups and secure backup storage

## Compliance Checklist

### GDPR Compliance:
- ✅ Lawful basis for processing
- ✅ Consent management
- ✅ Right to access (data export)
- ✅ Right to rectification (user profile updates)
- ✅ Right to erasure (data deletion)
- ✅ Right to data portability (data export)
- ✅ Data retention policies
- ✅ Audit logging

### COPPA Compliance:
- ✅ Age verification
- ✅ Parental consent mechanism
- ✅ Limited data collection for children
- ✅ Enhanced privacy controls

## Security Incident Response

1. **Detection**: Monitor logs and alerts
2. **Assessment**: Evaluate the scope and impact
3. **Containment**: Isolate affected systems
4. **Investigation**: Analyze the incident
5. **Recovery**: Restore normal operations
6. **Documentation**: Record lessons learned

## Contact

For security issues or questions, contact the development team or create a security issue in the project repository.