# Multi-stage Dockerfile for Metlab.edu production deployment

# Build stage for static assets
FROM node:18-alpine AS static-builder

WORKDIR /app

# Copy package files for TailwindCSS build (if you have them)
# COPY package*.json ./
# RUN npm ci --only=production

# Copy static source files
COPY static/ ./static/
COPY templates/ ./templates/

# Build TailwindCSS (uncomment if using npm build process)
# RUN npm run build

# Python base image
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    redis-tools \
    nginx \
    supervisor \
    curl \
    wget \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r metlab && useradd -r -g metlab metlab

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM base as production

# Copy application code
COPY . .

# Copy static files from builder stage
COPY --from=static-builder /app/static ./static

# Create necessary directories
RUN mkdir -p /var/log/metlab_edu \
    /var/www/metlab_edu/staticfiles \
    /var/www/metlab_edu/media \
    /app/logs

# Set ownership and permissions
RUN chown -R metlab:metlab /app \
    /var/log/metlab_edu \
    /var/www/metlab_edu \
    && chmod +x /app/scripts/*.py \
    && chmod +x /app/scripts/*.sh

# Copy configuration files
COPY docker/nginx.conf /etc/nginx/sites-available/metlab_edu
COPY docker/supervisord.conf /etc/supervisor/conf.d/metlab_edu.conf

# Enable nginx site
RUN ln -sf /etc/nginx/sites-available/metlab_edu /etc/nginx/sites-enabled/ \
    && rm -f /etc/nginx/sites-enabled/default

# Collect static files
RUN python scripts/collect_static.py

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health/ || exit 1

# Expose ports
EXPOSE 80 443

# Switch to non-root user
USER metlab

# Start supervisor to manage all services
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/metlab_edu.conf"]