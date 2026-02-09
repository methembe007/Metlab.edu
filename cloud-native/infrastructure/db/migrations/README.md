# Database Migrations

This directory contains database migration files for the Metlab platform.

## Migration Tool

We use [golang-migrate](https://github.com/golang-migrate/migrate) for database migrations.

### Installation

```bash
# macOS
brew install golang-migrate

# Linux
curl -L https://github.com/golang-migrate/migrate/releases/download/v4.17.0/migrate.linux-amd64.tar.gz | tar xvz
sudo mv migrate /usr/local/bin/

# Windows
scoop install migrate

# Or using Go
go install -tags 'postgres' github.com/golang-migrate/migrate/v4/cmd/migrate@latest
```

### Usage

#### Create a new migration

```bash
migrate create -ext sql -dir cloud-native/infrastructure/db/migrations -seq <migration_name>
```

#### Run migrations

```bash
# Up (apply all pending migrations)
migrate -path cloud-native/infrastructure/db/migrations -database "postgres://postgres:postgres@localhost:5432/metlab?sslmode=disable" up

# Down (rollback last migration)
migrate -path cloud-native/infrastructure/db/migrations -database "postgres://postgres:postgres@localhost:5432/metlab?sslmode=disable" down 1

# Force version (if migrations are stuck)
migrate -path cloud-native/infrastructure/db/migrations -database "postgres://postgres:postgres@localhost:5432/metlab?sslmode=disable" force <version>

# Check current version
migrate -path cloud-native/infrastructure/db/migrations -database "postgres://postgres:postgres@localhost:5432/metlab?sslmode=disable" version
```

#### Using environment variables

```bash
export DATABASE_URL="postgres://postgres:postgres@localhost:5432/metlab?sslmode=disable"
export MIGRATIONS_PATH="cloud-native/infrastructure/db/migrations"

migrate -path $MIGRATIONS_PATH -database $DATABASE_URL up
```

### Migration Files

Migration files are named with the following pattern:
- `<version>_<description>.up.sql` - Applied when migrating up
- `<version>_<description>.down.sql` - Applied when migrating down

Example:
- `000001_initial_schema.up.sql`
- `000001_initial_schema.down.sql`

### Best Practices

1. **Always create both up and down migrations** - This allows for rollbacks
2. **Keep migrations small and focused** - One logical change per migration
3. **Test migrations before applying to production** - Run on a copy of production data
4. **Never modify existing migrations** - Create a new migration to fix issues
5. **Use transactions** - Wrap DDL statements in transactions when possible
6. **Add indexes separately** - Create indexes in separate migrations to avoid long locks

### Migration Workflow

1. Create migration: `migrate create -ext sql -dir cloud-native/infrastructure/db/migrations -seq add_user_avatar`
2. Edit the generated `.up.sql` and `.down.sql` files
3. Test locally: `migrate -path cloud-native/infrastructure/db/migrations -database $DATABASE_URL up`
4. Commit the migration files
5. Apply to staging/production through CI/CD pipeline

### Kubernetes Integration

Migrations can be run as Kubernetes Jobs before deploying services:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migrate
spec:
  template:
    spec:
      containers:
      - name: migrate
        image: migrate/migrate
        args:
          - "-path=/migrations"
          - "-database=$(DATABASE_URL)"
          - "up"
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: DATABASE_URL
        volumeMounts:
        - name: migrations
          mountPath: /migrations
      volumes:
      - name: migrations
        configMap:
          name: db-migrations
      restartPolicy: OnFailure
```
