#!/bin/bash

# Production deployment script for Metlab.edu
# This script handles the complete deployment process

set -e

# Configuration
DEPLOY_ENV="${DEPLOY_ENV:-production}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_BEFORE_DEPLOY="${BACKUP_BEFORE_DEPLOY:-true}"
RUN_MIGRATIONS="${RUN_MIGRATIONS:-true}"
RESTART_SERVICES="${RESTART_SERVICES:-true}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    log "Checking deployment prerequisites..."
    
    # Check if environment file exists
    if [ ! -f "$PROJECT_ROOT/.env.production" ]; then
        error "Production environment file not found: .env.production"
        echo "Please copy .env.production.template to .env.production and configure it"
        exit 1
    fi
    
    # Check if Docker is available (if using Docker deployment)
    if command -v docker &> /dev/null; then
        success "Docker is available"
    else
        warning "Docker not found - assuming non-containerized deployment"
    fi
    
    # Check if required directories exist
    mkdir -p "$PROJECT_ROOT/logs"
    mkdir -p "$PROJECT_ROOT/backups"
    mkdir -p "$PROJECT_ROOT/staticfiles"
    mkdir -p "$PROJECT_ROOT/media"
    
    success "Prerequisites check completed"
}

# Function to create backup
create_backup() {
    if [ "$BACKUP_BEFORE_DEPLOY" = "true" ]; then
        log "Creating pre-deployment backup..."
        if [ -f "$PROJECT_ROOT/scripts/backup_database.sh" ]; then
            bash "$PROJECT_ROOT/scripts/backup_database.sh"
            success "Backup created successfully"
        else
            warning "Backup script not found, skipping backup"
        fi
    else
        log "Skipping backup (BACKUP_BEFORE_DEPLOY=false)"
    fi
}

# Function to deploy with Docker
deploy_docker() {
    log "Starting Docker deployment..."
    
    cd "$PROJECT_ROOT"
    
    # Build and start services
    docker-compose -f docker-compose.yml --env-file .env.production build
    docker-compose -f docker-compose.yml --env-file .env.production up -d
    
    # Wait for services to be healthy
    log "Waiting for services to be healthy..."
    sleep 30
    
    # Run migrations if needed
    if [ "$RUN_MIGRATIONS" = "true" ]; then
        log "Running database migrations..."
        docker-compose -f docker-compose.yml --env-file .env.production exec web python manage.py migrate
        docker-compose -f docker-compose.yml --env-file .env.production exec web python manage.py collectstatic --noinput
    fi
    
    success "Docker deployment completed"
}

# Function to deploy without Docker
deploy_traditional() {
    log "Starting traditional deployment..."
    
    cd "$PROJECT_ROOT"
    
    # Set environment
    export DJANGO_SETTINGS_MODULE=metlab_edu.settings_production
    
    # Install/update dependencies
    log "Installing Python dependencies..."
    pip install -r requirements.txt
    
    # Run migrations if needed
    if [ "$RUN_MIGRATIONS" = "true" ]; then
        log "Running database migrations..."
        python scripts/migrate_database.py
    fi
    
    # Collect static files
    log "Collecting static files..."
    python scripts/collect_static.py
    
    success "Traditional deployment completed"
}

# Function to restart services
restart_services() {
    if [ "$RESTART_SERVICES" = "true" ]; then
        log "Restarting services..."
        
        if command -v docker-compose &> /dev/null && [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then
            # Docker deployment
            docker-compose -f docker-compose.yml --env-file .env.production restart
        else
            # Traditional deployment - restart systemd services if they exist
            services=("metlab-edu" "nginx" "redis" "postgresql")
            for service in "${services[@]}"; do
                if systemctl is-active --quiet "$service" 2>/dev/null; then
                    log "Restarting $service..."
                    sudo systemctl restart "$service"
                fi
            done
        fi
        
        success "Services restarted"
    else
        log "Skipping service restart (RESTART_SERVICES=false)"
    fi
}

# Function to run health checks
health_check() {
    log "Running post-deployment health checks..."
    
    # Wait a moment for services to stabilize
    sleep 10
    
    # Check if the application is responding
    if command -v curl &> /dev/null; then
        if curl -f -s http://localhost/health/ > /dev/null; then
            success "Application health check passed"
        else
            error "Application health check failed"
            return 1
        fi
    else
        warning "curl not available, skipping HTTP health check"
    fi
    
    # Check database connectivity
    if python manage.py dbshell --command="SELECT 1;" &> /dev/null; then
        success "Database connectivity check passed"
    else
        error "Database connectivity check failed"
        return 1
    fi
    
    # Check Redis connectivity
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping | grep -q PONG; then
            success "Redis connectivity check passed"
        else
            warning "Redis connectivity check failed"
        fi
    fi
    
    success "Health checks completed"
}

# Function to display deployment summary
deployment_summary() {
    log "Deployment Summary"
    echo "=================="
    echo "Environment: $DEPLOY_ENV"
    echo "Project Root: $PROJECT_ROOT"
    echo "Timestamp: $(date)"
    echo "Backup Created: $BACKUP_BEFORE_DEPLOY"
    echo "Migrations Run: $RUN_MIGRATIONS"
    echo "Services Restarted: $RESTART_SERVICES"
    echo ""
    echo "Next steps:"
    echo "1. Monitor application logs for any issues"
    echo "2. Test critical functionality"
    echo "3. Verify data integrity"
    echo "4. Update monitoring dashboards"
    echo ""
    echo "Useful commands:"
    echo "- View logs: tail -f logs/django.log"
    echo "- Check status: docker-compose ps (if using Docker)"
    echo "- Run management commands: python manage.py <command>"
}

# Main deployment function
main() {
    log "Starting Metlab.edu deployment process..."
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --no-backup)
                BACKUP_BEFORE_DEPLOY=false
                shift
                ;;
            --no-migrations)
                RUN_MIGRATIONS=false
                shift
                ;;
            --no-restart)
                RESTART_SERVICES=false
                shift
                ;;
            --docker)
                DEPLOYMENT_TYPE="docker"
                shift
                ;;
            --traditional)
                DEPLOYMENT_TYPE="traditional"
                shift
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --no-backup      Skip database backup"
                echo "  --no-migrations  Skip database migrations"
                echo "  --no-restart     Skip service restart"
                echo "  --docker         Force Docker deployment"
                echo "  --traditional    Force traditional deployment"
                echo "  -h, --help       Show this help message"
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Run deployment steps
    check_prerequisites
    create_backup
    
    # Determine deployment type
    if [ -z "$DEPLOYMENT_TYPE" ]; then
        if [ -f "$PROJECT_ROOT/docker-compose.yml" ] && command -v docker-compose &> /dev/null; then
            DEPLOYMENT_TYPE="docker"
        else
            DEPLOYMENT_TYPE="traditional"
        fi
    fi
    
    # Deploy based on type
    case $DEPLOYMENT_TYPE in
        docker)
            deploy_docker
            ;;
        traditional)
            deploy_traditional
            ;;
        *)
            error "Unknown deployment type: $DEPLOYMENT_TYPE"
            exit 1
            ;;
    esac
    
    restart_services
    health_check
    deployment_summary
    
    success "Deployment completed successfully!"
}

# Run main function
main "$@"