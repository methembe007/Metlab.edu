package handlers

import (
	"context"
	"io"
	"net/http"
	"strconv"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/metlab/api-gateway/internal/transformers"
	videopb "github.com/metlab/shared/proto-gen/go/video"
)

// ListVideosRequest represents the HTTP request for listing videos
type ListVideosRequest struct {
	ClassID  string `json:"class_id"`
	Page     int32  `json:"page"`
	PageSize int32  `json:"page_size"`
}

// UploadVideoRequest represents the HTTP request for video upload
type UploadVideoRequest struct {
	TeacherID   string `json:"teacher_id"`
	ClassID     string `json:"class_id"`
	Title       string `json:"title"`
	Description string `json:"description"`
	Filename    string `json:"filename"`
	FileSize    int64  `json:"file_size"`
}

// RecordViewRequest represents the HTTP request for recording video views
type RecordViewRequest struct {
	PositionSeconds      int32 `json:"position_seconds"`
	WatchDurationSeconds int32 `json:"watch_duration_seconds"`
	Completed            bool  `json:"completed"`
}

// VideoResponse represents a video in HTTP responses
type VideoResponse struct {
	ID              string          `json:"id"`
	Title           string          `json:"title"`
	Description     string          `json:"description"`
	DurationSeconds int32           `json:"duration_seconds"`
	ThumbnailURL    string          `json:"thumbnail_url"`
	Status          string          `json:"status"`
	CreatedAt       int64           `json:"created_at"`
	Variants        []VideoVariant  `json:"variants,omitempty"`
}

// VideoVariant represents a video variant
type VideoVariant struct {
	Resolution  string `json:"resolution"`
	BitrateKbps int32  `json:"bitrate_kbps"`
	StoragePath string `json:"storage_path"`
}

// ListVideosResponse represents the HTTP response for listing videos
type ListVideosResponse struct {
	Videos     []VideoResponse `json:"videos"`
	TotalCount int32           `json:"total_count"`
}

// UploadVideoResponse represents the HTTP response for video upload
type UploadVideoResponse struct {
	VideoID string `json:"video_id"`
	Status  string `json:"status"`
}

// StreamingURLResponse represents the HTTP response for streaming URL
type StreamingURLResponse struct {
	URL         string `json:"url"`
	ExpiresAt   int64  `json:"expires_at"`
	ManifestURL string `json:"manifest_url"`
}

// RecordViewResponse represents the HTTP response for recording views
type RecordViewResponse struct {
	Success bool `json:"success"`
}

// VideoAnalyticsResponse represents the HTTP response for video analytics
type VideoAnalyticsResponse struct {
	VideoID      string              `json:"video_id"`
	TotalViews   int32               `json:"total_views"`
	StudentViews []StudentViewData   `json:"student_views"`
}

// StudentViewData represents student viewing data
type StudentViewData struct {
	StudentID         string `json:"student_id"`
	StudentName       string `json:"student_name"`
	PercentageWatched int32  `json:"percentage_watched"`
	TotalWatchSeconds int32  `json:"total_watch_seconds"`
	Completed         bool   `json:"completed"`
	LastViewedAt      int64  `json:"last_viewed_at"`
}

// ListVideos handles GET /api/videos
func (h *Handler) ListVideos(w http.ResponseWriter, r *http.Request) {
	// Get user ID from context (set by auth middleware)
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

	page := int32(1)
	if pageStr := r.URL.Query().Get("page"); pageStr != "" {
		if p, err := strconv.Atoi(pageStr); err == nil && p > 0 {
			page = int32(p)
		}
	}

	pageSize := int32(20)
	if pageSizeStr := r.URL.Query().Get("page_size"); pageSizeStr != "" {
		if ps, err := strconv.Atoi(pageSizeStr); err == nil && ps > 0 && ps <= 100 {
			pageSize = int32(ps)
		}
	}

	// Call gRPC service
	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()

	grpcReq := &videopb.ListVideosRequest{
		UserId:   userID,
		ClassId:  classID,
		Page:     page,
		PageSize: pageSize,
	}

	resp, err := h.clients.Video.ListVideos(ctx, grpcReq)
	if err != nil {
		transformers.HandleGRPCError(w, err)
		return
	}

	// Transform response
	videos := make([]VideoResponse, len(resp.Videos))
	for i, v := range resp.Videos {
		videos[i] = VideoResponse{
			ID:              v.Id,
			Title:           v.Title,
			Description:     v.Description,
			DurationSeconds: v.DurationSeconds,
			ThumbnailURL:    v.ThumbnailUrl,
			Status:          v.Status,
			CreatedAt:       v.CreatedAt,
		}
	}

	httpResp := ListVideosResponse{
		Videos:     videos,
		TotalCount: resp.TotalCount,
	}

	transformers.EncodeJSONResponse(w, http.StatusOK, httpResp)
}

