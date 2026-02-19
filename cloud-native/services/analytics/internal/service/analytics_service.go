package service

import (
	"context"
	"fmt"

	"github.com/google/uuid"
	"github.com/metlab/analytics/internal/models"
	"github.com/metlab/analytics/internal/repository"
)

// AnalyticsService handles business logic for analytics operations
type AnalyticsService struct {
	loginRepo      *repository.LoginRepository
	pdfRepo        *repository.PDFRepository
	engagementRepo *repository.EngagementRepository
}

// NewAnalyticsService creates a new analytics service
func NewAnalyticsService(
	loginRepo *repository.LoginRepository,
	pdfRepo *repository.PDFRepository,
	engagementRepo *repository.EngagementRepository,
) *AnalyticsService {
	return &AnalyticsService{
		loginRepo:      loginRepo,
		pdfRepo:        pdfRepo,
		engagementRepo: engagementRepo,
	}
}

// RecordLogin records a student login event
func (s *AnalyticsService) RecordLogin(ctx context.Context, studentID uuid.UUID, ipAddress, userAgent string) error {
	if err := s.loginRepo.RecordLogin(ctx, studentID, ipAddress, userAgent); err != nil {
		return fmt.Errorf("failed to record login: %w", err)
	}
	return nil
}

// GetStudentLoginStats retrieves login statistics for a student
func (s *AnalyticsService) GetStudentLoginStats(ctx context.Context, studentID uuid.UUID, days int32) ([]models.DailyLoginCount, int32, float64, error) {
	if days <= 0 {
		days = 30 // Default to 30 days
	}

	dailyCounts, totalLogins, averagePerWeek, err := s.loginRepo.GetStudentLoginStats(ctx, studentID, days)
	if err != nil {
		return nil, 0, 0, fmt.Errorf("failed to get student login stats: %w", err)
	}

	return dailyCounts, totalLogins, averagePerWeek, nil
}

// RecordPDFDownload records a PDF download event
func (s *AnalyticsService) RecordPDFDownload(ctx context.Context, pdfID, studentID uuid.UUID) error {
	if err := s.pdfRepo.RecordPDFDownload(ctx, pdfID, studentID); err != nil {
		return fmt.Errorf("failed to record PDF download: %w", err)
	}
	return nil
}

// GetClassEngagement retrieves engagement metrics for a class
func (s *AnalyticsService) GetClassEngagement(ctx context.Context, classID, teacherID uuid.UUID) ([]models.StudentEngagement, models.ClassStats, error) {
	students, classStats, err := s.engagementRepo.GetClassEngagement(ctx, classID, teacherID)
	if err != nil {
		return nil, models.ClassStats{}, fmt.Errorf("failed to get class engagement: %w", err)
	}

	return students, classStats, nil
}
