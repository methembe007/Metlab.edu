package handler

import (
	"context"
	"fmt"

	"github.com/google/uuid"
	"github.com/metlab/analytics/internal/service"
	pb "metlab/proto-gen/go/analytics"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

// AnalyticsHandler implements the gRPC AnalyticsService interface
type AnalyticsHandler struct {
	pb.UnimplementedAnalyticsServiceServer
	analyticsService *service.AnalyticsService
}

// NewAnalyticsHandler creates a new analytics handler
func NewAnalyticsHandler(analyticsService *service.AnalyticsService) *AnalyticsHandler {
	return &AnalyticsHandler{
		analyticsService: analyticsService,
	}
}

// RecordLogin records a student login event
func (h *AnalyticsHandler) RecordLogin(ctx context.Context, req *pb.RecordLoginRequest) (*pb.RecordLoginResponse, error) {
	// Validate required fields
	if req.StudentId == "" {
		return nil, status.Error(codes.InvalidArgument, "student_id is required")
	}

	// Parse UUID
	studentID, err := uuid.Parse(req.StudentId)
	if err != nil {
		return nil, status.Error(codes.InvalidArgument, "invalid student_id format")
	}

	// Call service layer to record the login
	if err := h.analyticsService.RecordLogin(ctx, studentID, req.IpAddress, req.UserAgent); err != nil {
		return nil, status.Error(codes.Internal, fmt.Sprintf("failed to record login: %v", err))
	}

	return &pb.RecordLoginResponse{
		Success: true,
	}, nil
}

// GetStudentLoginStats retrieves login statistics for a student
func (h *AnalyticsHandler) GetStudentLoginStats(ctx context.Context, req *pb.GetStudentLoginStatsRequest) (*pb.LoginStatsResponse, error) {
	// Validate required fields
	if req.StudentId == "" {
		return nil, status.Error(codes.InvalidArgument, "student_id is required")
	}

	// Parse UUID
	studentID, err := uuid.Parse(req.StudentId)
	if err != nil {
		return nil, status.Error(codes.InvalidArgument, "invalid student_id format")
	}

	// Default to 30 days if not specified
	days := req.Days
	if days <= 0 {
		days = 30
	}

	// Call service layer
	dailyCounts, totalLogins, averagePerWeek, err := h.analyticsService.GetStudentLoginStats(ctx, studentID, days)
	if err != nil {
		return nil, status.Error(codes.Internal, fmt.Sprintf("failed to get student login stats: %v", err))
	}

	// Convert daily counts to proto format
	var protoDailyCounts []*pb.DailyLoginCount
	for _, dc := range dailyCounts {
		protoDailyCounts = append(protoDailyCounts, &pb.DailyLoginCount{
			Date:  dc.Date,
			Count: dc.Count,
		})
	}

	return &pb.LoginStatsResponse{
		DailyCounts:    protoDailyCounts,
		TotalLogins:    totalLogins,
		AveragePerWeek: averagePerWeek,
	}, nil
}

// GetClassEngagement retrieves engagement metrics for a class
func (h *AnalyticsHandler) GetClassEngagement(ctx context.Context, req *pb.GetClassEngagementRequest) (*pb.ClassEngagementResponse, error) {
	// Validate required fields
	if req.ClassId == "" {
		return nil, status.Error(codes.InvalidArgument, "class_id is required")
	}
	if req.TeacherId == "" {
		return nil, status.Error(codes.InvalidArgument, "teacher_id is required")
	}

	// Parse UUIDs
	classID, err := uuid.Parse(req.ClassId)
	if err != nil {
		return nil, status.Error(codes.InvalidArgument, "invalid class_id format")
	}

	teacherID, err := uuid.Parse(req.TeacherId)
	if err != nil {
		return nil, status.Error(codes.InvalidArgument, "invalid teacher_id format")
	}

	// Call service layer
	students, classStats, err := h.analyticsService.GetClassEngagement(ctx, classID, teacherID)
	if err != nil {
		return nil, status.Error(codes.Internal, fmt.Sprintf("failed to get class engagement: %v", err))
	}

	// Convert students to proto format
	var protoStudents []*pb.StudentEngagement
	for _, s := range students {
		protoStudents = append(protoStudents, &pb.StudentEngagement{
			StudentId:         s.StudentID.String(),
			StudentName:       s.StudentName,
			TotalLogins:       s.TotalLogins,
			VideosWatched:     s.VideosWatched,
			HomeworkSubmitted: s.HomeworkSubmitted,
			ChatMessages:      s.ChatMessages,
			EngagementScore:   s.EngagementScore,
		})
	}

	return &pb.ClassEngagementResponse{
		Students: protoStudents,
		ClassStats: &pb.ClassStats{
			AverageLogins:          classStats.AverageLogins,
			AverageVideosWatched:   classStats.AverageVideosWatched,
			HomeworkCompletionRate: classStats.HomeworkCompletionRate,
			TotalStudents:          classStats.TotalStudents,
		},
	}, nil
}

// RecordPDFDownload records a PDF download event
func (h *AnalyticsHandler) RecordPDFDownload(ctx context.Context, req *pb.RecordPDFDownloadRequest) (*pb.RecordPDFDownloadResponse, error) {
	// Validate required fields
	if req.PdfId == "" {
		return nil, status.Error(codes.InvalidArgument, "pdf_id is required")
	}
	if req.StudentId == "" {
		return nil, status.Error(codes.InvalidArgument, "student_id is required")
	}

	// Parse UUIDs
	pdfID, err := uuid.Parse(req.PdfId)
	if err != nil {
		return nil, status.Error(codes.InvalidArgument, "invalid pdf_id format")
	}

	studentID, err := uuid.Parse(req.StudentId)
	if err != nil {
		return nil, status.Error(codes.InvalidArgument, "invalid student_id format")
	}

	// Call service layer
	if err := h.analyticsService.RecordPDFDownload(ctx, pdfID, studentID); err != nil {
		return nil, status.Error(codes.Internal, fmt.Sprintf("failed to record PDF download: %v", err))
	}

	return &pb.RecordPDFDownloadResponse{
		Success: true,
	}, nil
}
