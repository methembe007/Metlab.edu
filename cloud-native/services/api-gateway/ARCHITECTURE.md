# API Gateway Architecture

## Request Flow

```
┌─────────────┐
│   Client    │
│  (Browser)  │
└──────┬──────┘
       │ HTTP Request
       ▼
┌─────────────────────────────────────────┐
│         API Gateway (Port 8080)         │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │      Middleware Chain             │ │
│  │  1. Request ID                    │ │
│  │  2. Logging                       │ │
│  │  3. Recoverer                     │ │
│  │  4. CORS                          │ │
│  │  5. Authentication (TODO)         │ │
│  │  6. Rate Limiting (TODO)          │ │
│  └───────────────────────────────────┘ │
│                 │                       │
│                 ▼                       │
│  ┌───────────────────────────────────┐ │
│  │         Router (Chi)              │ │
│  │  - Route matching                 │ │
│  │  - Handler dispatch               │ │
│  └───────────────────────────────────┘ │
│                 │                       │
│                 ▼                       │
│  ┌───────────────────────────────────┐ │
│  │         Handlers                  │ │
│  │  - Request validation             │ │
│  │  - HTTP to gRPC transformation    │ │
│  └───────────────────────────────────┘ │
│                 │                       │
└─────────────────┼───────────────────────┘
                  │ gRPC Call
                  ▼
    ┌─────────────────────────────┐
    │   Backend Microservices     │
    │                             │
    │  ┌────────────────────────┐ │
    │  │  Auth Service          │ │
    │  │  (Port 50051)          │ │
    │  └────────────────────────┘ │
    │                             │
    │  ┌────────────────────────┐ │
    │  │  Video Service         │ │
    │  │  (Port 50052)          │ │
    │  └────────────────────────┘ │
    │                             │
    │  ┌────────────────────────┐ │
    │  │  Homework Service      │ │
    │  │  (Port 50053)          │ │
    │  └────────────────────────┘ │
    │                             │
    │  ┌────────────────────────┐ │
    │  │  Analytics Service     │ │
    │  │  (Port 50054)          │ │
    │  └────────────────────────┘ │
    │                             │
    │  ┌────────────────────────┐ │
    │  │  Collaboration Service │ │
    │  │  (Port 50055)          │ │
    │  └────────────────────────┘ │
    │                             │
    │  ┌────────────────────────┐ │
    │  │  PDF Service           │ │
    │  │  (Port 50056)          │ │
    │  └────────────────────────┘ │
    └─────────────────────────────┘
```

## Component Responsibilities

### API Gateway
- **Single Entry Point**: All client requests go through the gateway
- **Protocol Translation**: Converts HTTP/REST to gRPC
- **Cross-Cutting Concerns**: Authentication, logging, CORS, rate limiting
- **Error Handling**: Standardized error responses
- **Service Discovery**: Maintains connections to all backend services

### Middleware Chain
1. **Request ID**: Assigns unique ID for request tracing
2. **Logging**: Records request details (method, path, duration, status)
3. **Recoverer**: Catches panics and returns 500 errors
4. **CORS**: Handles cross-origin requests from frontend
5. **Authentication** (TODO): Validates JWT tokens
6. **Rate Limiting** (TODO): Prevents abuse

### Router (Chi)
- **Route Matching**: Maps URLs to handlers
- **Route Groups**: Organizes related endpoints
- **Middleware Application**: Applies middleware to specific routes
- **URL Parameters**: Extracts path parameters

### Handlers
- **Request Validation**: Validates input data
- **Business Logic**: Minimal - delegates to backend services
- **Transformation**: Converts between HTTP and gRPC formats
- **Error Handling**: Converts gRPC errors to HTTP responses

### gRPC Clients
- **Connection Management**: Maintains persistent connections
- **Load Balancing**: gRPC handles client-side load balancing
- **Retry Logic**: Automatic retries on transient failures
- **Timeout Handling**: Configurable timeouts per service

## Data Flow Example: Teacher Login

```
1. Client sends POST /api/auth/teacher/login
   {
     "email": "teacher@example.com",
     "password": "securepassword"
   }

2. API Gateway receives request
   - Request ID middleware: Assigns ID "req-12345"
   - Logging middleware: Logs incoming request
   - CORS middleware: Validates origin
   - Router: Matches to TeacherLogin handler

3. Handler processes request
   - Decodes JSON body
   - Validates email and password format
   - Creates gRPC LoginRequest message

4. gRPC call to Auth Service
   - Sends LoginRequest to Auth Service
   - Auth Service validates credentials
   - Returns AuthResponse with JWT token

5. Handler transforms response
   - Converts gRPC response to JSON
   - Sets appropriate HTTP status code
   - Returns to client

6. Middleware chain (reverse)
   - Logging middleware: Logs response (status, duration)
   - Response sent to client

7. Client receives response
   {
     "token": "eyJhbGc...",
     "user_id": "uuid-123",
     "role": "teacher",
     "expires_at": 1234567890
   }
```

