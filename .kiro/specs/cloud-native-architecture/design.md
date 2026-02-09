# Design Document: Cloud-Native Architecture Migration

## Overview

This document outlines the technical design for migrating Metlab.edu from a Django monolithic architecture to a cloud-native, microservices-based system. The new architecture leverages modern technologies including Cloudflare for edge services, Nginx for load balancing, Kubernetes for orchestration, TanStack Start for the frontend, Go for backend services, and PostgreSQL for data persistence.

### Migration Strategy

The migration will follow a **strangler fig pattern**, gradually replacing Django components with new microservices while maintaining system availability. This approach minimizes risk and allows for incremental validation.

### High-Level Architecture

```
[Users] 
   ↓
[Cloudflare CDN/WAF/DDoS]
   ↓
[Nginx Load Balancer]
   ↓
[Kubernetes Cluster]
   ├── Frontend Service (TanStack Start)
   ├── API Gateway Service (Go)
   ├── Auth Service (Go)
   ├── Video Service (Go)
   ├── Homework Service (Go)
   ├── Analytics Service (Go)
   ├── Study Group Service (Go)
   └── Chat Service (Go)
   ↓
[PostgreSQL Database Cluster]
[Redis Cache]
[Object Storage (S3-compatible)]
```

## Architecture

### 1. Edge Layer (Cloudflare)

**Purpose**: Provide CDN, WAF, and DDoS protection at the edge

**Components**:

- **Cloudflare CDN**: Cache static assets (JS, CSS, images, videos) with 85%+ hit ratio
- **Cloudflare WAF**: Filter malicious traffic using OWASP ruleset
- **Cloudflare DDoS Protection**: Automatic mitigation of L3/L4/L7 attacks
- **SSL/TLS Termination**: Handle TLS 1.3 encryption at the edge

**Configuration**:
- Cache rules: Static assets cached for 7 days, API responses not cached
- WAF rules: Block SQL injection, XSS, and common attack patterns
- Rate limiting: 100 requests/minute per IP for API endpoints
- Page rules: Always use HTTPS, browser cache TTL 4 hours

### 2. Load Balancing Layer (Nginx)

**Purpose**: Distribute traffic across backend service instances

**Configuration**:
```nginx
upstream frontend_service {
    least_conn;
    server frontend-1:3000 max_fails=3 fail_timeout=30s;
    server frontend-2:3000 max_fails=3 fail_timeout=30s;
    server frontend-3:3000 max_fails=3 fail_timeout=30s;
}

upstream api_gateway {
    least_conn;
    server api-gateway-1:8080 max_fails=3 fail_timeout=30s;
    server api-gateway-2:8080 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name metlab.edu;
    
    location / {
        proxy_pass http://frontend_service;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/ {
        proxy_pass http://api_gateway;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Health Checks**:
- HTTP GET to `/health` endpoint every 10 seconds
- Mark instance unhealthy after 3 consecutive failures
- Remove from pool for 30 seconds before retry

### 3. Container Orchestration (Kubernetes)

**Purpose**: Manage containerized services with auto-scaling and self-healing

**Cluster Architecture**:

- **Namespaces**: `production`, `staging`, `development`
- **Node Pools**: 
  - Frontend pool: 3-10 nodes (CPU optimized)
  - Backend pool: 5-20 nodes (balanced)
  - Database pool: 3 nodes (memory optimized)

**Auto-scaling Configuration**:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-gateway-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-gateway
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 80
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 85
```

**Resource Limits**:
- Frontend pods: 256Mi-512Mi memory, 200m-500m CPU
- Backend pods: 512Mi-1Gi memory, 500m-1000m CPU
- Database pods: 4Gi-8Gi memory, 2000m-4000m CPU

### 4. Development Environment

**Minikube Setup**:
```bash
minikube start --cpus=4 --memory=8192 --driver=docker
minikube addons enable ingress
minikube addons enable metrics-server
```

