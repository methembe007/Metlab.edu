# PowerShell script for running database migrations
# Usage: .\migrate.ps1 [up|down|create|version] [args...]

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("up", "down", "create", "version", "force")]
    [string]$Command,
    
    [Parameter(Mandatory=$false)]
    [string]$Name,
    
    [Parameter(Mandatory=$false)]
    [int]$Steps = 1,
    
    [Parameter(Mandatory=$false)]
    [int]$Version
)

# Configuration
$MIGRATIONS_PATH = "cloud-native/infrastructure/db/migrations"
$DATABASE_URL = $env:DATABASE_URL

if (-not $DATABASE_URL) {
    $DATABASE_URL = "postgres://postgres:postgres@localhost:5432/metlab?sslmode=disable"
    Write-Host "Using default DATABASE_URL: $DATABASE_URL" -ForegroundColor Yellow
}

# Check if migrate is installed
$migrateInstalled = Get-Command migrate -ErrorAction SilentlyContinue
if (-not $migrateInstalled) {
    Write-Host "Error: golang-migrate is not installed" -ForegroundColor Red
    Write-Host "Install it with: scoop install migrate" -ForegroundColor Yellow
    Write-Host "Or download from: https://github.com/golang-migrate/migrate/releases" -ForegroundColor Yellow
    exit 1
}

# Execute migration command
switch ($Command) {
    "up" {
        Write-Host "Running migrations up..." -ForegroundColor Green
        migrate -path $MIGRATIONS_PATH -database $DATABASE_URL up
    }
    "down" {
        Write-Host "Rolling back $Steps migration(s)..." -ForegroundColor Yellow
        migrate -path $MIGRATIONS_PATH -database $DATABASE_URL down $Steps
    }
    "create" {
        if (-not $Name) {
            Write-Host "Error: Migration name is required for create command" -ForegroundColor Red
            Write-Host "Usage: .\migrate.ps1 create -Name <migration_name>" -ForegroundColor Yellow
            exit 1
        }
        Write-Host "Creating new migration: $Name" -ForegroundColor Green
        migrate create -ext sql -dir $MIGRATIONS_PATH -seq $Name
    }
    "version" {
        Write-Host "Checking current migration version..." -ForegroundColor Green
        migrate -path $MIGRATIONS_PATH -database $DATABASE_URL version
    }
    "force" {
        if (-not $Version) {
            Write-Host "Error: Version is required for force command" -ForegroundColor Red
            Write-Host "Usage: .\migrate.ps1 force -Version <version_number>" -ForegroundColor Yellow
            exit 1
        }
        Write-Host "Forcing migration version to $Version..." -ForegroundColor Yellow
        migrate -path $MIGRATIONS_PATH -database $DATABASE_URL force $Version
    }
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "Migration command completed successfully!" -ForegroundColor Green
} else {
    Write-Host "Migration command failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}