## Error Handling Flow

```
Backend Service Error
        │
        ▼
gRPC Status Code
        │
        ▼
HandleGRPCError()
        │
        ▼
grpcCodeToHTTPStatus()
        │
        ▼
HTTP Status Code + JSON Error
        │
        ▼
Client receives:
{
  "error": {
    "code": "INVALID_ARGUMENT",
    "message": "Invalid email format"
  }
}
```

## Scalability Considerations

### Horizontal Scaling
- API Gateway is stateless
- Can run multiple instances behind load balancer
- Each instance maintains its own gRPC connections

### Connection Pooling
- gRPC maintains connection pools automatically
- Configurable max message sizes (50MB for file transfers)
- Automatic reconnection on failures

### Performance
- Minimal processing in gateway (just transformation)
- Business logic in backend services
- Efficient binary protocol (gRPC/protobuf)

## Security Layers

```
┌─────────────────────────────────────┐
│  Cloudflare (Edge)                  │
│  - DDoS Protection                  │
│  - WAF Rules                        │
│  - SSL/TLS Termination              │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Nginx Load Balancer                │
│  - Rate Limiting                    │
│  - Request Filtering                │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  API Gateway                        │
│  - CORS Validation                  │
│  - JWT Authentication               │
│  - Input Validation                 │
│  - Rate Limiting (per user)         │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Backend Services                   │
│  - Business Logic Validation        │
│  - Authorization Checks             │
│  - Data Access Control              │
└─────────────────────────────────────┘
```

## Deployment Architecture

### Kubernetes
```
┌─────────────────────────────────────┐
│  Ingress Controller                 │
│  - Routes traffic to services       │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  API Gateway Service                │
│  - ClusterIP: 8080                  │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  API Gateway Pods (3+ replicas)     │
│  - Auto-scaling based on CPU/Memory │
│  - Health checks: /health, /ready   │
└──────────────┬──────────────────────┘
               │
               ▼
    Backend Service Pods
```

### Resource Limits
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

### Auto-scaling
```yaml
minReplicas: 3
maxReplicas: 20
targetCPUUtilizationPercentage: 80
targetMemoryUtilizationPercentage: 85
```

## Monitoring and Observability

### Metrics (TODO)
- Request count by endpoint
- Response time percentiles (p50, p95, p99)
- Error rate by status code
- gRPC connection status

### Logging
- Request ID for tracing
- Request method, path, status
- Response time and size
- Error details with stack traces

### Health Checks
- `/health` - Basic liveness check
- `/ready` - Readiness check (can verify backend connections)

### Distributed Tracing (TODO)
- OpenTelemetry integration
- Trace requests across services
- Identify bottlenecks

## Configuration Management

### Environment Variables
```bash
# Server
PORT=8080

# Backend Services
AUTH_SERVICE_ADDR=auth-service:50051
VIDEO_SERVICE_ADDR=video-service:50052
HOMEWORK_SERVICE_ADDR=homework-service:50053
ANALYTICS_SERVICE_ADDR=analytics-service:50054
COLLABORATION_SERVICE_ADDR=collaboration-service:50055
PDF_SERVICE_ADDR=pdf-service:50056

# CORS
ALLOWED_ORIGINS=https://metlab.edu,https://www.metlab.edu
```

### Kubernetes ConfigMap
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-gateway-config
data:
  AUTH_SERVICE_ADDR: "auth-service:50051"
  VIDEO_SERVICE_ADDR: "video-service:50052"
  # ... other services
```

### Kubernetes Secret
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: api-gateway-secrets
type: Opaque
data:
  JWT_SECRET: <base64-encoded>
```

## Future Enhancements

1. **Circuit Breaker**: Prevent cascading failures
2. **Request Caching**: Cache frequent read requests
3. **GraphQL Support**: Alternative to REST API
4. **WebSocket Support**: Real-time bidirectional communication
5. **API Versioning**: Support multiple API versions
6. **Request Throttling**: Advanced rate limiting strategies
7. **Metrics Export**: Prometheus metrics endpoint
8. **Distributed Tracing**: OpenTelemetry integration