**Tilt Configuration** (`Tiltfile`):
```python
# Frontend service
docker_build('metlab-frontend', './frontend')
k8s_yaml('k8s/frontend-deployment.yaml')
k8s_resource('frontend', port_forwards='3000:3000')

# API Gateway
docker_build('metlab-api-gateway', './services/api-gateway')
k8s_yaml('k8s/api-gateway-deployment.yaml')
k8s_resource('api-gateway', port_forwards='8080:8080')

# Auto-reload on file changes
watch_file('./frontend/src')
watch_file('./services/api-gateway')
```

## Components and Interfaces

### 1. Frontend Service (TanStack Start)

**Technology Stack**:
- TanStack Start (React-based SSR framework)
- TanStack Query for data fetching
- TanStack Router for routing
- Tailwind CSS for styling
- Vite for build tooling

**Project Structure**:
```
frontend/
├── src/
│   ├── routes/
│   │   ├── __root.tsx
│   │   ├── index.tsx
│   │   ├── teacher/
│   │   │   ├── dashboard.tsx
│   │   │   ├── students.tsx
│   │   │   ├── videos.tsx
│   │   │   └── homework.tsx
│   │   └── student/
│   │       ├── dashboard.tsx
│   │       ├── videos.tsx
│   │       ├── homework.tsx
│   │       └── study-groups.tsx
│   ├── components/
│   ├── hooks/
│   ├── api/
│   └── utils/
├── Dockerfile
└── package.json
```

**Key Features**:

- Server-side rendering for initial page load
- Code splitting by route
- Optimistic UI updates
- Real-time updates via WebSocket
- Progressive Web App capabilities

**API Client**:
```typescript
// src/api/client.ts
import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000, // 1 minute
      cacheTime: 5 * 60 * 1000, // 5 minutes
      retry: 3,
    },
  },
})

export const apiClient = {
  baseURL: process.env.API_URL || 'http://localhost:8080/api',
  
  async request(endpoint: string, options?: RequestInit) {
    const token = localStorage.getItem('auth_token')
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
        ...options?.headers,
      },
    })
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`)
    }
    
    return response.json()
  },
}
```

### 2. API Gateway Service (Go)

**Purpose**: Single entry point for all backend services, handles routing, authentication, and rate limiting

**Technology Stack**:
- Go 1.21+
- Chi router
- gRPC client for service communication
- JWT for authentication

**Project Structure**:
```
services/api-gateway/
├── cmd/
│   └── server/
│       └── main.go
├── internal/
│   ├── handlers/
│   ├── middleware/
│   ├── auth/
│   └── grpc/
├── proto/
├── Dockerfile
└── go.mod
```

**Key Responsibilities**:
- Route HTTP requests to appropriate microservices
- Validate JWT tokens
- Rate limiting per IP/user
- Request/response transformation
- API versioning

**Example Handler**:
```go
// internal/handlers/video.go
package handlers

import (
    "net/http"
    "github.com/go-chi/chi/v5"
    pb "metlab/proto/video"
)

type VideoHandler struct {
    videoClient pb.VideoServiceClient
}

func (h *VideoHandler) ListVideos(w http.ResponseWriter, r *http.Request) {
    userID := r.Context().Value("user_id").(string)
    classID := chi.URLParam(r, "classID")
    
    resp, err := h.videoClient.ListVideos(r.Context(), &pb.ListVideosRequest{
        UserId: userID,
        ClassId: classID,
    })
    
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    
    json.NewEncoder(w).Encode(resp)
}
```

### 3. Authentication Service (Go)

**Purpose**: Handle user authentication, authorization, and session management

**Database Schema**:

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255),
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('teacher', 'student')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE teachers (
    id UUID PRIMARY KEY REFERENCES users(id),
    subject_area VARCHAR(100),
    verified BOOLEAN DEFAULT false
);

CREATE TABLE signin_codes (
    code VARCHAR(8) PRIMARY KEY,
    teacher_id UUID REFERENCES teachers(id),
    class_id UUID REFERENCES classes(id),
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT false,
    used_by UUID REFERENCES users(id),
    used_at TIMESTAMP
);

CREATE TABLE students (
    id UUID PRIMARY KEY REFERENCES users(id),
    teacher_id UUID REFERENCES teachers(id),
    signin_code VARCHAR(8) REFERENCES signin_codes(code)
);

CREATE INDEX idx_signin_codes_teacher ON signin_codes(teacher_id);
CREATE INDEX idx_signin_codes_expires ON signin_codes(expires_at) WHERE NOT used;
CREATE INDEX idx_students_teacher ON students(teacher_id);
```

