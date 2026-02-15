package handlers

import (
	"context"
	"io"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/metlab/api-gateway/internal/transformers"
	homeworkpb "github.com/metlab/shared/proto-gen/go/homework"
)

// CreateAssignmentRequest represents the HTTP request for creating an assignment
type CreateAssignmentRequest struct {
	TeacherID   string `json:"teacher_id"`
	ClassID     string `json:"class_id"`
	Title       string `json:"title"`
	Description string `json:"description"`
	DueDate     int64  `json:"due_date"`
	MaxScore    int32  `json:"max_score"`
}

// AssignmentResponse represents an assignment in HTTP responses
type AssignmentResponse struct {
	ID              string `json:"id"`
	Title           string `json:"title"`
	Description     string `json:"description"`
	DueDate         int64  `json:"due_date"`
	MaxScore        int32  `json:"max_score"`
	SubmissionCount int32  `json:"submission_count"`
	GradedCount     int32  `json:"graded_count"`
	CreatedAt       int64  `json:"created_at"`
}

// ListAssignmentsResponse represents the HTTP response for listing assignments
type ListAssignmentsResponse struct {
	Assignments []AssignmentResponse `json:"assignments"`
}

// SubmitHomeworkRequest represents the HTTP request for homework submission
type SubmitHomeworkRequest struct {
	AssignmentID string `json:"assignment_id"`
	StudentID    string `json:"student_id"`
	Filename     string `json:"filename"`
	FileSize     int64  `json:"file_size"`
}

// SubmitHomeworkResponse represents the HTTP response for homework submission
type SubmitHomeworkResponse struct {
	SubmissionID string `json:"submission_id"`
	IsLate       bool   `json:"is_late"`
	Status       string `json:"status"`
}

// SubmissionResponse represents a submission in HTTP responses
type SubmissionResponse struct {
	ID           string        `json:"id"`
	AssignmentID string        `json:"assignment_id"`
	StudentID    string        `json:"student_id"`
	StudentName  string        `json:"student_name"`
	Filename     string        `json:"filename"`
	SubmittedAt  int64         `json:"submitted_at"`
	IsLate       bool          `json:"is_late"`
	Status       string        `json:"status"`
	Grade        *GradeDetails `json:"grade,omitempty"`
}

// GradeDetails represents grade information
type GradeDetails struct {
	Score     int32  `json:"score"`
	Feedback  string `json:"feedback"`
	GradedAt  int64  `json:"graded_at"`
	GradedBy  string `json:"graded_by"`
}

// ListSubmissionsResponse represents the HTTP response for listing submissions
type ListSubmissionsResponse struct {
	Submissions []SubmissionResponse `json:"submissions"`
}

// GradeSubmissionRequest represents the HTTP request for grading a submission
type GradeSubmissionRequest struct {
	Score    int32  `json:"score"`
	Feedback string `json:"feedback"`
}

// GradeSubmissionResponse represents the HTTP response for grading
type GradeSubmissionResponse struct {
	Success bool          `json:"success"`
	Grade   *GradeDetails `json:"grade"`
}

// CreateAssignment handles POST /api/homework/assignments
func (h *Handler) CreateAssignment(w http.ResponseWriter, r *http.Request) {
	// Get user ID from context (set by auth middleware)
	userID, ok := r.Context().Value("user_id").(string)
	if !ok || userID == "" {
		transformers.WriteError(w, http.StatusUnauthorized, "UNAUTHORIZED", "User ID not found in context")
		return
	}

	// Decode request
	var req CreateAssignmentRequest
	if err := transformers.DecodeJSONRequest(r, &req); err != nil {
		transformers.WriteError(w, http.StatusBadRequest, "INVALID_REQUEST", "Invalid request body")
		return
	}

	// Validate required fields
	if req.TeacherID == "" || req.ClassID == "" || req.Title == "" {
		transformers.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "teacher_id, class_id, and title are required")
		return
	}

	if req.DueDate <= 0 {
		transformers.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "due_date must be a valid timestamp")
		return
	}

	if req.MaxScore <= 0 {
		req.MaxScore = 100 // Default to 100 if not provided
	}

	// Call gRPC service
	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()

	grpcReq := &homeworkpb.CreateAssignmentRequest{
		TeacherId:   req.TeacherID,
		ClassId:     req.ClassID,
		Title:       req.Title,
		Description: req.Description,
		DueDate:     req.DueDate,
		MaxScore:    req.MaxScore,
	}

	resp, err := h.clients.Homework.CreateAssignment(ctx, grpcReq)
	if err != nil {
		transformers.HandleGRPCError(w, err)
		return
	}

	// Transform response
	httpResp := AssignmentResponse{
		ID:              resp.Id,
		Title:           resp.Title,
		Description:     resp.Description,
		DueDate:         resp.DueDate,
		MaxScore:        resp.MaxScore,
		SubmissionCount: resp.SubmissionCount,
		GradedCount:     resp.GradedCount,
		CreatedAt:       resp.CreatedAt,
	}

	transformers.EncodeJSONResponse(w, http.StatusCreated, httpResp)
}

