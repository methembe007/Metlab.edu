package handler

import (
	"context"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/metlab/homework/internal/models"
	"github.com/metlab/homework/internal/repository"
	"github.com/metlab/shared/errors"
	"github.com/metlab/shared/logger"
	pb "github.com/metlab/shared/proto-gen/go/homework"
	"github.com/metlab/shared/storage"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

// HomeworkHandler implements the HomeworkService gRPC service
type HomeworkHandler struct {
	pb.UnimplementedHomeworkServiceServer
	assignmentRepo *repository.AssignmentRepository
	submissionRepo *repository.SubmissionRepository
	gradeRepo      *repository.GradeRepository
	storageClient  *storage.S3Client
	logger         *logger.Logger
	maxUploadSize  int64
}

// NewHomeworkHandler creates a new homework handler
func NewHomeworkHandler(
	db *pgxpool.Pool,
	storageClient *storage.S3Client,
	log *logger.Logger,
	maxUploadSize int64,
) *HomeworkHandler {
	return &HomeworkHandler{
		assignmentRepo: repository.NewAssignmentRepository(db),
		submissionRepo: repository.NewSubmissionRepository(db),
		gradeRepo:      repository.NewGradeRepository(db),
		storageClient:  storageClient,
		logger:         log,
		maxUploadSize:  maxUploadSize,
	}
}

// CreateAssignment creates a new homework assignment
func (h *HomeworkHandler) CreateAssignment(ctx context.Context, req *pb.CreateAssignmentRequest) (*pb.Assignment, error) {
	h.logger.Info("Creating assignment", "teacher_id", req.TeacherId, "class_id", req.ClassId)
	
	// Validate request
	if req.TeacherId == "" {
		return nil, status.Error(codes.InvalidArgument, "teacher_id is required")
	}
	if req.ClassId == "" {
		return nil, status.Error(codes.InvalidArgument, "class_id is required")
	}
	if req.Title == "" {
		return nil, status.Error(codes.InvalidArgument, "title is required")
	}
	if req.DueDate <= 0 {
		return nil, status.Error(codes.InvalidArgument, "due_date is required")
	}
	if req.MaxScore <= 0 {
		return nil, status.Error(codes.InvalidArgument, "max_score must be greater than 0")
	}
	
	// Create assignment model
	assignment := &models.Assignment{
		TeacherID:   req.TeacherId,
		ClassID:     req.ClassId,
		Title:       req.Title,
		Description: req.Description,
		DueDate:     time.Unix(req.DueDate, 0),
		MaxScore:    req.MaxScore,
	}
	
	// Save to database
	if err := h.assignmentRepo.Create(ctx, assignment); err != nil {
		h.logger.Error("Failed to create assignment", err)
		return nil, status.Error(codes.Internal, "failed to create assignment")
	}
	
	h.logger.Info("Assignment created successfully", "assignment_id", assignment.ID)
	
	return &pb.Assignment{
		Id:              assignment.ID,
		Title:           assignment.Title,
		Description:     assignment.Description,
		DueDate:         assignment.DueDate.Unix(),
		MaxScore:        assignment.MaxScore,
		SubmissionCount: 0,
		GradedCount:     0,
		CreatedAt:       assignment.CreatedAt.Unix(),
	}, nil
}

// ListAssignments lists assignments for a class or teacher
func (h *HomeworkHandler) ListAssignments(ctx context.Context, req *pb.ListAssignmentsRequest) (*pb.ListAssignmentsResponse, error) {
	h.logger.Info("Listing assignments", "user_id", req.UserId, "class_id", req.ClassId, "role", req.Role)
	
	var assignments []*models.Assignment
	var err error
	
	if req.ClassId != "" {
		assignments, err = h.assignmentRepo.ListByClass(ctx, req.ClassId)
	} else if req.Role == "teacher" {
		assignments, err = h.assignmentRepo.ListByTeacher(ctx, req.UserId)
	} else {
		return nil, status.Error(codes.InvalidArgument, "either class_id or teacher role is required")
	}
	
	if err != nil {
		h.logger.Error("Failed to list assignments", err)
		return nil, status.Error(codes.Internal, "failed to list assignments")
	}
	
	// Convert to proto
	pbAssignments := make([]*pb.Assignment, len(assignments))
	for i, a := range assignments {
		pbAssignments[i] = &pb.Assignment{
			Id:              a.ID,
			Title:           a.Title,
			Description:     a.Description,
			DueDate:         a.DueDate.Unix(),
			MaxScore:        a.MaxScore,
			SubmissionCount: a.SubmissionCount,
			GradedCount:     a.GradedCount,
			CreatedAt:       a.CreatedAt.Unix(),
		}
	}
	
	return &pb.ListAssignmentsResponse{
		Assignments: pbAssignments,
	}, nil
}

// SubmitHomework handles homework submission with file upload
func (h *HomeworkHandler) SubmitHomework(stream pb.HomeworkService_SubmitHomeworkServer) error {
	h.logger.Info("Starting homework submission")
	
	var metadata *pb.SubmissionMetadata
	var assignmentID, studentID, filename string
	var fileSize int64
	var tempFile *os.File
	var err error
	
	// Receive first message with metadata
	req, err := stream.Recv()
	if err != nil {
		h.logger.Error("Failed to receive metadata", err)
		return status.Error(codes.Internal, "failed to receive metadata")
	}
	
	metadata = req.GetMetadata()
	if metadata == nil {
		return status.Error(codes.InvalidArgument, "first message must contain metadata")
	}
	
	assignmentID = metadata.AssignmentId
	studentID = metadata.StudentId
	filename = metadata.Filename
	fileSize = metadata.FileSize
	
	// Validate metadata
	if assignmentID == "" || studentID == "" || filename == "" {
		return status.Error(codes.InvalidArgument, "assignment_id, student_id, and filename are required")
	}
	
	if fileSize > h.maxUploadSize {
		return status.Error(codes.InvalidArgument, fmt.Sprintf("file size exceeds maximum of %d bytes", h.maxUploadSize))
	}
	
	// Create temporary file
	tempFile, err = os.CreateTemp("", "homework-*"+filepath.Ext(filename))
	if err != nil {
		h.logger.Error("Failed to create temp file", err)
		return status.Error(codes.Internal, "failed to create temp file")
	}
	defer os.Remove(tempFile.Name())
	defer tempFile.Close()
	
	// Receive file chunks
	var receivedSize int64
	for {
		req, err := stream.Recv()
		if err == io.EOF {
			break
		}
		if err != nil {
			h.logger.Error("Failed to receive chunk", err)
			return status.Error(codes.Internal, "failed to receive file chunk")
		}
		
		chunk := req.GetChunk()
		if chunk == nil {
			continue
		}
		
		n, err := tempFile.Write(chunk)
		if err != nil {
			h.logger.Error("Failed to write chunk", err)
			return status.Error(codes.Internal, "failed to write file chunk")
		}
		
		receivedSize += int64(n)
		if receivedSize > h.maxUploadSize {
			return status.Error(codes.InvalidArgument, "file size exceeds maximum")
		}
	}
	
	// Close temp file before uploading
	tempFile.Close()
	
	// Upload to S3
	storagePath := fmt.Sprintf("homework/%s/%s/%s", assignmentID, studentID, filename)
	if err := h.storageClient.UploadFile(context.Background(), tempFile.Name(), storagePath); err != nil {
		h.logger.Error("Failed to upload to storage", err)
		return status.Error(codes.Internal, "failed to upload file")
	}
	
	// Check if submission is late
	isLate, err := h.assignmentRepo.IsLate(context.Background(), assignmentID, time.Now())
	if err != nil {
		h.logger.Error("Failed to check if late", err)
		return status.Error(codes.Internal, "failed to check submission time")
	}
	
	// Create submission record
	submission := &models.Submission{
		AssignmentID:  assignmentID,
		StudentID:     studentID,
		FilePath:      storagePath,
		FileName:      filename,
		FileSizeBytes: receivedSize,
		IsLate:        isLate,
		Status:        models.StatusSubmitted,
	}
	
	if err := h.submissionRepo.Create(context.Background(), submission); err != nil {
		h.logger.Error("Failed to create submission", err)
		return status.Error(codes.Internal, "failed to create submission")
	}
	
	h.logger.Info("Homework submitted successfully", "submission_id", submission.ID)
	
	return stream.SendAndClose(&pb.SubmitHomeworkResponse{
		SubmissionId: submission.ID,
		IsLate:       isLate,
		Status:       submission.Status,
	})
}

// ListSubmissions lists submissions for an assignment
func (h *HomeworkHandler) ListSubmissions(ctx context.Context, req *pb.ListSubmissionsRequest) (*pb.ListSubmissionsResponse, error) {
	h.logger.Info("Listing submissions", "assignment_id", req.AssignmentId)
	
	if req.AssignmentId == "" {
		return nil, status.Error(codes.InvalidArgument, "assignment_id is required")
	}
	
	submissions, err := h.submissionRepo.ListByAssignment(ctx, req.AssignmentId, req.StatusFilter)
	if err != nil {
		h.logger.Error("Failed to list submissions", err)
		return nil, status.Error(codes.Internal, "failed to list submissions")
	}
	
	// Convert to proto
	pbSubmissions := make([]*pb.Submission, len(submissions))
	for i, s := range submissions {
		pbSub := &pb.Submission{
			Id:           s.ID,
			AssignmentId: s.AssignmentID,
			StudentId:    s.StudentID,
			StudentName:  s.StudentName,
			Filename:     s.FileName,
			SubmittedAt:  s.SubmittedAt.Unix(),
			IsLate:       s.IsLate,
			Status:       s.Status,
		}
		
		if s.Grade != nil {
			pbSub.Grade = &pb.Grade{
				Score:    s.Grade.Score,
				Feedback: s.Grade.Feedback,
				GradedAt: s.Grade.GradedAt.Unix(),
				GradedBy: s.Grade.GradedBy,
			}
		}
		
		pbSubmissions[i] = pbSub
	}
	
	return &pb.ListSubmissionsResponse{
		Submissions: pbSubmissions,
	}, nil
}

// GradeSubmission grades a homework submission
func (h *HomeworkHandler) GradeSubmission(ctx context.Context, req *pb.GradeSubmissionRequest) (*pb.GradeSubmissionResponse, error) {
	h.logger.Info("Grading submission", "submission_id", req.SubmissionId, "teacher_id", req.TeacherId)
	
	// Validate request
	if req.SubmissionId == "" {
		return nil, status.Error(codes.InvalidArgument, "submission_id is required")
	}
	if req.TeacherId == "" {
		return nil, status.Error(codes.InvalidArgument, "teacher_id is required")
	}
	if req.Score < 0 {
		return nil, status.Error(codes.InvalidArgument, "score must be non-negative")
	}
	
	// Get submission to validate it exists
	submission, err := h.submissionRepo.GetByID(ctx, req.SubmissionId)
	if err != nil {
		h.logger.Error("Failed to get submission", err)
		return nil, status.Error(codes.NotFound, "submission not found")
	}
	
	// Create or update grade
	grade := &models.Grade{
		SubmissionID: req.SubmissionId,
		Score:        req.Score,
		Feedback:     req.Feedback,
		GradedBy:     req.TeacherId,
	}
	
	if err := h.gradeRepo.Create(ctx, grade); err != nil {
		h.logger.Error("Failed to create grade", err)
		return nil, status.Error(codes.Internal, "failed to create grade")
	}
	
	// Update submission status
	if err := h.submissionRepo.UpdateStatus(ctx, req.SubmissionId, models.StatusGraded); err != nil {
		h.logger.Error("Failed to update submission status", err)
		return nil, status.Error(codes.Internal, "failed to update submission status")
	}
	
	h.logger.Info("Submission graded successfully", "submission_id", submission.ID, "score", grade.Score)
	
	return &pb.GradeSubmissionResponse{
		Success: true,
		Grade: &pb.Grade{
			Score:    grade.Score,
			Feedback: grade.Feedback,
			GradedAt: grade.GradedAt.Unix(),
			GradedBy: grade.GradedBy,
		},
	}, nil
}

// GetSubmissionFile streams a submission file for download
func (h *HomeworkHandler) GetSubmissionFile(req *pb.GetSubmissionFileRequest, stream pb.HomeworkService_GetSubmissionFileServer) error {
	h.logger.Info("Getting submission file", "submission_id", req.SubmissionId)
	
	if req.SubmissionId == "" {
		return status.Error(codes.InvalidArgument, "submission_id is required")
	}
	
	// Get submission
	submission, err := h.submissionRepo.GetByID(context.Background(), req.SubmissionId)
	if err != nil {
		h.logger.Error("Failed to get submission", err)
		return status.Error(codes.NotFound, "submission not found")
	}
	
	// Download from S3 to temp file
	tempFile, err := os.CreateTemp("", "download-*")
	if err != nil {
		h.logger.Error("Failed to create temp file", err)
		return status.Error(codes.Internal, "failed to create temp file")
	}
	defer os.Remove(tempFile.Name())
	defer tempFile.Close()
	
	if err := h.storageClient.DownloadFile(context.Background(), submission.FilePath, tempFile.Name()); err != nil {
		h.logger.Error("Failed to download from storage", err)
		return status.Error(codes.Internal, "failed to download file")
	}
	
	// Seek to beginning
	if _, err := tempFile.Seek(0, 0); err != nil {
		h.logger.Error("Failed to seek file", err)
		return status.Error(codes.Internal, "failed to read file")
	}
	
	// Stream file chunks
	buffer := make([]byte, 64*1024) // 64KB chunks
	for {
		n, err := tempFile.Read(buffer)
		if err == io.EOF {
			break
		}
		if err != nil {
			h.logger.Error("Failed to read file", err)
			return status.Error(codes.Internal, "failed to read file")
		}
		
		if err := stream.Send(&pb.FileChunk{Data: buffer[:n]}); err != nil {
			h.logger.Error("Failed to send chunk", err)
			return status.Error(codes.Internal, "failed to send file chunk")
		}
	}
	
	h.logger.Info("File streamed successfully", "submission_id", submission.ID)
	return nil
}