**JWT Token Structure**:
```json
{
  "sub": "user-uuid",
  "role": "teacher|student",
  "exp": 1234567890,
  "iat": 1234567890,
  "teacher_id": "teacher-uuid",
  "class_ids": ["class-uuid-1", "class-uuid-2"]
}
```

**gRPC Service Definition** (`proto/auth/auth.proto`):
```protobuf
syntax = "proto3";
package auth;
option go_package = "metlab/proto/auth";

service AuthService {
  rpc TeacherSignup(TeacherSignupRequest) returns (AuthResponse);
  rpc TeacherLogin(LoginRequest) returns (AuthResponse);
  rpc StudentSignin(StudentSigninRequest) returns (AuthResponse);
  rpc ValidateToken(ValidateTokenRequest) returns (ValidateTokenResponse);
  rpc GenerateSigninCode(GenerateSigninCodeRequest) returns (SigninCodeResponse);
}

message TeacherSignupRequest {
  string email = 1;
  string password = 2;
  string full_name = 3;
  string subject_area = 4;
}

message StudentSigninRequest {
  string teacher_name = 1;
  string student_name = 2;
  string signin_code = 3;
}

message AuthResponse {
  string token = 1;
  string user_id = 2;
  string role = 3;
  int64 expires_at = 4;
}

message GenerateSigninCodeRequest {
  string teacher_id = 1;
  string class_id = 2;
}

message SigninCodeResponse {
  string code = 1;
  int64 expires_at = 2;
}
```

### 4. Video Service (Go)

**Purpose**: Handle video uploads, processing, storage, and streaming

**Technology Stack**:
- FFmpeg for video processing
- S3-compatible object storage (MinIO for dev, AWS S3 for prod)
- HLS for adaptive streaming

**Database Schema**:
```sql
CREATE TABLE videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID REFERENCES teachers(id),
    class_id UUID REFERENCES classes(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    original_filename VARCHAR(255),
    storage_path VARCHAR(500),
    duration_seconds INT,
    file_size_bytes BIGINT,
    status VARCHAR(20) CHECK (status IN ('uploading', 'processing', 'ready', 'failed')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE video_variants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
    resolution VARCHAR(20), -- '1080p', '720p', '480p', '360p'
    bitrate_kbps INT,
    storage_path VARCHAR(500),
    file_size_bytes BIGINT
);

CREATE TABLE video_thumbnails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
    timestamp_percent INT, -- 0, 25, 50, 75
    storage_path VARCHAR(500)
);

CREATE TABLE video_views (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID REFERENCES videos(id),
    student_id UUID REFERENCES students(id),
    started_at TIMESTAMP DEFAULT NOW(),
    last_position_seconds INT DEFAULT 0,
    total_watch_seconds INT DEFAULT 0,
    completed BOOLEAN DEFAULT false,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_video_views_video_student ON video_views(video_id, student_id);
CREATE INDEX idx_videos_class ON videos(class_id);
```

**Video Processing Pipeline**:

1. Upload original video to object storage
2. Queue processing job
3. Generate multiple resolutions (1080p, 720p, 480p, 360p)
4. Create HLS manifest
5. Generate thumbnails at 0%, 25%, 50%, 75%
6. Update video status to 'ready'