// ListAssignments handles GET /api/homework/assignments
func (h *Handler) ListAssignments(w http.ResponseWriter, r *http.Request) {
	// Get user ID from context
	userID, ok := r.Context().Value("user_id").(string)
	if !ok || userID == "" {
		transformers.WriteError(w, http.StatusUnauthorized, "UNAUTHORIZED", "User ID not found in context")
		return
	}

	// Get query parameters
	classID := r.URL.Query().Get("class_id")
	if classID == "" {
		transformers.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "class_id is required")
		return
	}

	role := r.URL.Query().Get("role")
	if role == "" {
		// Try to get role from context if available
		if roleVal, ok := r.Context().Value("role").(string); ok {
			role = roleVal
		} else {
			role = "student" // Default to student
		}
	}

	// Call gRPC service
	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()

	grpcReq := &homeworkpb.ListAssignmentsRequest{
		UserId:  userID,
		ClassId: classID,
		Role:    role,
	}

	resp, err := h.clients.Homework.ListAssignments(ctx, grpcReq)
	if err != nil {
		transformers.HandleGRPCError(w, err)
		return
	}

	// Transform response
	assignments := make([]AssignmentResponse, len(resp.Assignments))
	for i, a := range resp.Assignments {
		assignments[i] = AssignmentResponse{
			ID:              a.Id,
			Title:           a.Title,
			Description:     a.Description,
			DueDate:         a.DueDate,
			MaxScore:        a.MaxScore,
			SubmissionCount: a.SubmissionCount,
			GradedCount:     a.GradedCount,
			CreatedAt:       a.CreatedAt,
		}
	}

	httpResp := ListAssignmentsResponse{
		Assignments: assignments,
	}

	transformers.EncodeJSONResponse(w, http.StatusOK, httpResp)
}

// SubmitHomework handles POST /api/homework/submissions
func (h *Handler) SubmitHomework(w http.ResponseWriter, r *http.Request) {
	// Get user ID from context
	userID, ok := r.Context().Value("user_id").(string)
	if !ok || userID == "" {
		transformers.WriteError(w, http.StatusUnauthorized, "UNAUTHORIZED", "User ID not found in context")
		return
	}

	// Parse multipart form
	err := r.ParseMultipartForm(25 << 20) // 25MB max
	if err != nil {
		transformers.WriteError(w, http.StatusBadRequest, "INVALID_REQUEST", "Failed to parse multipart form")
		return
	}

	// Get form fields
	assignmentID := r.FormValue("assignment_id")
	studentID := r.FormValue("student_id")

	// Validate required fields
	if assignmentID == "" || studentID == "" {
		transformers.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "assignment_id and student_id are required")
		return
	}

	// Get file from form
	file, header, err := r.FormFile("file")
	if err != nil {
		transformers.WriteError(w, http.StatusBadRequest, "INVALID_REQUEST", "file is required")
		return
	}
	defer file.Close()

	// Call gRPC streaming service
	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Minute) // Long timeout for large uploads
	defer cancel()

	stream, err := h.clients.Homework.SubmitHomework(ctx)
	if err != nil {
		transformers.HandleGRPCError(w, err)
		return
	}

	// Send metadata first
	metadataReq := &homeworkpb.SubmitHomeworkRequest{
		Data: &homeworkpb.SubmitHomeworkRequest_Metadata{
			Metadata: &homeworkpb.SubmissionMetadata{
				AssignmentId: assignmentID,
				StudentId:    studentID,
				Filename:     header.Filename,
				FileSize:     header.Size,
			},
		},
	}

	if err := stream.Send(metadataReq); err != nil {
		transformers.HandleGRPCError(w, err)
		return
	}

	// Stream file chunks
	buffer := make([]byte, 1024*1024) // 1MB chunks
	for {
		n, err := file.Read(buffer)
		if err == io.EOF {
			break
		}
		if err != nil {
			transformers.WriteError(w, http.StatusInternalServerError, "UPLOAD_ERROR", "Failed to read file")
			return
		}

		chunkReq := &homeworkpb.SubmitHomeworkRequest{
			Data: &homeworkpb.SubmitHomeworkRequest_Chunk{
				Chunk: buffer[:n],
			},
		}

		if err := stream.Send(chunkReq); err != nil {
			transformers.HandleGRPCError(w, err)
			return
		}
	}

	// Close stream and get response
	resp, err := stream.CloseAndRecv()
	if err != nil {
		transformers.HandleGRPCError(w, err)
		return
	}

	// Transform and return response
	httpResp := SubmitHomeworkResponse{
		SubmissionID: resp.SubmissionId,
		IsLate:       resp.IsLate,
		Status:       resp.Status,
	}

	transformers.EncodeJSONResponse(w, http.StatusCreated, httpResp)
}

