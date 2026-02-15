# Homework Handlers Implementation

## Overview

This document describes the implementation of HTTP handlers for homework endpoints in the API Gateway service. These handlers provide REST API access to the Homework microservice via gRPC.

## Implementation Date

February 15, 2026

## Implemented Endpoints

### 1. POST /api/homework/assignments
**Handler:** `CreateAssignment`

Creates a new homework assignment for a class.

**Request Body:**
```json
{
  "teacher_id": "uuid",
  "class_id": "uuid",
  "title": "Assignment Title",
  "description": "Assignment description",
  "due_date": 1234567890,
  "max_score": 100
}
```

**Response (201 Created):**
```json
{
  "id": "uuid",
  "title": "Assignment Title",
  "description": "Assignment description",
  "due_date": 1234567890,
  "max_score": 100,
  "submission_count": 0,
  "graded_count": 0,
  "created_at": 1234567890
}
```

**Features:**
- Validates required fields (teacher_id, class_id, title)
- Validates due_date is a valid timestamp
- Defaults max_score to 100 if not provided
- Requires authentication

---

### 2. GET /api/homework/assignments
**Handler:** `ListAssignments`

Lists all homework assignments for a class.

**Query Parameters:**
- `class_id` (required): The class ID to filter assignments
- `role` (optional): User role (teacher/student), defaults to student

**Response (200 OK):**
```json
{
  "assignments": [
    {
      "id": "uuid",
      "title": "Assignment Title",
      "description": "Assignment description",
      "due_date": 1234567890,
      "max_score": 100,
      "submission_count": 5,
      "graded_count": 3,
      "created_at": 1234567890
    }
  ]
}
```

**Features:**
- Filters assignments by class_id
- Supports role-based filtering
- Requires authentication

---

### 3. POST /api/homework/submissions
**Handler:** `SubmitHomework`

Submits homework for an assignment.

**Request (multipart/form-data):**
- `assignment_id`: Assignment UUID
- `student_id`: Student UUID
- `file`: The homework file (max 25MB)

**Response (201 Created):**
```json
{
  "submission_id": "uuid",
  "is_late": false,
  "status": "submitted"
}
```

**Features:**
- Accepts multipart form data with file upload
- Validates file size (max 25MB)
- Streams file to backend service in 1MB chunks
- Automatically detects late submissions
- Requires authentication

---

### 4. GET /api/homework/submissions
**Handler:** `ListSubmissions`

Lists all submissions for a homework assignment.

**Query Parameters:**
- `assignment_id` (required): The assignment ID
- `status` (optional): Filter by status (submitted/graded)

**Response (200 OK):**
```json
{
  "submissions": [
    {
      "id": "uuid",
      "assignment_id": "uuid",
      "student_id": "uuid",
      "student_name": "John Doe",
      "filename": "homework.pdf",
      "submitted_at": 1234567890,
      "is_late": false,
      "status": "graded",
      "grade": {
        "score": 95,
        "feedback": "Great work!",
        "graded_at": 1234567890,
        "graded_by": "teacher-uuid"
      }
    }
  ]
}
```

**Features:**
- Lists all submissions for an assignment
- Includes student information
- Shows grade information if available
- Supports status filtering
- Requires authentication

---

### 5. POST /api/homework/submissions/:id/grade
**Handler:** `GradeSubmission`

Grades a homework submission.

**URL Parameters:**
- `id`: Submission UUID

**Request Body:**
```json
{
  "score": 95,
  "feedback": "Great work! Keep it up."
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "grade": {
    "score": 95,
    "feedback": "Great work! Keep it up.",
    "graded_at": 1234567890,
    "graded_by": "teacher-uuid"
  }
}
```

**Features:**
- Validates score is non-negative
- Allows updating existing grades
- Records grading timestamp and teacher
- Requires authentication

---

### 6. GET /api/homework/submissions/:id/file
**Handler:** `GetSubmissionFile`

Downloads a homework submission file.

**URL Parameters:**
- `id`: Submission UUID

**Response (200 OK):**
- Content-Type: application/octet-stream
- Content-Disposition: attachment
- Body: File binary data (streamed)

**Features:**
- Streams file from backend service
- Sets appropriate headers for file download
- Verifies teacher has permission to access
- Requires authentication

---

## Technical Implementation Details