**gRPC Service Definition** (`proto/video/video.proto`):
```protobuf
syntax = "proto3";
package video;
option go_package = "metlab/proto/video";

service VideoService {
  rpc UploadVideo(stream UploadVideoRequest) returns (UploadVideoResponse);
  rpc ListVideos(ListVideosRequest) returns (ListVideosResponse);
  rpc GetVideo(GetVideoRequest) returns (Video);
  rpc GetStreamingURL(GetStreamingURLRequest) returns (StreamingURLResponse);
  rpc RecordView(RecordViewRequest) returns (RecordViewResponse);
  rpc GetVideoAnalytics(GetVideoAnalyticsRequest) returns (VideoAnalyticsResponse);
}

message Video {
  string id = 1;
  string title = 2;
  string description = 3;
  int32 duration_seconds = 4;
  string thumbnail_url = 5;
  string status = 6;
  int64 created_at = 7;
}

message RecordViewRequest {
  string video_id = 1;
  string student_id = 2;
  int32 position_seconds = 3;
  int32 watch_duration_seconds = 4;
}
```

### 5. Homework Service (Go)

**Purpose**: Manage homework assignments, submissions, and grading

**Database Schema**:
```sql
CREATE TABLE homework_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID REFERENCES teachers(id),
    class_id UUID REFERENCES classes(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    due_date TIMESTAMP NOT NULL,
    max_score INT DEFAULT 100,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE homework_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assignment_id UUID REFERENCES homework_assignments(id),
    student_id UUID REFERENCES students(id),
    file_path VARCHAR(500),
    file_name VARCHAR(255),
    file_size_bytes BIGINT,
    submitted_at TIMESTAMP DEFAULT NOW(),
    is_late BOOLEAN DEFAULT false,
    status VARCHAR(20) CHECK (status IN ('submitted', 'graded', 'returned')),
    UNIQUE(assignment_id, student_id)
);

CREATE TABLE homework_grades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id UUID REFERENCES homework_submissions(id) UNIQUE,
    score INT,
    feedback TEXT,
    graded_by UUID REFERENCES teachers(id),
    graded_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_homework_assignments_class ON homework_assignments(class_id);
CREATE INDEX idx_homework_submissions_assignment ON homework_submissions(assignment_id);
CREATE INDEX idx_homework_submissions_student ON homework_submissions(student_id);
```

**gRPC Service Definition** (`proto/homework/homework.proto`):
```protobuf
syntax = "proto3";
package homework;
option go_package = "metlab/proto/homework";

service HomeworkService {
  rpc CreateAssignment(CreateAssignmentRequest) returns (Assignment);
  rpc ListAssignments(ListAssignmentsRequest) returns (ListAssignmentsResponse);
  rpc SubmitHomework(stream SubmitHomeworkRequest) returns (SubmitHomeworkResponse);
  rpc ListSubmissions(ListSubmissionsRequest) returns (ListSubmissionsResponse);
  rpc GradeSubmission(GradeSubmissionRequest) returns (GradeSubmissionResponse);
  rpc GetSubmissionFile(GetSubmissionFileRequest) returns (stream FileChunk);
}

message Assignment {
  string id = 1;
  string title = 2;
  string description = 3;
  int64 due_date = 4;
  int32 max_score = 5;
  int32 submission_count = 6;
}

message GradeSubmissionRequest {
  string submission_id = 1;
  string teacher_id = 2;
  int32 score = 3;
  string feedback = 4;
}
```

### 6. Analytics Service (Go)

**Purpose**: Track and report user activity and engagement metrics

**Database Schema**:
```sql
CREATE TABLE student_logins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES students(id),
    login_at TIMESTAMP DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

CREATE TABLE pdf_downloads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pdf_id UUID REFERENCES pdfs(id),
    student_id UUID REFERENCES students(id),
    downloaded_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_student_logins_student_date ON student_logins(student_id, login_at DESC);
CREATE INDEX idx_pdf_downloads_student ON pdf_downloads(student_id);
```

**gRPC Service Definition** (`proto/analytics/analytics.proto`):
```protobuf
syntax = "proto3";
package analytics;
option go_package = "metlab/proto/analytics";

service AnalyticsService {
  rpc RecordLogin(RecordLoginRequest) returns (RecordLoginResponse);
  rpc GetStudentLoginStats(GetStudentLoginStatsRequest) returns (LoginStatsResponse);
  rpc GetClassEngagement(GetClassEngagementRequest) returns (ClassEngagementResponse);
}

message LoginStatsResponse {
  repeated DailyLoginCount daily_counts = 1;
  int32 total_logins = 2;
  double average_per_week = 3;
}

message DailyLoginCount {
  string date = 1;
  int32 count = 2;
}
```

