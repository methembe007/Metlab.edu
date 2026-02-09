#!/bin/bash

# Database migration script using golang-migrate
# Usage: ./migrate.sh [up|down|create|version|force] [args...]

set -e

COMMAND=$1
NAME=$2
STEPS=${3:-1}

# Configuration
MIGRATIONS_PATH="cloud-native/infrastructure/db/migrations"
DATABASE_URL=${DATABASE_URL:-"postgres://postgres:postgres@localhost:5432/metlab?sslmode=disable"}

# Check if migrate is installed
if ! command -v migrate &> /dev/null; then
    echo "Error: golang-migrate is not installed"
    echo "Install it with:"
    echo "  macOS: brew install golang-migrate"
    echo "  Linux: curl -L https://github.com/golang-migrate/migrate/releases/download/v4.17.0/migrate.linux-amd64.tar.gz | tar xvz && sudo mv migrate /usr/local/bin/"
    echo "  Or: go install -tags 'postgres' github.com/golang-migrate/migrate/v4/cmd/migrate@latest"
    exit 1
fi

case $COMMAND in
    up)
        echo "Running migrations up..."
        migrate -path $MIGRATIONS_PATH -database "$DATABASE_URL" up
        echo "Migrations applied successfully!"
        ;;
    down)
        echo "Rolling back $STEPS migration(s)..."
        migrate -path $MIGRATIONS_PATH -database "$DATABASE_URL" down $STEPS
        echo "Migrations rolled back successfully!"
        ;;
    create)
        if [ -z "$NAME" ]; then
            echo "Error: Migration name required"
            echo "Usage: ./migrate.sh create <migration_name>"
            exit 1
        fi
        
        echo "Creating new migration: $NAME"
        migrate create -ext sql -dir $MIGRATIONS_PATH -seq $NAME
        echo "Migration files created successfully!"
        ;;
    version)
        echo "Checking current migration version..."
        migrate -path $MIGRATIONS_PATH -database "$DATABASE_URL" version
        ;;
    force)
        if [ -z "$NAME" ]; then
            echo "Error: Version number required"
            echo "Usage: ./migrate.sh force <version_number>"
            exit 1
        fi
        
        echo "Forcing migration version to $NAME..."
        migrate -path $MIGRATIONS_PATH -database "$DATABASE_URL" force $NAME
        echo "Migration version forced successfully!"
        ;;
    *)
        echo "Usage: ./migrate.sh {up|down|create|version|force} [args...]"
        echo ""
        echo "Commands:"
        echo "  up                    - Apply all pending migrations"
        echo "  down [steps]          - Rollback migrations (default: 1)"
        echo "  create <name>         - Create a new migration"
        echo "  version               - Show current migration version"
        echo "  force <version>       - Force set migration version"
        echo ""
        echo "Environment variables:"
        echo "  DATABASE_URL          - PostgreSQL connection string"
        echo "                          (default: postgres://postgres:postgres@localhost:5432/metlab?sslmode=disable)"
        exit 1
        ;;
esac
