# Monitoring and Logging System

This module provides comprehensive monitoring, logging, and analytics capabilities for the Metlab.edu platform.

## Features

### 1. Structured Logging with Correlation IDs
- Every request gets a unique correlation ID for tracing
- Structured JSON logging for better parsing and analysis
- Automatic correlation ID propagation across services

### 2. Performance Monitoring
- Automatic performance tracking for all requests
- AI processing performance metrics
- Database query optimization monitoring
- Custom performance decorators for specific operations

### 3. Error Tracking and Alerting
- Comprehensive error logging with context
- Automatic alert generation for critical issues
- Error resolution tracking
- Stack trace capture and analysis

### 4. User Activity Analytics
- User behavior tracking
- Activity pattern analysis
- Session monitoring
- Privacy-compliant data collection

### 5. AI Processing Metrics
- AI operation performance tracking
- Token usage and cost monitoring
- Success/failure rate analysis
- Processing time optimization

### 6. Real-time Dashboard
- Live system health monitoring
- Performance metrics visualization
- Error rate tracking
- User activity analytics

## Usage

### Basic Monitoring

```python
from services.monitoring import monitoring, monitor_performance

# Log performance of a function
@monitor_performance('my_operation')
def my_function():
    # Your code here
    pass

# Log user activity
monitoring.log_user_activity(user.id, 'content_upload', {'file_type': 'pdf'})

# Log errors with context
try:
    risky_operation()
except Exception as e:
    monitoring.log_error(e, {'operation': 'risky_operation', 'user_id': user.id})
```

### AI Processing Monitoring

```python
from services.monitoring import monitor_ai_processing

@monitor_ai_processing
def generate_summary(text):
    # AI processing code
    return summary
```

### Correlation ID Context

```python
from services.monitoring import monitoring

# Use correlation context for related operations
with monitoring.correlation_context() as correlation_id:
    # All operations in this block will share the same correlation ID
    result1 = operation1()
    result2 = operation2()
```

## Dashboard Access

The monitoring dashboard is available at `/services/monitoring/` for staff users.

### Dashboard Features:
- System health overview
- Performance metrics charts
- Error rate monitoring
- User activity tracking
- AI processing analytics
- Alert management

## Management Commands

### Generate Demo Data
```bash
python manage.py demo_monitoring --count 10
```

### Check System Health
```bash
python manage.py check_system_health --hours 24
```

### Clean Up Old Logs
```bash
python manage.py cleanup_old_logs --days 30
```

## Configuration

### Middleware Setup
The following middleware is automatically configured:
- `CorrelationIDMiddleware` - Adds correlation IDs to requests
- `PerformanceMonitoringMiddleware` - Tracks request performance
- `UserActivityMiddleware` - Logs user activities

### Logging Configuration
Structured logging is configured with separate log files:
- `logs/performance.log` - Performance metrics
- `logs/errors.log` - Error logs
- `logs/activity.log` - User activity logs

### Database Models
- `PerformanceLog` - Performance metrics storage
- `ErrorLog` - Error information and resolution tracking
- `UserActivityLog` - User behavior analytics
- `AIProcessingMetrics` - AI operation metrics
- `AlertLog` - System alerts and notifications
- `SystemMetrics` - General system metrics

## API Endpoints

### Dashboard APIs
- `/services/api/performance-metrics/` - Performance data
- `/services/api/error-metrics/` - Error statistics
- `/services/api/user-activity/` - User activity data
- `/services/api/ai-processing-metrics/` - AI processing stats
- `/services/api/system-health/` - System health status

## Alerting

The system automatically generates alerts for:
- High error rates
- Slow AI processing
- System performance issues
- Critical system errors

Alerts can be managed through the dashboard or Django admin interface.

## Privacy and Compliance

- User activity logging respects privacy settings
- Personal data is anonymized where possible
- Configurable data retention policies
- GDPR/COPPA compliance features

## Performance Considerations

- Asynchronous logging to minimize performance impact
- Efficient database indexing for fast queries
- Configurable log retention to manage storage
- Caching for dashboard performance

## Troubleshooting

### Common Issues

1. **High Memory Usage**: Adjust log retention settings
2. **Slow Dashboard**: Check database indexes and query optimization
3. **Missing Correlation IDs**: Ensure middleware is properly configured
4. **Alert Spam**: Adjust alert thresholds in settings

### Debug Mode
Enable debug logging by setting the log level to DEBUG in Django settings.

## Contributing

When adding new monitoring features:
1. Use the existing monitoring decorators
2. Follow the correlation ID pattern
3. Add appropriate database indexes
4. Update dashboard visualizations
5. Add tests for new functionality

## Security

- Dashboard access restricted to staff users
- Sensitive data filtering in logs
- Secure correlation ID generation
- Rate limiting on monitoring endpoints