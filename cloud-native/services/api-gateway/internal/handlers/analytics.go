package handlers

import (
	"context"
	"net/http"
	"strconv"
	"time"

	"github.com/metlab/api-gateway/internal/transformers"
	analyticspb "github.com/metlab/shared/proto-gen/go/analytics"
)

// DailyLoginCountResponse represents daily login count data
type DailyLoginCountResponse struct {
	Date  string `json:"date"`
	Count int32  `json:"count"`
}

// LoginStatsResponse represents the HTTP response for login statistics
type LoginStatsResponse struct {
	DailyCounts    []DailyLoginCountResponse `json:"daily_counts"`
	TotalLogins    int32                     `json:"total_logins"`
	AveragePerWeek float64                   `json:"average_per_week"`
}

// StudentEngagementResponse represents student engagement data
type StudentEngagementResponse struct {
	StudentID        string  `json:"student_id"`
	StudentName      string  `json:"student_name"`
	TotalLogins      int32   `json:"total_logins"`
	VideosWatched    int32   `json:"videos_watched"`
	HomeworkSubmitted int32  `json:"homework_submitted"`
	ChatMessages     int32   `json:"chat_messages"`
	EngagementScore  float64 `json:"engagement_score"`
}

// ClassStatsResponse represents class-wide statistics
type ClassStatsResponse struct {
	AverageLogins           float64 `json:"average_logins"`
	AverageVideosWatched    float64 `json:"average_videos_watched"`
	HomeworkCompletionRate  float64 `json:"homework_completion_rate"`
	TotalStudents           int32   `json:"total_students"`
}

// ClassEngagementResponse represents the HTTP response for class engagement
type ClassEngagementResponse struct {
	Students   []StudentEngagementResponse `json:"students"`
	ClassStats ClassStatsResponse          `json:"class_stats"`
}

// GetLoginStats handles GET /api/analytics/login-stats
func (h *Handler) GetLoginStats(w http.ResponseWriter, r *http.Request) {
	// Get user ID from context
	userID, ok := r.Context().Value("user_id").(string)
	if !ok || userID == "" {
		transformers.WriteError(w, http.StatusUnauthorized, "UNAUTHORIZED", "User ID not found in context")
		return
	}

	// Get query parameters
	studentID := r.URL.Query().Get("student_id")
	if studentID == "" {
		// If not provided, use the authenticated user's ID
		studentID = userID
	}

	// Get days parameter (default to 30)
	days := int32(30)
	if daysStr := r.URL.Query().Get("days"); daysStr != "" {
		if d, err := strconv.Atoi(daysStr); err == nil && d > 0 && d <= 365 {
			days = int32(d)
		}
	}

	// Call gRPC service
	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()

	grpcReq := &analyticspb.GetStudentLoginStatsRequest{
		StudentId: studentID,
		Days:      days,
	}

	resp, err := h.clients.Analytics.GetStudentLoginStats(ctx, grpcReq)
	if err != nil {
		transformers.HandleGRPCError(w, err)
		return
	}

	// Transform response
	dailyCounts := make([]DailyLoginCountResponse, len(resp.DailyCounts))
	for i, dc := range resp.DailyCounts {
		dailyCounts[i] = DailyLoginCountResponse{
			Date:  dc.Date,
			Count: dc.Count,
		}
	}

	httpResp := LoginStatsResponse{
		DailyCounts:    dailyCounts,
		TotalLogins:    resp.TotalLogins,
		AveragePerWeek: resp.AveragePerWeek,
	}

	transformers.EncodeJSONResponse(w, http.StatusOK, httpResp)
}

// GetClassEngagement handles GET /api/analytics/class-engagement
func (h *Handler) GetClassEngagement(w http.ResponseWriter, r *http.Request) {
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

	teacherID := r.URL.Query().Get("teacher_id")
	if teacherID == "" {
		// If not provided, use the authenticated user's ID (assuming they're a teacher)
		teacherID = userID
	}

	// Call gRPC service
	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()

	grpcReq := &analyticspb.GetClassEngagementRequest{
		ClassId:   classID,
		TeacherId: teacherID,
	}

	resp, err := h.clients.Analytics.GetClassEngagement(ctx, grpcReq)
	if err != nil {
		transformers.HandleGRPCError(w, err)
		return
	}

	// Transform response
	students := make([]StudentEngagementResponse, len(resp.Students))
	for i, s := range resp.Students {
		students[i] = StudentEngagementResponse{
			StudentID:        s.StudentId,
			StudentName:      s.StudentName,
			TotalLogins:      s.TotalLogins,
			VideosWatched:    s.VideosWatched,
			HomeworkSubmitted: s.HomeworkSubmitted,
			ChatMessages:     s.ChatMessages,
			EngagementScore:  s.EngagementScore,
		}
	}

	classStats := ClassStatsResponse{
		AverageLogins:          resp.ClassStats.AverageLogins,
		AverageVideosWatched:   resp.ClassStats.AverageVideosWatched,
		HomeworkCompletionRate: resp.ClassStats.HomeworkCompletionRate,
		TotalStudents:          resp.ClassStats.TotalStudents,
	}

	httpResp := ClassEngagementResponse{
		Students:   students,
		ClassStats: classStats,
	}

	transformers.EncodeJSONResponse(w, http.StatusOK, httpResp)
}

// RecordLogin handles POST /api/analytics/login (internal use, typically called by auth middleware)
func (h *Handler) RecordLogin(w http.ResponseWriter, r *http.Request) {
	// Get user ID from context
	userID, ok := r.Context().Value("user_id").(string)
	if !ok || userID == "" {
		transformers.WriteError(w, http.StatusUnauthorized, "UNAUTHORIZED", "User ID not found in context")
		return
	}

	// Get IP address and user agent
	ipAddress := r.RemoteAddr
	if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
		ipAddress = xff
	} else if xri := r.Header.Get("X-Real-IP"); xri != "" {
		ipAddress = xri
	}

	userAgent := r.UserAgent()

	// Call gRPC service
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	grpcReq := &analyticspb.RecordLoginRequest{
		StudentId: userID,
		IpAddress: ipAddress,
		UserAgent: userAgent,
	}

	resp, err := h.clients.Analytics.RecordLogin(ctx, grpcReq)
	if err != nil {
		transformers.HandleGRPCError(w, err)
		return
	}

	// Return success response
	transformers.EncodeJSONResponse(w, http.StatusOK, map[string]bool{
		"success": resp.Success,
	})
}
