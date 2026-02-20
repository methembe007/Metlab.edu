# PDF Service

The PDF Service handles PDF document uploads, storage, and download URL generation for the Metlab.edu platform.

## Features

- **PDF Upload**: Stream-based PDF file uploads with validation
- **PDF Listing**: Retrieve PDFs by class with download tracking
- **Download URLs**: Generate signed, time-limited download URLs
- **Download Tracking**: Track which students have downloaded PDFs for analytics

## Architecture

The service follows a clean architecture pattern:

```
cmd/
  server/          # Application entry point
internal/
  config/          # Configuration management
  handler/         # gRPC handlers
  models/          # Domain models
  repository/      # Database operations
migrations/        # Database migrations
```

## Requirements

- Go 1.21+
- PostgreSQL 15+
- MinIO or S3-compatible storage
- Protocol Buffers compiler (for proto generation)

## Configuration

Configuration is loaded from environment variables. See `.env.example` for all available options.

Key configurations:
- `PORT`: gRPC server port (default: 50056)
- `DATABASE_URL`: PostgreSQL connection string
- `S3_ENDPOINT`: S3-compatible storage endpoint
- `S3_BUCKET`: Bucket name for PDF storage (default: metlab-pdfs)
- `MAX_UPLOAD_SIZE`: Maximum PDF file size in bytes (default: 50MB)

## Running Locally

1. Copy `.env.example` to `.env` and configure:
   ```bash
   cp .env.example .env
   ```

2. Ensure PostgreSQL and MinIO are running

3. Run database migrations:
   ```bash
   cd ../../infrastructure/db
   ./migrate.sh up
   ```

4. Start the service:
   ```bash
   make run
   ```

## Building

Build the binary:
```bash
make build
```

Build Docker image:
```bash
make docker-build
```

## API

The service implements the following gRPC methods defined in `proto/pdf/pdf.proto`:

### UploadPDF
Streams a PDF file to storage and creates a database record.

**Request**: Stream of `UploadPDFRequest` (metadata + chunks)
**Response**: `UploadPDFResponse` with PDF ID

### ListPDFs
Lists all PDFs for a specific class.

**Request**: `ListPDFsRequest` with class_id and optional user_id
**Response**: `ListPDFsResponse` with array of PDFs

### GetDownloadURL
Generates a signed download URL valid for 1 hour.

**Request**: `GetDownloadURLRequest` with pdf_id and user_id
**Response**: `DownloadURLResponse` with URL and expiration time

## Database Schema

The service uses the following tables:

- `pdfs`: PDF metadata and storage information
- `pdf_downloads`: Download tracking for analytics

See `migrations/001_pdf_tables.up.sql` for the complete schema.

## Storage

PDFs are stored in S3-compatible storage with the following path structure:
```
pdfs/{class_id}/{teacher_id}/{timestamp}_{filename}
```

## Error Handling

The service returns standard gRPC status codes:
- `INVALID_ARGUMENT`: Invalid request parameters
- `NOT_FOUND`: PDF not found
- `INTERNAL`: Server errors

## Health Checks

The service implements gRPC health checks on the same port as the main service.

## Development

Run with hot reload (requires [air](https://github.com/cosmtrek/air)):
```bash
make dev
```

Format code:
```bash
make fmt
```

Run tests:
```bash
make test
```

## Deployment

The service is deployed to Kubernetes. See `k8s/deployment.yaml` for the deployment configuration.

## Monitoring

The service logs structured JSON logs with the following fields:
- `timestamp`: ISO 8601 timestamp
- `level`: Log level (DEBUG, INFO, WARN, ERROR)
- `service`: Always "pdf-service"
- `message`: Log message
- Additional context fields

## Requirements Mapping

This service implements the following requirements:
- 5.1: PDF upload acceptance
- 5.2: PDF storage and class association
- 5.3: Secure download URL generation
- 5.4: Download button functionality (via API)
- 5.5: Download event logging
- 11.1: PDF list display
- 11.2: Download functionality
- 11.3: File size display
- 11.4: Unlimited downloads
- 11.5: Download tracking