### 7. Study Group & Chat Service (Go)

**Purpose**: Enable student collaboration through study groups and real-time chat

**Database Schema**:

```sql
CREATE TABLE study_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    class_id UUID REFERENCES classes(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_by UUID REFERENCES students(id),
    created_at TIMESTAMP DEFAULT NOW(),
    max_members INT DEFAULT 10
);

CREATE TABLE study_group_members (
    study_group_id UUID REFERENCES study_groups(id) ON DELETE CASCADE,
    student_id UUID REFERENCES students(id),
    joined_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (study_group_id, student_id)
);

CREATE TABLE chat_rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    class_id UUID REFERENCES classes(id),
    name VARCHAR(255) NOT NULL,
    created_by UUID REFERENCES students(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_room_id UUID REFERENCES chat_rooms(id) ON DELETE CASCADE,
    sender_id UUID REFERENCES students(id),
    message_text TEXT,
    image_path VARCHAR(500),
    sent_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_chat_messages_room_time ON chat_messages(chat_room_id, sent_at DESC);
CREATE INDEX idx_study_groups_class ON study_groups(class_id);
```

**Real-time Communication**:
- WebSocket connections for chat
- Redis Pub/Sub for message distribution across service instances
- Message retention: 7 days

**gRPC Service Definition** (`proto/collaboration/collaboration.proto`):
```protobuf
syntax = "proto3";
package collaboration;
option go_package = "metlab/proto/collaboration";

service CollaborationService {
  rpc CreateStudyGroup(CreateStudyGroupRequest) returns (StudyGroup);
  rpc JoinStudyGroup(JoinStudyGroupRequest) returns (JoinStudyGroupResponse);
  rpc ListStudyGroups(ListStudyGroupsRequest) returns (ListStudyGroupsResponse);
  rpc CreateChatRoom(CreateChatRoomRequest) returns (ChatRoom);
  rpc SendMessage(SendMessageRequest) returns (SendMessageResponse);
  rpc GetMessages(GetMessagesRequest) returns (GetMessagesResponse);
  rpc StreamMessages(StreamMessagesRequest) returns (stream ChatMessage);
}

message StudyGroup {
  string id = 1;
  string name = 2;
  string description = 3;
  int32 member_count = 4;
  int32 max_members = 5;
}

message ChatMessage {
  string id = 1;
  string sender_id = 2;
  string sender_name = 3;
  string message_text = 4;
  string image_url = 5;
  int64 sent_at = 6;
}
```

### 8. PDF Service (Go)

**Purpose**: Manage PDF document uploads and downloads

**Database Schema**:
```sql
CREATE TABLE pdfs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID REFERENCES teachers(id),
    class_id UUID REFERENCES classes(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    file_name VARCHAR(255),
    storage_path VARCHAR(500),
    file_size_bytes BIGINT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_pdfs_class ON pdfs(class_id);
```

**gRPC Service Definition** (`proto/pdf/pdf.proto`):
```protobuf
syntax = "proto3";
package pdf;
option go_package = "metlab/proto/pdf";

service PDFService {
  rpc UploadPDF(stream UploadPDFRequest) returns (UploadPDFResponse);
  rpc ListPDFs(ListPDFsRequest) returns (ListPDFsResponse);
  rpc GetDownloadURL(GetDownloadURLRequest) returns (DownloadURLResponse);
}

message PDF {
  string id = 1;
  string title = 2;
  string description = 3;
  int64 file_size_bytes = 4;
  int64 created_at = 5;
}

message DownloadURLResponse {
  string url = 1;
  int64 expires_at = 2;
}
```

## Data Models

### Core Entities

**Class**:
```sql
CREATE TABLE classes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID REFERENCES teachers(id),
    name VARCHAR(255) NOT NULL,
    subject VARCHAR(100),
    grade_level VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX idx_classes_teacher ON classes(teacher_id);
```

