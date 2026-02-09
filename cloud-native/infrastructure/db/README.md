# PostgreSQL Database Infrastructure

This directory contains the PostgreSQL database infrastructure setup for the Metlab platform, including Kubernetes manifests, migration files, and connection pooling configuration.

## Overview

The database infrastructure consists of:

1. **PostgreSQL StatefulSet** - Running PostgreSQL 15 with persistent storage
2. **Connection Pooling** - Go package for managing database connections with pgx
3. **Database Migrations** - Using golang-migrate for schema versioning
4. **Initialization Scripts** - Automated schema and index creation

## Quick Start

### 1. Deploy PostgreSQL to Kubernetes

```bash
# Apply the PostgreSQL manifests
kubectl apply -f cloud-native/infrastructure/k8s/postgres.yaml

# Wait for PostgreSQL to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n metlab-dev --timeout=120s

# Check PostgreSQL status
kubectl get statefulset postgres -n metlab-dev
kubectl get pods -l app=postgres -n metlab-dev
```

### 2. Run Database Migrations

#### Option A: Using Kubernetes Job

```bash
# Run migrations as a Kubernetes Job
kubectl apply -f cloud-native/infrastructure/k8s/db-migrate-job.yaml

# Check migration job status
kubectl get jobs -n metlab-dev
kubectl logs job/db-migrate -n metlab-dev
```

#### Option B: Using Local Migration Tool

```bash
# Set database connection
export DATABASE_URL="postgres://postgres:postgres@localhost:5432/metlab?sslmode=disable"

# Port-forward to access PostgreSQL locally
kubectl port-forward svc/postgres 5432:5432 -n metlab-dev &

# Run migrations
cd cloud-native
./scripts/migrate.sh up

# Or on Windows
.\scripts\migrate.ps1 up
```

### 3. Verify Database Setup

```bash
# Connect to PostgreSQL
kubectl exec -it postgres-0 -n metlab-dev -- psql -U postgres -d metlab

# List tables
\dt

# Check migration version
SELECT * FROM schema_migrations;

# Exit
\q
```

## Database Schema

The database schema includes the following main tables:

### Authentication & Users
- `users` - Base user table for teachers and students
- `teachers` - Teacher-specific information
- `students` - Student-specific information
- `signin_codes` - Codes for student registration
- `classes` - Class information

### Content Management
- `videos` - Video metadata
- `video_variants` - Multiple resolution versions
- `video_thumbnails` - Video preview images
- `video_views` - Student viewing tracking
- `pdfs` - PDF document metadata

### Homework System
- `homework_assignments` - Assignment details
- `homework_submissions` - Student submissions
- `homework_grades` - Grading and feedback

### Collaboration
- `study_groups` - Student study groups
- `study_group_members` - Group membership
- `chat_rooms` - Chat room metadata
- `chat_messages` - Chat messages

### Analytics
- `student_logins` - Login tracking
- `pdf_downloads` - Download tracking

## Connection Pooling

The shared database package provides connection pooling using pgx/v5:

```go
import (
    "context"
    "github.com/metlab/shared/db"
)

// Create connection pool with default settings
pool, err := db.NewPoolFromURL(ctx, os.Getenv("DATABASE_URL"))
if err != nil {
    log.Fatal(err)
}
defer pool.Close()

// Or with custom configuration
cfg := &db.Config{
    Host:            "postgres",
    Port:            5432,
    User:            "postgres",
    Password:        "postgres",
    Database:        "metlab",
    SSLMode:         "disable",
    MinConns:        10,
    MaxConns:        100,
    MaxConnLifetime: time.Hour,
}

pool, err := db.NewPool(ctx, cfg)
```

### Connection Pool Settings

- **MinConns**: 10 - Minimum connections maintained
- **MaxConns**: 100 - Maximum connections allowed
- **MaxConnLifetime**: 1 hour - Maximum connection lifetime
- **MaxConnIdleTime**: 30 minutes - Maximum idle time
- **HealthCheckPeriod**: 1 minute - Health check interval

## Database Migrations

### Creating a New Migration

```bash
# Create a new migration
./scripts/migrate.sh create add_user_avatar

# This creates two files:
# - 000003_add_user_avatar.up.sql
# - 000003_add_user_avatar.down.sql
```

### Migration Best Practices

1. **Always create both up and down migrations**
2. **Keep migrations small and focused** - One logical change per migration
3. **Test migrations before production** - Run on a copy of production data
4. **Never modify existing migrations** - Create a new migration to fix issues
5. **Use transactions** - Wrap DDL statements in BEGIN/COMMIT
6. **Add indexes separately** - Create indexes in separate migrations