// ListSubmissions handles GET /api/homework/submissions
func (h *Handler) ListSubmissions(w http.ResponseWriter, r *http.Request) {
	// Get user ID from context
	userID, ok := r.Context().Value("user_id").(string)
	if !ok || userID == "" {
		transformers.WriteError(w, http.StatusUnauthorized, "UNAUTHORIZED", "User ID not found in context")
		return
	}

	// Get query parameters
	assignmentID := r.URL.Query().Get("assignment_id")
	if assignmentID == "" {
		transformers.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "assignment_id is required")
		return
	}

	statusFilter := r.URL.Query().Get("status")

	// Call gRPC service
	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()

	grpcReq := &homeworkpb.ListSubmissionsRequest{
		AssignmentId: assignmentID,
		TeacherId:    userID,
		StatusFilter: statusFilter,
	}

	resp, err := h.clients.Homework.ListSubmissions(ctx, grpcReq)
	if err != nil {
		transformers.HandleGRPCError(w, err)
		return
	}

	// Transform response
	submissions := make([]SubmissionResponse, len(resp.Submissions))
	for i, s := range resp.Submissions {
		submission := SubmissionResponse{
			ID:           s.Id,
			AssignmentID: s.AssignmentId,
			StudentID:    s.StudentId,
			StudentName:  s.StudentName,
			Filename:     s.Filename,
			SubmittedAt:  s.SubmittedAt,
			IsLate:       s.IsLate,
			Status:       s.Status,
		}

		// Add grade if present
		if s.Grade != nil {
			submission.Grade = &GradeDetails{
				Score:    s.Grade.Score,
				Feedback: s.Grade.Feedback,
				GradedAt: s.Grade.GradedAt,
				GradedBy: s.Grade.GradedBy,
			}
		}

		submissions[i] = submission
	}

	httpResp := ListSubmissionsResponse{
		Submissions: submissions,
	}

	transformers.EncodeJSONResponse(w, http.StatusOK, httpResp)
}

// GradeSubmission handles POST /api/homework/submissions/:id/grade
func (h *Handler) GradeSubmission(w http.ResponseWriter, r *http.Request) {
	// Get user ID from context
	userID, ok := r.Context().Value("user_id").(string)
	if !ok || userID == "" {
		transformers.WriteError(w, http.StatusUnauthorized, "UNAUTHORIZED", "User ID not found in context")
		return
	}

	// Get submission ID from URL
	submissionID := chi.URLParam(r, "id")
	if submissionID == "" {
		transformers.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "submission ID is required")
		return
	}

	// Decode request
	var req GradeSubmissionRequest
	if err := transformers.DecodeJSONRequest(r, &req); err != nil {
		transformers.WriteError(w, http.StatusBadRequest, "INVALID_REQUEST", "Invalid request body")
		return
	}

	// Validate score
	if req.Score < 0 {
		transformers.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "score must be non-negative")
		return
	}

	// Call gRPC service
	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()

	grpcReq := &homeworkpb.GradeSubmissionRequest{
		SubmissionId: submissionID,
		TeacherId:    userID,
		Score:        req.Score,
		Feedback:     req.Feedback,
	}

	resp, err := h.clients.Homework.GradeSubmission(ctx, grpcReq)
	if err != nil {
		transformers.HandleGRPCError(w, err)
		return
	}

	// Transform response
	var gradeDetails *GradeDetails
	if resp.Grade != nil {
		gradeDetails = &GradeDetails{
			Score:    resp.Grade.Score,
			Feedback: resp.Grade.Feedback,
			GradedAt: resp.Grade.GradedAt,
			GradedBy: resp.Grade.GradedBy,
		}
	}

	httpResp := GradeSubmissionResponse{
		Success: resp.Success,
		Grade:   gradeDetails,
	}

	transformers.EncodeJSONResponse(w, http.StatusOK, httpResp)
}

// GetSubmissionFile handles GET /api/homework/submissions/:id/file
func (h *Handler) GetSubmissionFile(w http.ResponseWriter, r *http.Request) {
	// Get user ID from context
	userID, ok := r.Context().Value("user_id").(string)
	if !ok || userID == "" {
		transformers.WriteError(w, http.StatusUnauthorized, "UNAUTHORIZED", "User ID not found in context")
		return
	}

	// Get submission ID from URL
	submissionID := chi.URLParam(r, "id")
	if submissionID == "" {
		transformers.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "submission ID is required")
		return
	}

	// Call gRPC streaming service
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Minute)
	defer cancel()

	grpcReq := &homeworkpb.GetSubmissionFileRequest{
		SubmissionId: submissionID,
		TeacherId:    userID,
	}

	stream, err := h.clients.Homework.GetSubmissionFile(ctx, grpcReq)
	if err != nil {
		transformers.HandleGRPCError(w, err)
		return
	}

	// Set headers for file download
	w.Header().Set("Content-Type", "application/octet-stream")
	w.Header().Set("Content-Disposition", "attachment")

	// Stream file chunks to response
	for {
		chunk, err := stream.Recv()
		if err == io.EOF {
			break
		}
		if err != nil {
			// Can't write error response after starting to stream
			return
		}

		if _, err := w.Write(chunk.Data); err != nil {
			return
		}
	}
}
