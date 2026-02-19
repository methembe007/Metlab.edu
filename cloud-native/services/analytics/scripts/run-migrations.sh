#!/bin/bash

# Script to run database migrations for analytics service

set -e

# Load environment variables if .env file exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Construct database URL
DATABASE_URL="postgres://${DATABASE_USER}:${DATABASE_PASSWORD}@${DATABASE_HOST}:${DATABASE_PORT}/${DATABASE_NAME}?sslmode=disable"

echo "Running migrations for analytics service..."
echo "Database: ${DATABASE_HOST}:${DATABASE_PORT}/${DATABASE_NAME}"

# Check if migrate tool is installed
if ! command -v migrate &> /dev/null; then
    echo "Error: migrate tool is not installed"
    echo "Install it with: go install -tags 'postgres' github.com/golang-migrate/migrate/v4/cmd/migrate@latest"
    exit 1
fi

# Run migrations
migrate -path migrations -database "${DATABASE_URL}" up

echo "Migrations completed successfully!"