// UploadVideo handles POST /api/videos
func (h *Handler) UploadVideo(w http.ResponseWriter, r *http.Request) {
	// Get user ID from context
	userID, ok := r.Context().Value("user_id").(string)
	if !ok || userID == "" {
		transformers.WriteError(w, http.StatusUnauthorized, "UNAUTHORIZED", "User ID not found in context")
		return
	}

	// Parse multipart form
	err := r.ParseMultipartForm(2 << 30) // 2GB max
	if err != nil {
		transformers.WriteError(w, http.StatusBadRequest, "INVALID_REQUEST", "Failed to parse multipart form")
		return
	}

	// Get form fields
	teacherID := r.FormValue("teacher_id")
	classID := r.FormValue("class_id")
	title := r.FormValue("title")
	description := r.FormValue("description")

	// Validate required fields
	if teacherID == "" || classID == "" || title == "" {
		transformers.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "teacher_id, class_id, and title are required")
		return
	}

	// Get file from form
	file, header, err := r.FormFile("video")
	if err != nil {
		transformers.WriteError(w, http.StatusBadRequest, "INVALID_REQUEST", "video file is required")
		return
	}
	defer file.Close()

	// Call gRPC streaming service
	ctx, cancel := context.WithTimeout(r.Context(), 30*time.Minute) // Long timeout for large uploads
	defer cancel()

	stream, err := h.clients.Video.UploadVideo(ctx)
	if err != nil {
		transformers.HandleGRPCError(w, err)
		return
	}

	// Send metadata first
	metadataReq := &videopb.UploadVideoRequest{
		Data: &videopb.UploadVideoRequest_Metadata{
			Metadata: &videopb.VideoMetadata{
				TeacherId:   teacherID,
				ClassId:     classID,
				Title:       title,
				Description: description,
				Filename:    header.Filename,
				FileSize:    header.Size,
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

		chunkReq := &videopb.UploadVideoRequest{
			Data: &videopb.UploadVideoRequest_Chunk{
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
	httpResp := UploadVideoResponse{
		VideoID: resp.VideoId,
		Status:  resp.Status,
	}

	transformers.EncodeJSONResponse(w, http.StatusCreated, httpResp)
}

// GetVideo handles GET /api/videos/:id
func (h *Handler) GetVideo(w http.ResponseWriter, r *http.Request) {
	// Get user ID from context
	userID, ok := r.Context().Value("user_id").(string)
	if !ok || userID == "" {
		transformers.WriteError(w, http.StatusUnauthorized, "UNAUTHORIZED", "User ID not found in context")
		return
	}

	// Get video ID from URL
	videoID := chi.URLParam(r, "id")
	if videoID == "" {
		transformers.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "video ID is required")
		return
	}

	// Call gRPC service
	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()

	grpcReq := &videopb.GetVideoRequest{
		VideoId: videoID,
		UserId:  userID,
	}

	resp, err := h.clients.Video.GetVideo(ctx, grpcReq)
	if err != nil {
		transformers.HandleGRPCError(w, err)
		return
	}

	// Transform response
	variants := make([]VideoVariant, len(resp.Variants))
	for i, v := range resp.Variants {
		variants[i] = VideoVariant{
			Resolution:  v.Resolution,
			BitrateKbps: v.BitrateKbps,
			StoragePath: v.StoragePath,
		}
	}

	httpResp := VideoResponse{
		ID:              resp.Id,
		Title:           resp.Title,
		Description:     resp.Description,
		DurationSeconds: resp.DurationSeconds,
		ThumbnailURL:    resp.ThumbnailUrl,
		Status:          resp.Status,
		CreatedAt:       resp.CreatedAt,
		Variants:        variants,
	}

	transformers.EncodeJSONResponse(w, http.StatusOK, httpResp)
}

// GetStreamingURL handles GET /api/videos/:id/stream
func (h *Handler) GetStreamingURL(w http.ResponseWriter, r *http.Request) {
	// Get user ID from context
	userID, ok := r.Context().Value("user_id").(string)
	if !ok || userID == "" {
		transformers.WriteError(w, http.StatusUnauthorized, "UNAUTHORIZED", "User ID not found in context")
		return
	}

	// Get video ID from URL
	videoID := chi.URLParam(r, "id")
	if videoID == "" {
		transformers.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "video ID is required")
		return
	}

	// Get optional resolution parameter
	resolution := r.URL.Query().Get("resolution")

	// Call gRPC service
	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()

	grpcReq := &videopb.GetStreamingURLRequest{
		VideoId:    videoID,
		UserId:     userID,
		Resolution: resolution,
	}

	resp, err := h.clients.Video.GetStreamingURL(ctx, grpcReq)
	if err != nil {
		transformers.HandleGRPCError(w, err)
		return
	}

	// Transform and return response
	httpResp := StreamingURLResponse{
		URL:         resp.Url,
		ExpiresAt:   resp.ExpiresAt,
		ManifestURL: resp.ManifestUrl,
	}

	transformers.EncodeJSONResponse(w, http.StatusOK, httpResp)
}

// RecordView handles POST /api/videos/:id/view
func (h *Handler) RecordView(w http.ResponseWriter, r *http.Request) {
	// Get user ID from context
	userID, ok := r.Context().Value("user_id").(string)
	if !ok || userID == "" {
		transformers.WriteError(w, http.StatusUnauthorized, "UNAUTHORIZED", "User ID not found in context")
		return
	}

	// Get video ID from URL
	videoID := chi.URLParam(r, "id")
	if videoID == "" {
		transformers.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "video ID is required")
		return
	}

	// Decode request
	var req RecordViewRequest
	if err := transformers.DecodeJSONRequest(r, &req); err != nil {
		transformers.WriteError(w, http.StatusBadRequest, "INVALID_REQUEST", "Invalid request body")
		return
	}

	// Validate request
	if req.PositionSeconds < 0 {
		transformers.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "position_seconds must be non-negative")
		return
	}
	if req.WatchDurationSeconds < 0 {
		transformers.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "watch_duration_seconds must be non-negative")
		return
	}

	// Call gRPC service
	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()

	grpcReq := &videopb.RecordViewRequest{
		VideoId:              videoID,
		StudentId:            userID,
		PositionSeconds:      req.PositionSeconds,
		WatchDurationSeconds: req.WatchDurationSeconds,
		Completed:            req.Completed,
	}

	resp, err := h.clients.Video.RecordView(ctx, grpcReq)
	if err != nil {
		transformers.HandleGRPCError(w, err)
		return
	}

	// Transform and return response
	httpResp := RecordViewResponse{
		Success: resp.Success,
	}

	transformers.EncodeJSONResponse(w, http.StatusOK, httpResp)
}