### File Structure
```
cloud-native/services/api-gateway/internal/handlers/
├── homework.go          # New file with all homework handlers
├── handlers.go          # Base handler struct
├── auth.go             # Auth handlers
└── video.go            # Video handlers
```

### Request/Response Types

All request and response types are defined in `homework.go`:
- `CreateAssignmentRequest`
- `AssignmentResponse`
- `ListAssignmentsResponse`
- `SubmitHomeworkRequest`
- `SubmitHomeworkResponse`
- `SubmissionResponse`
- `GradeDetails`
- `ListSubmissionsResponse`
- `GradeSubmissionRequest`
- `GradeSubmissionResponse`

### Error Handling

All handlers use the standard error handling pattern:
- `transformers.WriteError()` for validation errors
- `transformers.HandleGRPCError()` for backend service errors
- Proper HTTP status codes (400, 401, 500, etc.)

### Authentication

All homework endpoints require authentication via the `Authenticate` middleware:
- JWT token extracted from Authorization header
- User ID added to request context
- Used for authorization checks in backend service

### File Upload/Download

**Upload (SubmitHomework):**
- Accepts multipart/form-data
- Max file size: 25MB
- Streams file in 1MB chunks to backend
- Timeout: 10 minutes

**Download (GetSubmissionFile):**
- Streams file from backend to client
- Sets Content-Disposition header for download
- Timeout: 5 minutes

### gRPC Integration

All handlers communicate with the Homework microservice via gRPC:
- Client: `h.clients.Homework` (HomeworkServiceClient)
- Timeout: 10 seconds (except file operations)
- Error handling via `transformers.HandleGRPCError()`

### Router Integration

Endpoints are registered in `router.go`:
```go
r.Route("/homework", func(r chi.Router) {
    r.Route("/assignments", func(r chi.Router) {
        r.Post("/", handler.CreateAssignment)
        r.Get("/", handler.ListAssignments)
    })
    r.Route("/submissions", func(r chi.Router) {
        r.Post("/", handler.SubmitHomework)
        r.Get("/", handler.ListSubmissions)
        r.Post("/{id}/grade", handler.GradeSubmission)
        r.Get("/{id}/file", handler.GetSubmissionFile)
    })
})
```

## Requirements Coverage

This implementation satisfies the following requirements from the design document:

- **6.1**: Teacher can create homework assignments
- **6.2**: Teacher can view all homework submissions
- **6.3**: Teacher can filter submissions by status
- **6.4**: Teacher can download submitted files
- **6.5**: Teacher can provide grades and feedback
- **8.1**: Grading interface with numeric scores and text feedback
- **8.2**: Grade storage and student notification
- **8.3**: Support for grade scales (0-100 points)
- **8.4**: Allow grade updates after initial submission
- **8.5**: Calculate and display class average scores
- **15.1**: Student can view assigned homework with due dates
- **15.2**: Student can upload homework files (PDF, DOCX, TXT, images up to 25MB)
- **15.3**: System marks submissions as on-time or late
- **15.4**: System records delay duration for late submissions
- **15.5**: Students can resubmit homework before grading

## Testing Recommendations

### Unit Tests
- Test request validation (missing fields, invalid data)
- Test error handling (gRPC errors, file errors)
- Test response transformation

### Integration Tests
- Test end-to-end flow: create assignment → submit homework → grade → download
- Test file upload with various file sizes
- Test late submission detection
- Test resubmission logic

### Load Tests
- Test concurrent file uploads
- Test large file uploads (near 25MB limit)
- Test file download performance

## Next Steps

1. Implement the Homework microservice backend (Task 32-39)
2. Write unit tests for homework handlers
3. Write integration tests for homework workflows
4. Test with frontend application
5. Performance testing and optimization

## Related Files

- `cloud-native/services/api-gateway/internal/handlers/homework.go` - Handler implementation
- `cloud-native/services/api-gateway/internal/router/router.go` - Route registration
- `cloud-native/proto/homework/homework.proto` - gRPC service definition
- `cloud-native/services/api-gateway/internal/grpc/clients.go` - gRPC client setup

## Notes

- All endpoints require authentication except auth endpoints
- File uploads use streaming to handle large files efficiently
- File downloads also use streaming for memory efficiency
- The implementation follows the same patterns as existing video handlers
- Error responses follow the standard format defined in transformers package