**Relationships**:
- One teacher has many classes
- One class has many students
- One class has many videos, PDFs, homework assignments
- One student belongs to one class (can be extended to many-to-many)
- One student can join multiple study groups (max 5)

### Database Connection Management

**Connection Pool Configuration**:
```go
// internal/db/postgres.go
package db

import (
    "github.com/jackc/pgx/v5/pgxpool"
)

func NewPool(connString string) (*pgxpool.Pool, error) {
    config, err := pgxpool.ParseConfig(connString)
    if err != nil {
        return nil, err
    }
    
    config.MinConns = 10
    config.MaxConns = 100
    config.MaxConnLifetime = time.Hour
    config.MaxConnIdleTime = 30 * time.Minute
    
    return pgxpool.NewWithConfig(context.Background(), config)
}
```

## Error Handling

### Error Types

**gRPC Status Codes**:
- `INVALID_ARGUMENT`: Invalid input data
- `UNAUTHENTICATED`: Missing or invalid JWT token
- `PERMISSION_DENIED`: User lacks required permissions
- `NOT_FOUND`: Resource doesn't exist
- `ALREADY_EXISTS`: Duplicate resource
- `RESOURCE_EXHAUSTED`: Rate limit exceeded
- `INTERNAL`: Server error

**Error Response Format**:
```json
{
  "error": {
    "code": "INVALID_SIGNIN_CODE",
    "message": "The signin code is invalid or expired",
    "details": {
      "field": "signin_code",
      "reason": "expired"
    }
  }
}
```

### Retry Strategy

**Client-side Retries**:
- Exponential backoff: 100ms, 200ms, 400ms
- Max 3 retries for idempotent operations
- No retry for 4xx errors (except 429)
- Retry for 5xx errors and network failures

**Circuit Breaker**:

- Open circuit after 5 consecutive failures
- Half-open after 30 seconds
- Close circuit after 2 successful requests

## Testing Strategy

### Unit Testing

**Go Services**:
- Use `testing` package and `testify` for assertions
- Mock gRPC clients using generated mock interfaces
- Mock database using `pgxmock`
- Target: 80% code coverage

**Frontend**:
- Vitest for unit tests
- React Testing Library for component tests
- Mock API calls using MSW (Mock Service Worker)
- Target: 70% code coverage

### Integration Testing

**Service-to-Service**:
- Test gRPC communication between services
- Use test containers for PostgreSQL and Redis
- Verify data consistency across services

**API Gateway**:
- Test HTTP to gRPC translation
- Verify authentication middleware
- Test rate limiting

### End-to-End Testing

**User Flows**:
- Teacher signup → student registration → video upload → student viewing
- Student homework submission → teacher grading → student viewing grade
- Study group creation → chat messaging

**Tools**:
- Playwright for browser automation
- Test against staging environment
- Run nightly on main branch

### Performance Testing

**Load Testing**:
- Use k6 for load testing
- Simulate 1000 concurrent users
- Target: 95th percentile response time < 500ms
- Target: 0.1% error rate

**Scenarios**:
- Video streaming under load
- Concurrent homework submissions
- Real-time chat with 100 active users

### Security Testing

**Automated Scans**:
- OWASP ZAP for vulnerability scanning
- Trivy for container image scanning
- Dependabot for dependency updates

**Manual Testing**:
- Penetration testing quarterly
- Security code review for auth changes

## Deployment Architecture

### Kubernetes Manifests

**Namespace**:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: metlab-production
```

**ConfigMap**:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: metlab-config
  namespace: metlab-production
data:
  DATABASE_HOST: "postgres-service"
  DATABASE_PORT: "5432"
  REDIS_HOST: "redis-service"
  REDIS_PORT: "6379"
  S3_ENDPOINT: "s3.amazonaws.com"
  S3_BUCKET: "metlab-media"
```

**Secret**:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: metlab-secrets
  namespace: metlab-production
type: Opaque
data:
  DATABASE_PASSWORD: <base64-encoded>
  JWT_SECRET: <base64-encoded>
  S3_ACCESS_KEY: <base64-encoded>
  S3_SECRET_KEY: <base64-encoded>
