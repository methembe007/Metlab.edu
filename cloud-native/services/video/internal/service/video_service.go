package service

import (
	"context"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"time"

	"github.com/metlab/video/internal/ffmpeg"
	"github.com/metlab/video/internal/models"
	"github.com/metlab/video/internal/repository"
	pb "github.com/metlab/shared/proto-gen/go/video"
	"github.com/metlab/shared/queue"
	"github.com/metlab/shared/storage"

	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

// VideoService implements the gRPC VideoService
type VideoService struct {
	pb.UnimplementedVideoServiceServer
	repo           *repository.VideoRepository
	storageClient  StorageClient
	ffmpegProcessor *ffmpeg.Processor
	processingQueue Queue
	tempDir        string
	videoBucket    string
}

// StorageClient interface for S3-compatible storage
type StorageClient interface {
	Upload(ctx context.Context, bucket, key string, data io.Reader, opts *storage.UploadOptions) (string, error)
	GeneratePresignedURL(bucket, key string, expiration time.Duration) (string, error)
	Delete(ctx context.Context, bucket, key string) error
}

// Queue interface for job queue
type Queue interface {
	Enqueue(ctx context.Context, job *queue.Job) error
}

// NewVideoService creates a new video service
func NewVideoService(
	repo *repository.VideoRepository,
	storageClient StorageClient,
	processingQueue Queue,
	videoBucket string,
	tempDir string,
) *VideoService {
	return &VideoService{
		repo:           repo,
		storageClient:  storageClient,
		ffmpegProcessor: ffmpeg.NewProcessor(),
		processingQueue: processingQueue,
		tempDir:        tempDir,
		videoBucket:    videoBucket,
	}
}

// UploadVideo handles video upload streaming
func (s *VideoService) UploadVideo(stream pb.VideoService_UploadVideoServer) error {
	ctx := stream.Context()

	// Receive first message with metadata
	req, err := stream.Recv()
	if err != nil {
		return status.Errorf(codes.InvalidArgument, "failed to receive metadata: %v", err)
	}

	metadata := req.GetMetadata()
	if metadata == nil {
		return status.Error(codes.InvalidArgument, "first message must contain metadata")
	}

	// Validate metadata
	if metadata.TeacherId == "" || metadata.ClassId == "" || metadata.Title == "" {
		return status.Error(codes.InvalidArgument, "teacher_id, class_id, and title are required")
	}

	// Validate file size (max 2GB)
	if metadata.FileSize > 2*1024*1024*1024 {
		return status.Error(codes.InvalidArgument, "file size exceeds 2GB limit")
	}

	// Create video record
	video := &models.Video{
		TeacherID:        metadata.TeacherId,
		ClassID:          metadata.ClassId,
		Title:            metadata.Title,
		Description:      metadata.Description,
		OriginalFilename: metadata.Filename,
		FileSizeBytes:    metadata.FileSize,
		Status:           "uploading",
	}

	err = s.repo.CreateVideo(ctx, video)
	if err != nil {
		return status.Errorf(codes.Internal, "failed to create video record: %v", err)
	}

	// Create temporary file for upload
	tempFile := filepath.Join(s.tempDir, fmt.Sprintf("%s_%s", video.ID, metadata.Filename))
	file, err := os.Create(tempFile)
	if err != nil {
		return status.Errorf(codes.Internal, "failed to create temp file: %v", err)
	}
	defer os.Remove(tempFile)
	defer file.Close()

	// Receive and write video chunks
	var totalBytes int64
	for {
		req, err := stream.Recv()
		if err == io.EOF {
			break
		}
		if err != nil {
			s.repo.UpdateVideoStatus(ctx, video.ID, "failed")
			return status.Errorf(codes.Internal, "failed to receive chunk: %v", err)
		}

		chunk := req.GetChunk()
		if chunk == nil {
			continue
		}

		n, err := file.Write(chunk)
		if err != nil {
			s.repo.UpdateVideoStatus(ctx, video.ID, "failed")
			return status.Errorf(codes.Internal, "failed to write chunk: %v", err)
		}
		totalBytes += int64(n)
	}

	// Close file to flush writes
	file.Close()

	// Validate video file
	err = s.ffmpegProcessor.ValidateVideoFile(ctx, tempFile)
	if err != nil {
		s.repo.UpdateVideoStatus(ctx, video.ID, "failed")
		return status.Errorf(codes.InvalidArgument, "invalid video file: %v", err)
	}

	// Upload to storage
	storagePath := fmt.Sprintf("videos/%s/original/%s", video.ID, metadata.Filename)
	file, _ = os.Open(tempFile)
	defer file.Close()

	_, err = s.storageClient.Upload(ctx, s.videoBucket, storagePath, file, nil)
	if err != nil {
		s.repo.UpdateVideoStatus(ctx, video.ID, "failed")
		return status.Errorf(codes.Internal, "failed to upload to storage: %v", err)
	}

	// Update video record with storage path
	video.StoragePath = storagePath
	s.repo.UpdateVideoStatus(ctx, video.ID, "processing")

	// Queue video processing job
	job := &queue.Job{
		ID:   video.ID,
		Type: "process_video",
		Payload: map[string]interface{}{
			"video_id": video.ID,
			"path":     storagePath,
		},
	}

	if err := s.processingQueue.Enqueue(ctx, job); err != nil {
		// Log error but don't fail the upload - video can be processed manually
		// In production, this should be logged to a monitoring system
		fmt.Printf("Warning: failed to queue video processing job: %v\n", err)
	}

	// Send response
	return stream.SendAndClose(&pb.UploadVideoResponse{
		VideoId: video.ID,
		Status:  "processing",
	})
}

// ListVideos lists videos for a class
func (s *VideoService) ListVideos(ctx context.Context, req *pb.ListVideosRequest) (*pb.ListVideosResponse, error) {
	if req.ClassId == "" {
		return nil, status.Error(codes.InvalidArgument, "class_id is required")
	}

	page := req.Page
	if page < 1 {
		page = 1
	}
	pageSize := req.PageSize
	if pageSize < 1 || pageSize > 100 {
		pageSize = 20
	}

	videos, totalCount, err := s.repo.ListVideosByClass(ctx, req.ClassId, page, pageSize)
	if err != nil {
		return nil, status.Errorf(codes.Internal, "failed to list videos: %v", err)
	}

	// Convert to proto messages
	pbVideos := make([]*pb.Video, len(videos))
	for i, video := range videos {
		// Get thumbnails
		thumbnails, _ := s.repo.GetVideoThumbnails(ctx, video.ID)
		thumbnailURL := ""
		if len(thumbnails) > 0 {
			// Use first thumbnail
			thumbnailURL, _ = s.storageClient.GeneratePresignedURL(
				s.videoBucket,
				thumbnails[0].StoragePath,
				1*time.Hour,
			)
		}

		// Get variants
		variants, _ := s.repo.GetVideoVariants(ctx, video.ID)
		pbVariants := make([]*pb.VideoVariant, len(variants))
		for j, variant := range variants {
			pbVariants[j] = &pb.VideoVariant{
				Resolution:   variant.Resolution,
				BitrateKbps:  variant.BitrateKbps,
				StoragePath:  variant.StoragePath,
			}
		}

		pbVideos[i] = &pb.Video{
			Id:              video.ID,
			Title:           video.Title,
			Description:     video.Description,
			DurationSeconds: video.DurationSeconds,
			ThumbnailUrl:    thumbnailURL,
			Status:          video.Status,
			CreatedAt:       video.CreatedAt.Unix(),
			Variants:        pbVariants,
		}
	}

	return &pb.ListVideosResponse{
		Videos:     pbVideos,
		TotalCount: totalCount,
	}, nil
}

// GetVideo retrieves a single video by ID
func (s *VideoService) GetVideo(ctx context.Context, req *pb.GetVideoRequest) (*pb.Video, error) {
	if req.VideoId == "" {
		return nil, status.Error(codes.InvalidArgument, "video_id is required")
	}

	video, err := s.repo.GetVideoByID(ctx, req.VideoId)
	if err != nil {
		return nil, status.Errorf(codes.NotFound, "video not found: %v", err)
	}

	// Get thumbnails
	thumbnails, _ := s.repo.GetVideoThumbnails(ctx, video.ID)
	thumbnailURL := ""
	if len(thumbnails) > 0 {
		thumbnailURL, _ = s.storageClient.GeneratePresignedURL(
			s.videoBucket,
			thumbnails[0].StoragePath,
			1*time.Hour,
		)
	}

	// Get variants
	variants, _ := s.repo.GetVideoVariants(ctx, video.ID)
	pbVariants := make([]*pb.VideoVariant, len(variants))
	for i, variant := range variants {
		pbVariants[i] = &pb.VideoVariant{
			Resolution:   variant.Resolution,
			BitrateKbps:  variant.BitrateKbps,
			StoragePath:  variant.StoragePath,
		}
	}

	return &pb.Video{
		Id:              video.ID,
		Title:           video.Title,
		Description:     video.Description,
		DurationSeconds: video.DurationSeconds,
		ThumbnailUrl:    thumbnailURL,
		Status:          video.Status,
		CreatedAt:       video.CreatedAt.Unix(),
		Variants:        pbVariants,
	}, nil
}

// GetStreamingURL generates a streaming URL for a video
func (s *VideoService) GetStreamingURL(ctx context.Context, req *pb.GetStreamingURLRequest) (*pb.StreamingURLResponse, error) {
	if req.VideoId == "" {
		return nil, status.Error(codes.InvalidArgument, "video_id is required")
	}

	video, err := s.repo.GetVideoByID(ctx, req.VideoId)
	if err != nil {
		return nil, status.Errorf(codes.NotFound, "video not found: %v", err)
	}

	if video.Status != "ready" {
		return nil, status.Error(codes.FailedPrecondition, "video is not ready for streaming")
	}

	// Generate presigned URL for HLS manifest
	manifestPath := fmt.Sprintf("videos/%s/hls/playlist.m3u8", video.ID)
	url, err := s.storageClient.GeneratePresignedURL(s.videoBucket, manifestPath, 1*time.Hour)
	if err != nil {
		return nil, status.Errorf(codes.Internal, "failed to generate URL: %v", err)
	}

	return &pb.StreamingURLResponse{
		Url:         url,
		ExpiresAt:   time.Now().Add(1 * time.Hour).Unix(),
		ManifestUrl: url,
	}, nil
}

// RecordView records a video view
func (s *VideoService) RecordView(ctx context.Context, req *pb.RecordViewRequest) (*pb.RecordViewResponse, error) {
	if req.VideoId == "" || req.StudentId == "" {
		return nil, status.Error(codes.InvalidArgument, "video_id and student_id are required")
	}

	view := &models.VideoView{
		VideoID:            req.VideoId,
		StudentID:          req.StudentId,
		LastPositionSeconds: req.PositionSeconds,
		TotalWatchSeconds:  req.WatchDurationSeconds,
		Completed:          req.Completed,
	}

	err := s.repo.RecordVideoView(ctx, view)
	if err != nil {
		return nil, status.Errorf(codes.Internal, "failed to record view: %v", err)
	}

	return &pb.RecordViewResponse{
		Success: true,
	}, nil
}

// GetVideoAnalytics retrieves viewing analytics for a video
func (s *VideoService) GetVideoAnalytics(ctx context.Context, req *pb.GetVideoAnalyticsRequest) (*pb.VideoAnalyticsResponse, error) {
	if req.VideoId == "" {
		return nil, status.Error(codes.InvalidArgument, "video_id is required")
	}

	// Get total views
	totalViews, err := s.repo.GetTotalViews(ctx, req.VideoId)
	if err != nil {
		return nil, status.Errorf(codes.Internal, "failed to get total views: %v", err)
	}

	// Get student view data
	studentViews, err := s.repo.GetVideoAnalytics(ctx, req.VideoId)
	if err != nil {
		return nil, status.Errorf(codes.Internal, "failed to get analytics: %v", err)
	}

	// Convert to proto messages
	pbStudentViews := make([]*pb.StudentViewData, len(studentViews))
	for i, view := range studentViews {
		pbStudentViews[i] = &pb.StudentViewData{
			StudentId:         view.StudentID,
			StudentName:       view.StudentName,
			PercentageWatched: view.PercentageWatched,
			TotalWatchSeconds: view.TotalWatchSeconds,
			Completed:         view.Completed,
			LastViewedAt:      view.LastViewedAt.Unix(),
		}
	}

	return &pb.VideoAnalyticsResponse{
		VideoId:      req.VideoId,
		TotalViews:   totalViews,
		StudentViews: pbStudentViews,
	}, nil
}