### Migration Commands

```bash
# Apply all pending migrations
./scripts/migrate.sh up

# Rollback last migration
./scripts/migrate.sh down

# Rollback last 3 migrations
./scripts/migrate.sh down 3

# Check current version
./scripts/migrate.sh version

# Force version (if stuck)
./scripts/migrate.sh force 2
```

## PostgreSQL Configuration

The PostgreSQL instance is configured with performance tuning:

### Memory Settings
- `shared_buffers`: 256MB
- `effective_cache_size`: 1GB
- `work_mem`: 2621kB
- `maintenance_work_mem`: 64MB

### Connection Settings
- `max_connections`: 200
- `superuser_reserved_connections`: 3

### WAL Settings
- `wal_buffers`: 16MB
- `min_wal_size`: 1GB
- `max_wal_size`: 4GB
- `checkpoint_completion_target`: 0.9

### Query Planner
- `random_page_cost`: 1.1 (optimized for SSD)
- `effective_io_concurrency`: 200
- `default_statistics_target`: 100

## Backup and Recovery

### Manual Backup

```bash
# Create backup
kubectl exec postgres-0 -n metlab-dev -- pg_dump -U postgres metlab > backup.sql

# Restore backup
kubectl exec -i postgres-0 -n metlab-dev -- psql -U postgres metlab < backup.sql
```

### Automated Backups

For production, configure automated backups:

1. Use PostgreSQL's continuous archiving (WAL archiving)
2. Schedule regular pg_dump backups
3. Store backups in object storage (S3)
4. Test restore procedures regularly

## Monitoring

### Check Database Health

```bash
# Check PostgreSQL status
kubectl exec postgres-0 -n metlab-dev -- pg_isready -U postgres

# View logs
kubectl logs postgres-0 -n metlab-dev

# Check resource usage
kubectl top pod postgres-0 -n metlab-dev
```

### Connection Pool Statistics

```go
import "github.com/metlab/shared/db"

stats := db.GetPoolStats(pool)
log.Printf("Total connections: %d", stats.TotalConns)
log.Printf("Idle connections: %d", stats.IdleConns)
log.Printf("Acquired connections: %d", stats.AcquiredConns)
```

## Troubleshooting

### Cannot Connect to Database

```bash
# Check if PostgreSQL is running
kubectl get pods -l app=postgres -n metlab-dev

# Check PostgreSQL logs
kubectl logs postgres-0 -n metlab-dev

# Verify service
kubectl get svc postgres -n metlab-dev

# Test connection
kubectl exec postgres-0 -n metlab-dev -- psql -U postgres -d metlab -c "SELECT 1"
```

### Migration Stuck

```bash
# Check current version
./scripts/migrate.sh version

# If stuck, force to correct version
./scripts/migrate.sh force <version_number>

# Then try migration again
./scripts/migrate.sh up
```

### Out of Connections

```bash
# Check active connections
kubectl exec postgres-0 -n metlab-dev -- psql -U postgres -d metlab -c "SELECT count(*) FROM pg_stat_activity"

# View connection details
kubectl exec postgres-0 -n metlab-dev -- psql -U postgres -d metlab -c "SELECT * FROM pg_stat_activity"

# Increase max_connections if needed (requires restart)
```

## Security Considerations

1. **Change default password** - Update `postgres-secret` with a strong password
2. **Enable SSL/TLS** - Configure SSL for production environments
3. **Network policies** - Restrict database access to authorized services
4. **Regular updates** - Keep PostgreSQL version up to date
5. **Audit logging** - Enable audit logging for compliance

## Production Recommendations

1. **Use managed PostgreSQL** - Consider cloud provider managed databases
2. **Enable replication** - Set up read replicas for high availability
3. **Configure backups** - Automated backups with point-in-time recovery
4. **Monitor performance** - Use tools like pgAdmin, DataDog, or Prometheus
5. **Tune for workload** - Adjust configuration based on actual usage patterns
6. **Use connection pooling** - Always use connection pooling in applications
7. **Regular maintenance** - Schedule VACUUM, ANALYZE, and REINDEX operations

## References

- [PostgreSQL Documentation](https://www.postgresql.org/docs/15/)
- [pgx Documentation](https://pkg.go.dev/github.com/jackc/pgx/v5)
- [golang-migrate Documentation](https://github.com/golang-migrate/migrate)
- [Kubernetes StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)