```

**Deployment Example (API Gateway)**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  namespace: metlab-production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
    spec:
      containers:
      - name: api-gateway
        image: metlab/api-gateway:latest
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: metlab-secrets
              key: DATABASE_PASSWORD
        envFrom:
        - configMapRef:
            name: metlab-config
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

**Service**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: api-gateway-service
  namespace: metlab-production
spec:
  selector:
    app: api-gateway
  ports:
  - protocol: TCP
    port: 8080
    targetPort: 8080
  type: ClusterIP
```

**Ingress**:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: metlab-ingress
  namespace: metlab-production
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  ingressClassName: nginx
  rules:
  - host: metlab.edu
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-gateway-service
            port:
              number: 8080
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 3000
```

### CI/CD Pipeline

**GitHub Actions Workflow**:
```yaml
name: Build and Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: make test
      
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker images
        run: |
          docker build -t metlab/api-gateway:${{ github.sha }} ./services/api-gateway
          docker build -t metlab/frontend:${{ github.sha }} ./frontend
      - name: Push to registry
        run: |
          docker push metlab/api-gateway:${{ github.sha }}
          docker push metlab/frontend:${{ github.sha }}
  
  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/api-gateway \
            api-gateway=metlab/api-gateway:${{ github.sha }} \
            -n metlab-production
