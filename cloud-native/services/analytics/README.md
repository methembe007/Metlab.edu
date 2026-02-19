# Analytics Service

The Analytics Service is responsible for tracking and reporting user activity and engagement metrics in the Metlab.edu platform.

## Features

- **Login Tracking**: Records student login events with IP address and user agent
- **Student Login Statistics**: Provides daily login counts, total logins, and weekly averages
- **Class Engagement Metrics**: Aggregates engagement data including video views, homework submissions, and chat activity
- **PDF Download Tracking**: Records PDF download events for analytics

## Architecture

The service follows a clean architecture pattern with the following layers:

- **Handler Layer** (`internal/handler`): gRPC request handlers
- **Service Layer** (`internal/service`): Business logic
- **Repository Layer** (`internal/repository`): Database operations
- **Models** (`internal/models`): Data structures
- **Config** (`internal/config`): Configuration management
- **DB** (`internal/db`): Database connection management

## Database Schema

### student_logins
Tracks student login events for analytics.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| student_id | UUID | Reference to student |
| login_at | TIMESTAMP | Login timestamp |
| ip_address | INET | IP address of login |
| user_agent | TEXT | Browser user agent |

### pdf_downloads
Tracks PDF download events for analytics.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| pdf_id | UUID | Reference to PDF |
| student_id | UUID | Reference to student |
| downloaded_at | TIMESTAMP | Download timestamp |

## gRPC Service Methods

### RecordLogin
Records a student login event.

**Request:**
- `student_id` (string): Student UUID
- `ip_address` (string): IP address
- `user_agent` (string): User agent string

**Response:**
- `success` (bool): Operation success status

### GetStudentLoginStats
Retrieves login statistics for a student.

**Request:**
- `student_id` (string): Student UUID
- `days` (int32): Number of days to query (default: 30)

**Response:**
- `daily_counts` (array): Daily login counts
- `total_logins` (int32): Total login count
- `average_per_week` (float64): Average logins per week

### GetClassEngagement
Retrieves engagement metrics for all students in a class.

**Request:**
- `class_id` (string): Class UUID
- `teacher_id` (string): Teacher UUID

**Response:**
- `students` (array): Student engagement data
- `class_stats` (object): Aggregated class statistics

### RecordPDFDownload
Records a PDF download event.

**Request:**
- `pdf_id` (string): PDF UUID
- `student_id` (string): Student UUID

**Response:**
- `success` (bool): Operation success status

## Configuration

Configuration is loaded from environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| PORT | 50054 | gRPC server port |
| DATABASE_HOST | localhost | PostgreSQL host |
| DATABASE_PORT | 5432 | PostgreSQL port |
| DATABASE_USER | postgres | Database user |
| DATABASE_PASSWORD | postgres | Database password |
| DATABASE_NAME | metlab | Database name |
| ENV | development | Environment (development/production) |

## Development

### Prerequisites

- Go 1.21 or higher
- PostgreSQL 15 or higher
- golang-migrate (for database migrations)

### Setup

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Update the `.env` file with your configuration.

3. Install dependencies:
```bash
make deps
```

4. Run database migrations:
```bash
make migrate-up
```

5. Run the service:
```bash
make run
```

### Building

Build the binary:
```bash
make build
```

Build Docker image:
```bash
make docker-build
```

### Testing

Run tests:
```bash
make test
```

### Database Migrations

Run migrations up:
```bash
make migrate-up
```

Run migrations down:
```bash
make migrate-down
```

## Deployment

### Docker

Build and run with Docker:
```bash
make docker-build
make docker-run
```

### Kubernetes

Deploy to Kubernetes:
```bash
kubectl apply -f k8s/deployment.yaml
```

## Requirements Mapping

This service implements the following requirements from the design document:

- **Requirement 12.1**: Display login activity graph
- **Requirement 12.2**: Record login events with timestamp
- **Requirement 12.3**: Show total login count and weekly average
- **Requirement 12.4**: Update graph data within 5 minutes
- **Requirement 12.5**: Toggle between daily, weekly, and monthly views

## Health Checks

The service exposes a gRPC health check endpoint that can be queried using:

```bash
grpc_health_probe -addr=localhost:50054
```

## Monitoring

The service is designed to integrate with:
- Prometheus for metrics collection
- Grafana for visualization
- ELK stack for log aggregation
- Jaeger for distributed tracing

## Future Enhancements

- Real-time analytics using Redis Pub/Sub
- Advanced engagement scoring algorithms
- Predictive analytics for student performance
- Export functionality for analytics reports
