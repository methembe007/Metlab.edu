# Homework Service

The Homework Service manages homework assignments, submissions, and grading for the Metlab.edu platform.

## Features

- **Assignment Management**: Create and manage homework assignments with due dates and max scores
- **Submission Handling**: Accept homework submissions with file uploads up to 25MB
- **Late Detection**: Automatically detect and flag late submissions
- **Grading**: Grade submissions with scores and feedback
- **File Storage**: Store submission files in S3-compatible object storage
- **File Download**: Stream submission files for teacher review

## Architecture

The service follows a clean architecture pattern:

```
homework/
├── cmd/
│   └── server/          # Application entry point
├── internal/
│   ├── config/          # Configuration management
│   ├── handler/         # gRPC service handlers
│   ├── models/          # Domain models
│   └── repository/      # Database access layer
├── migrations/          # Database migrations
└── k8s/                # Kubernetes manifests
```

## Database Schema

The service uses three main tables:

- **homework_assignments**: Stores assignment details
- **homework_submissions**: Stores student submissions
- **homework_grades**: Stores grades and feedback

See `migrations/001_homework_tables.up.sql` for the complete schema.

## gRPC Service Interface

The service implements the following RPC methods:

- `CreateAssignment`: Create a new homework assignment
- `ListAssignments`: List assignments for a class or teacher
- `SubmitHomework`: Submit homework with file upload (streaming)
- `ListSubmissions`: List submissions for an assignment
- `GradeSubmission`: Grade a submission with score and feedback
- `GetSubmissionFile`: Download a submission file (streaming)

See `proto/homework/homework.proto` for the complete API definition.

## Configuration

Configuration is loaded from environment variables. See `.env.example` for all available options.

Key configuration:

- `PORT`: gRPC server port (default: 50053)
- `DATABASE_URL`: PostgreSQL connection string
- `S3_ENDPOINT`: S3-compatible storage endpoint
- `MAX_UPLOAD_SIZE`: Maximum file upload size in bytes (default: 25MB)

## Running Locally

### Prerequisites

- Go 1.21+
- PostgreSQL 15+
- MinIO or S3-compatible storage
- Protocol Buffers compiler

### Setup

1. Copy environment file:
   ```bash
   cp .env.example .env
   ```

2. Update `.env` with your configuration

3. Run database migrations:
   ```bash
   make migrate-up
   ```

4. Run the service:
   ```bash
   make run
   ```

## Development

### Building

```bash
make build
```

### Running Tests

```bash
make test
```

### Generating Protobuf Code

```bash
make proto
```

### Docker

Build Docker image:
```bash
make docker-build
```

Run Docker container:
```bash
make docker-run
```

## Deployment

### Kubernetes

Deploy to Kubernetes:

```bash
kubectl apply -f k8s/deployment.yaml
```

The service will be available at `homework-service:50053` within the cluster.

### Health Checks

The service implements gRPC health checks:

```bash
grpc_health_probe -addr=localhost:50053
```

## API Examples

### Create Assignment

```go
req := &pb.CreateAssignmentRequest{
    TeacherId:   "teacher-uuid",
    ClassId:     "class-uuid",
    Title:       "Math Homework 1",
    Description: "Complete exercises 1-10",
    DueDate:     time.Now().Add(7 * 24 * time.Hour).Unix(),
    MaxScore:    100,
}

resp, err := client.CreateAssignment(ctx, req)
```

### Submit Homework

```go
stream, err := client.SubmitHomework(ctx)

// Send metadata
metadata := &pb.SubmissionMetadata{
    AssignmentId: "assignment-uuid",
    StudentId:    "student-uuid",
    Filename:     "homework.pdf",
    FileSize:     fileSize,
}
stream.Send(&pb.SubmitHomeworkRequest{
    Data: &pb.SubmitHomeworkRequest_Metadata{Metadata: metadata},
})

// Send file chunks
buffer := make([]byte, 64*1024)
for {
    n, err := file.Read(buffer)
    if err == io.EOF {
        break
    }
    stream.Send(&pb.SubmitHomeworkRequest{
        Data: &pb.SubmitHomeworkRequest_Chunk{Chunk: buffer[:n]},
    })
}

resp, err := stream.CloseAndRecv()
```

### Grade Submission

```go
req := &pb.GradeSubmissionRequest{
    SubmissionId: "submission-uuid",
    TeacherId:    "teacher-uuid",
    Score:        85,
    Feedback:     "Good work! Check problem 5.",
}

resp, err := client.GradeSubmission(ctx, req)
```

## Monitoring

The service exposes metrics for:

- Request count and latency
- File upload/download metrics
- Database query performance
- Storage operations

## Error Handling

The service uses standard gRPC status codes:

- `INVALID_ARGUMENT`: Invalid input data
- `NOT_FOUND`: Resource not found
- `INTERNAL`: Server error
- `RESOURCE_EXHAUSTED`: File size limit exceeded

## Security

- File uploads are validated for size and type
- All database queries use prepared statements
- JWT tokens are validated for authentication
- Teacher permissions are verified for grading operations

## Contributing

1. Follow the existing code structure
2. Add tests for new features
3. Update documentation
4. Run linter before committing: `make lint`

## License

Copyright © 2026 Metlab.edu
