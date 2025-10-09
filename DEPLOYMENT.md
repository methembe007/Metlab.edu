# Metlab.edu Production Deployment Guide

This guide covers the complete production deployment process for the Metlab.edu AI learning platform.

## Prerequisites

### System Requirements
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Nginx (for reverse proxy)
- Docker & Docker Compose (optional, for containerized deployment)

### Environment Setup
1. Copy `.env.production.template` to `.env.production`
2. Fill in all required environment variables
3. Ensure all secrets are properly configured

## Deployment Options

### Option 1: Docker Deployment (Recommended)

#### Quick Start
```bash
# Clone and navigate to project
git clone <repository-url>
cd metlab_edu

# Configure environment
cp .env.production.template .env.production
# Edit .env.production with your values

# Deploy with Docker Compose
docker-compose -f docker-compose.yml --env-file .env.production up -d

# Run initial setup
docker-compose exec web python scripts/migrate_database.py
```

#### Docker Services
- **web**: Main Django application with Nginx
- **db**: PostgreSQL database
- **redis**: Redis cache and message broker
- **celery**: Background task worker
- **celery-beat**: Scheduled task scheduler
- **nginx**: Load balancer (optional)

### Option 2: Traditional Deployment

#### System Setup
```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt update
sudo apt install python3.11 python3.11-venv postgresql-15 redis-server nginx

# Create application user
sudo useradd -m -s /bin/bash metlab
sudo usermod -aG www-data metlab

# Create directories
sudo mkdir -p /var/www/metlab_edu/{staticfiles,media}
sudo mkdir -p /var/log/metlab_edu
sudo chown -R metlab:www-data /var/www/metlab_edu
sudo chown -R metlab:metlab /var/log/metlab_edu
```

#### Application Setup
```bash
# Switch to application user
sudo su - metlab

# Clone repository
git clone <repository-url> /var/www/metlab_edu/app
cd /var/www/metlab_edu/app

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.production.template .env.production
# Edit .env.production with your values

# Run deployment script
bash scripts/deploy.sh
```

## Database Setup

### PostgreSQL Configuration
```sql
-- Create database and user
CREATE DATABASE metlab_edu_prod;
CREATE USER metlab_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE metlab_edu_prod TO metlab_user;
ALTER USER metlab_user CREATEDB;
```

### Initial Migration
```bash
# Run migration script
python scripts/migrate_database.py

# Or manually
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

## Web Server Configuration

### Nginx Setup
```bash
# Copy nginx configuration
sudo cp nginx.conf.template /etc/nginx/sites-available/metlab_edu
sudo ln -s /etc/nginx/sites-available/metlab_edu /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

### SSL Certificate Setup
```bash
# Using Let's Encrypt (recommended)
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Or configure custom certificates in nginx.conf
```

## Process Management

### Systemd Services (Traditional Deployment)

#### Django Application Service
Create `/etc/systemd/system/metlab-edu.service`:
```ini
[Unit]
Description=Metlab.edu Django Application
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=metlab
Group=www-data
WorkingDirectory=/var/www/metlab_edu/app
Environment=DJANGO_SETTINGS_MODULE=metlab_edu.settings_production
EnvironmentFile=/var/www/metlab_edu/app/.env.production
ExecStart=/var/www/metlab_edu/app/venv/bin/gunicorn metlab_edu.wsgi:application --bind 127.0.0.1:8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Celery Worker Service
Create `/etc/systemd/system/metlab-celery.service`:
```ini
[Unit]
Description=Metlab.edu Celery Worker
After=network.target redis.service

[Service]
Type=exec
User=metlab
Group=metlab
WorkingDirectory=/var/www/metlab_edu/app
Environment=DJANGO_SETTINGS_MODULE=metlab_edu.settings_production
EnvironmentFile=/var/www/metlab_edu/app/.env.production
ExecStart=/var/www/metlab_edu/app/venv/bin/celery -A metlab_edu worker --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Enable and Start Services
```bash
sudo systemctl daemon-reload
sudo systemctl enable metlab-edu metlab-celery
sudo systemctl start metlab-edu metlab-celery
```

## Backup and Recovery

### Automated Backups
```bash
# Create backup
bash scripts/backup_database.sh

# Schedule daily backups (crontab)
0 2 * * * /var/www/metlab_edu/app/scripts/backup_database.sh
```

### Database Restoration
```bash
# Restore from backup
bash scripts/restore_database.sh metlab_edu_backup_20231201_120000.sql.gz
```

## Monitoring and Maintenance

### Log Locations
- Application logs: `/var/log/metlab_edu/`
- Nginx logs: `/var/log/nginx/`
- System logs: `journalctl -u metlab-edu`

### Health Checks
```bash
# Application health
curl -f http://localhost/health/

# Database connectivity
python manage.py dbshell --command="SELECT 1;"

# Redis connectivity
redis-cli ping
```

### Performance Monitoring
- Monitor CPU, memory, and disk usage
- Track database query performance
- Monitor Redis memory usage
- Set up alerts for critical metrics

## Security Considerations

### Firewall Configuration
```bash
# Allow only necessary ports
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

### File Permissions
```bash
# Set proper permissions
sudo chown -R metlab:www-data /var/www/metlab_edu
sudo chmod -R 755 /var/www/metlab_edu
sudo chmod -R 644 /var/www/metlab_edu/staticfiles
```

### Regular Updates
- Keep system packages updated
- Update Python dependencies regularly
- Monitor security advisories
- Rotate secrets periodically

## Troubleshooting

### Common Issues

#### Static Files Not Loading
```bash
# Recollect static files
python manage.py collectstatic --clear --noinput
sudo systemctl restart nginx
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql
sudo -u postgres psql -c "SELECT version();"
```

#### Redis Connection Issues
```bash
# Check Redis status
sudo systemctl status redis
redis-cli ping
```

#### Application Not Starting
```bash
# Check logs
journalctl -u metlab-edu -f
tail -f /var/log/metlab_edu/django.log
```

### Performance Issues
- Check database query performance
- Monitor Redis memory usage
- Review Celery task queue
- Analyze Nginx access logs

## Scaling Considerations

### Horizontal Scaling
- Use multiple application servers behind load balancer
- Implement database read replicas
- Use Redis Cluster for cache scaling
- Consider CDN for static files

### Vertical Scaling
- Increase server resources (CPU, RAM)
- Optimize database configuration
- Tune Gunicorn worker settings
- Adjust Redis memory limits

## Maintenance Schedule

### Daily
- Monitor system health
- Check error logs
- Verify backup completion

### Weekly
- Review performance metrics
- Update security patches
- Clean up old log files

### Monthly
- Update dependencies
- Review and rotate secrets
- Perform disaster recovery tests
- Analyze usage patterns

## Support and Documentation

For additional support:
- Check application logs first
- Review Django and system documentation
- Monitor GitHub issues and updates
- Contact development team for critical issues