```

## Migration Plan

### Phase 1: Infrastructure Setup (Weeks 1-2)

1. Set up Kubernetes cluster (Minikube for dev, cloud provider for prod)
2. Configure Cloudflare DNS and edge services
3. Deploy Nginx ingress controller
4. Set up PostgreSQL cluster with replication
5. Deploy Redis for caching and pub/sub
6. Configure S3-compatible object storage
7. Set up monitoring (Prometheus, Grafana)
8. Configure logging (ELK stack or cloud provider)

### Phase 2: Core Services (Weeks 3-5)

1. Implement Authentication Service
   - User registration and login
   - JWT token generation and validation
   - Signin code generation
2. Implement API Gateway
   - HTTP routing
   - Authentication middleware
   - Rate limiting
3. Deploy Frontend skeleton
   - Basic routing
   - Authentication flows
   - Layout components

### Phase 3: Content Services (Weeks 6-8)

1. Implement Video Service
   - Upload and storage
   - Video processing pipeline
   - Streaming endpoints
   - View tracking
2. Implement PDF Service
   - Upload and storage
   - Download URL generation
3. Migrate existing content from Django
   - Export videos and PDFs
   - Import to new storage
   - Update database references

### Phase 4: Academic Services (Weeks 9-11)

1. Implement Homework Service
   - Assignment creation
   - Submission handling
   - Grading functionality
2. Implement Analytics Service
   - Login tracking
   - Activity reporting
   - Dashboard data
3. Migrate homework data from Django

### Phase 5: Collaboration Services (Weeks 12-13)

1. Implement Study Group Service
   - Group creation and management
   - Membership handling
2. Implement Chat Service
   - WebSocket connections
   - Message persistence
   - Real-time delivery

### Phase 6: Testing & Optimization (Weeks 14-15)

1. End-to-end testing
2. Performance optimization
3. Security audit
4. Load testing
5. Documentation

### Phase 7: Cutover (Week 16)

1. Final data migration
2. DNS cutover to new system
3. Monitor for issues
4. Keep Django system as fallback for 1 week
5. Decommission Django after validation

## Monitoring and Observability

### Metrics

**Application Metrics** (Prometheus):
- Request rate, latency, error rate per service
- gRPC call duration and status codes
- Database connection pool usage
- Cache hit/miss ratio
- Video processing queue length
- Active WebSocket connections

**Infrastructure Metrics**:
- CPU, memory, disk usage per pod
- Network I/O
- Pod restart count
- Node resource utilization

**Business Metrics**:
- Daily active users (teachers, students)
- Video views per day
- Homework submission rate
- Average grading time
- Chat message volume

### Logging

**Structured Logging Format**:
```json
{
  "timestamp": "2026-02-09T10:30:00Z",
  "level": "INFO",
  "service": "api-gateway",
  "trace_id": "abc123",
  "user_id": "user-uuid",
  "message": "Request processed",
  "duration_ms": 45,
  "status_code": 200,
  "path": "/api/videos"
}
```

**Log Aggregation**:
- Centralized logging with ELK stack or cloud provider
- Log retention: 30 days for INFO, 90 days for ERROR
- Searchable by trace_id, user_id, service

### Tracing

**Distributed Tracing** (Jaeger or cloud provider):
- Trace requests across all services
- Identify bottlenecks
- Debug cross-service issues

### Alerting

**Critical Alerts** (PagerDuty or similar):
- Service down (no healthy pods)
- Error rate > 5%
- Database connection failures
- Disk usage > 90%

**Warning Alerts** (Slack):
- Response time p95 > 1s
- Cache hit ratio < 70%
- Video processing queue > 100
- Pod restart detected

## Security Considerations

### Authentication & Authorization

- JWT tokens with 24-hour expiry for teachers, 7-day for students
- Refresh tokens stored in httpOnly cookies
- Role-based access control (RBAC)
- Teacher can only access their own classes
- Students can only access their enrolled class

### Data Protection

- TLS 1.3 for all external communication
- mTLS for internal service-to-service communication
- Database encryption at rest (AES-256)
- Encrypted backups
- PII data anonymization in logs

### Input Validation

- Validate all inputs against proto3 schemas
- Sanitize user-generated content
- File upload validation (type, size, content)
- SQL injection prevention via prepared statements
- XSS prevention via content security policy

### Rate Limiting

- API Gateway: 100 requests/minute per IP
- Authentication: 5 login attempts per 15 minutes
- File uploads: 10 per hour per user
- Chat messages: 60 per minute per user

### Secrets Management

- Kubernetes Secrets for sensitive data
- Rotate secrets quarterly
- Never commit secrets to git
- Use environment variables for configuration

## Performance Optimization

### Caching Strategy

**Redis Cache**:
- User sessions: 24 hours
- Video metadata: 1 hour
- Class rosters: 30 minutes
- Homework assignments: 15 minutes

**CDN Cache** (Cloudflare):
- Static assets: 7 days
- Video thumbnails: 30 days
- Processed videos: 30 days

### Database Optimization

- Indexes on all foreign keys
- Composite indexes for common queries
- Read replicas for analytics queries
- Connection pooling (10-100 connections)
- Query timeout: 5 seconds

### Frontend Optimization

- Code splitting by route
- Lazy loading for images and videos
- Service worker for offline support
- Prefetch critical resources
- Bundle size < 200KB gzipped

## Disaster Recovery

### Backup Strategy

**Database Backups**:
- Automated backups every 6 hours
- Retention: 30 days
- Test restore monthly
- Cross-region replication

**Object Storage**:
- Versioning enabled
- Cross-region replication
- Lifecycle policy: archive after 1 year

### Recovery Procedures

**RTO (Recovery Time Objective)**: 1 hour
**RPO (Recovery Point Objective)**: 6 hours

**Incident Response**:
1. Detect issue via monitoring
2. Assess impact and severity
3. Activate incident response team
4. Restore from backup if needed
5. Post-mortem within 48 hours

## Cost Optimization

### Resource Allocation

- Right-size pods based on actual usage
- Use spot instances for non-critical workloads
- Auto-scale down during off-hours
- Archive old videos to cheaper storage tier

### Monitoring Costs

- Track cloud provider costs per service
- Set budget alerts
- Review and optimize monthly

## Documentation

### Developer Documentation

- API documentation (OpenAPI/Swagger)
- gRPC service documentation
- Database schema documentation
- Deployment runbooks
- Troubleshooting guides

### User Documentation

- Teacher onboarding guide
- Student onboarding guide
- Feature tutorials
- FAQ

## Conclusion

This design provides a comprehensive blueprint for migrating Metlab.edu to a modern, cloud-native architecture. The microservices approach enables independent scaling, faster development cycles, and improved reliability. The use of Kubernetes, Go, and TanStack Start provides a solid foundation for future growth while maintaining high performance and security standards.
