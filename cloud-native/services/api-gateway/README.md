# API Gateway Service

The API Gateway is the single entry point for all client requests to the Metlab backend services. It handles HTTP-to-gRPC translation, authentication, rate limiting, and request routing.

## Features

- **HTTP to gRPC Translation**: Converts REST API calls to gRPC service calls
- **Service Discovery**: Maintains connections to all backend microservices
- **CORS Configuration**: Handles cross-origin requests from the frontend
- **Request Logging**: Logs all incoming requests with timing information
- **Error Handling**: Standardized error responses across all endpoints
- **Health Checks**: Provides health and readiness endpoints for Kubernetes

## Architecture

```
HTTP Request → API Gateway → gRPC Service
                    ↓
            [Middleware Chain]
            - Request ID
            - Logging
            - CORS
            - Authentication (TODO)
            - Rate Limiting (TODO)
```

## Project Structure

```
api-gateway/
├── cmd/
│   └── server/
│       └── main.go              # Application entry point
├── internal/
│   ├── config/
│   │   └── config.go            # Configuration management
│   ├── grpc/
│   │   └── clients.go           # gRPC client connections
│   ├── handlers/
│   │   ├── handlers.go          # Handler base
│   │   └── health.go            # Health check handlers
│   ├── middleware/
│   │   ├── cors.go              # CORS middleware
│   │   ├── logging.go           # Request logging
│   │   └── request_id.go        # Request ID tracking
│   ├── router/
│   │   └── router.go            # Route definitions
│   └── transformers/
│       └── transformers.go      # HTTP/gRPC transformers
├── Dockerfile                    # Container image definition
├── go.mod                        # Go module definition
└── README.md                     # This file
```

## Configuration

The API Gateway is configured via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | HTTP server port | `8080` |
| `AUTH_SERVICE_ADDR` | Auth service gRPC address | `localhost:50051` |
| `VIDEO_SERVICE_ADDR` | Video service gRPC address | `localhost:50052` |
| `HOMEWORK_SERVICE_ADDR` | Homework service gRPC address | `localhost:50053` |
| `ANALYTICS_SERVICE_ADDR` | Analytics service gRPC address | `localhost:50054` |
| `COLLABORATION_SERVICE_ADDR` | Collaboration service gRPC address | `localhost:50055` |
| `PDF_SERVICE_ADDR` | PDF service gRPC address | `localhost:50056` |
| `ALLOWED_ORIGINS` | Comma-separated list of allowed CORS origins | `http://localhost:3000,http://localhost:5173` |

## Running Locally

### Prerequisites

- Go 1.21 or higher
- Access to backend gRPC services (or they can be unavailable for development)

### Steps

1. Navigate to the api-gateway directory:
   ```bash
   cd cloud-native/services/api-gateway
   ```

2. Install dependencies:
   ```bash
   go mod download
   ```

3. Run the service:
   ```bash
   go run cmd/server/main.go
   ```

4. The API Gateway will start on port 8080 (or the port specified in the `PORT` environment variable)

### Testing

Test the health endpoint:
```bash
curl http://localhost:8080/health
```

Expected response:
```json
{
  "status": "healthy",
  "message": "API Gateway is running"
}
```

## API Endpoints

### Health Checks

- `GET /health` - Health check endpoint
- `GET /ready` - Readiness check endpoint

### API Routes

All API routes are prefixed with `/api`:

- `GET /api/` - API information

#### Authentication (TODO)
- `POST /api/auth/teacher/signup` - Teacher registration
- `POST /api/auth/teacher/login` - Teacher login
- `POST /api/auth/student/signin` - Student signin
- `POST /api/auth/codes/generate` - Generate signin code

#### Videos (TODO)
- `GET /api/videos` - List videos
- `POST /api/videos` - Upload video
- `GET /api/videos/:id` - Get video details
- `GET /api/videos/:id/stream` - Get streaming URL
- `POST /api/videos/:id/view` - Record video view
- `GET /api/videos/:id/analytics` - Get video analytics

#### Homework (TODO)
- `POST /api/homework/assignments` - Create assignment
- `GET /api/homework/assignments` - List assignments
- `POST /api/homework/submissions` - Submit homework
- `GET /api/homework/submissions` - List submissions
- `POST /api/homework/submissions/:id/grade` - Grade submission
- `GET /api/homework/submissions/:id/file` - Download submission

#### PDFs (TODO)
- `POST /api/pdfs` - Upload PDF
- `GET /api/pdfs` - List PDFs
- `GET /api/pdfs/:id/download` - Get download URL

#### Analytics (TODO)
- `GET /api/analytics/login-stats` - Get login statistics
- `GET /api/analytics/class-engagement` - Get class engagement

#### Study Groups (TODO)
- `POST /api/study-groups` - Create study group
- `GET /api/study-groups` - List study groups
- `POST /api/study-groups/:id/join` - Join study group

#### Chat (TODO)
- `POST /api/chat/rooms` - Create chat room
- `GET /api/chat/rooms` - List chat rooms
- `POST /api/chat/rooms/:id/messages` - Send message
- `GET /api/chat/rooms/:id/messages` - Get messages

## Docker

Build the Docker image:
```bash
docker build -t metlab/api-gateway:latest .
```

Run the container:
```bash
docker run -p 8080:8080 \
  -e AUTH_SERVICE_ADDR=auth-service:50051 \
  -e VIDEO_SERVICE_ADDR=video-service:50052 \
  metlab/api-gateway:latest
```

## Kubernetes Deployment

The API Gateway is deployed to Kubernetes using the manifests in `infrastructure/k8s/api-gateway/`.

Deploy to Kubernetes:
```bash
kubectl apply -f infrastructure/k8s/api-gateway/
```

## Development

### Adding New Endpoints

1. Create a handler in `internal/handlers/`
2. Add the route in `internal/router/router.go`
3. Implement HTTP to gRPC transformation in the handler
4. Update this README with the new endpoint

### Middleware

The middleware chain is defined in `internal/router/router.go`. Current middleware:

1. Request ID - Adds unique ID to each request
2. Logging - Logs request details
3. Recoverer - Recovers from panics
4. CORS - Handles cross-origin requests

To add new middleware, create it in `internal/middleware/` and add it to the router.

## Next Steps

- [ ] Implement authentication middleware (Task 16)
- [ ] Implement rate limiting middleware (Task 17)
- [ ] Implement auth endpoint handlers (Task 18)
- [ ] Implement video endpoint handlers (Task 19)
- [ ] Implement homework endpoint handlers (Task 20)
- [ ] Implement remaining endpoint handlers (Task 21)

## Troubleshooting

### gRPC Connection Errors

If you see errors connecting to backend services:
- Ensure the services are running
- Check the service addresses in environment variables
- Verify network connectivity between services

### CORS Errors

If you see CORS errors in the browser:
- Check the `ALLOWED_ORIGINS` environment variable
- Ensure the frontend origin is included in the allowed origins list
- Verify the CORS middleware is properly configured

## License

Copyright © 2024 Metlab.edu