// GetVideoAnalytics handles GET /api/videos/:id/analytics
func (h *Handler) GetVideoAnalytics(w http.ResponseWriter, r *http.Request) {
	// Get user ID from context
	userID, ok := r.Context().Value("user_id").(string)
	if !ok || userID == "" {
		transformers.WriteError(w, http.StatusUnauthorized, "UNAUTHORIZED", "User ID not found in context")
		return
	}

	// Get video ID from URL
	videoID := chi.URLParam(r, "id")
	if videoID == "" {
		transformers.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "video ID is required")
		return
	}

	// Call gRPC service
	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()

	grpcReq := &videopb.GetVideoAnalyticsRequest{
		VideoId:   videoID,
		TeacherId: userID,
	}

	resp, err := h.clients.Video.GetVideoAnalytics(ctx, grpcReq)
	if err != nil {
		transformers.HandleGRPCError(w, err)
		return
	}

	// Transform response
	studentViews := make([]StudentViewData, len(resp.StudentViews))
	for i, sv := range resp.StudentViews {
		studentViews[i] = StudentViewData{
			StudentID:         sv.StudentId,
			StudentName:       sv.StudentName,
			PercentageWatched: sv.PercentageWatched,
			TotalWatchSeconds: sv.TotalWatchSeconds,
			Completed:         sv.Completed,
			LastViewedAt:      sv.LastViewedAt,
		}
	}

	httpResp := VideoAnalyticsResponse{
		VideoID:      resp.VideoId,
		TotalViews:   resp.TotalViews,
		StudentViews: studentViews,
	}

	transformers.EncodeJSONResponse(w, http.StatusOK, httpResp)
}
