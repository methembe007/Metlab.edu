package worker

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
	"github.com/metlab/shared/logger"
	"github.com/metlab/shared/queue"
	"github.com/metlab/shared/storage"
)

// VideoProcessor handles background video processing
type VideoProcessor struct {
	repo          *repository.VideoRepository
	storageClient *storage.Client
	ffmpeg        *ffmpeg.Processor
	queue         *queue.Queue
	videoBucket   string
	tempDir       string
	log           *logger.Logger
}

// NewVideoProcessor creates a new video processor
func NewVideoProcessor(
	repo *repository.VideoRepository,
	storageClient *storage.Client,
	queue *queue.Queue,
	videoBucket string,
	tempDir string,
	log *logger.Logger,
) *VideoProcessor {
	return &VideoProcessor{
		repo:          repo,
		storageClient: storageClient,
		ffmpeg:        ffmpeg.NewProcessor(),
		queue:         queue,
		videoBucket:   videoBucket,
		tempDir:       tempDir,
		log:           log,
	}
}

// Start begins processing jobs from the queue
func (p *VideoProcessor) Start(ctx context.Context) error {
	p.log.Info("video processor started", nil)

	for {
		select {
		case <-ctx.Done():
			p.log.Info("video processor stopped", nil)
			return ctx.Err()
		default:
			// Dequeue job with 5 second timeout
			job, err := p.queue.Dequeue(ctx, 5*time.Second)
			if err != nil {
				p.log.Error("failed to dequeue job", err, nil)
				time.Sleep(1 * time.Second)
				continue
			}

			if job == nil {
				// No job available, continue
				continue
			}

			// Process the job
			if err := p.processJob(ctx, job); err != nil {
				p.log.Error("failed to process job", err, map[string]interface{}{
					"job_id": job.ID,
					"job_type": job.Type,
				})
			}
		}
	}
}

// processJob processes a single video processing job
func (p *VideoProcessor) processJob(ctx context.Context, job *queue.Job) error {
	if job.Type != "process_video" {
		return fmt.Errorf("unknown job type: %s", job.Type)
	}

	videoID, ok := job.Payload["video_id"].(string)
	if !ok {
		return fmt.Errorf("missing video_id in job payload")
	}

	p.log.Info("processing video", map[string]interface{}{
		"video_id": videoID,
		"job_id": job.ID,
	})

	// Get video record
	video, err := p.repo.GetVideoByID(ctx, videoID)
	if err != nil {
		return fmt.Errorf("failed to get video: %w", err)
	}

	// Download original video from storage
	originalPath := filepath.Join(p.tempDir, fmt.Sprintf("%s_original", videoID))
	if err := p.downloadFromStorage(ctx, video.StoragePath, originalPath); err != nil {
		p.repo.UpdateVideoStatus(ctx, videoID, "failed")
		return fmt.Errorf("failed to download video: %w", err)
	}
	defer os.Remove(originalPath)

	// Extract video metadata
	metadata, err := p.ffmpeg.GetMetadata(ctx, originalPath)
	if err != nil {
		p.repo.UpdateVideoStatus(ctx, videoID, "failed")
		return fmt.Errorf("failed to extract metadata: %w", err)
	}

	// Update video with metadata
	if err := p.repo.UpdateVideoMetadata(ctx, videoID, metadata.DurationSeconds); err != nil {
		p.log.Error("failed to update video metadata", err, map[string]interface{}{
			"video_id": videoID,
		})
	}

	p.log.Info("extracted video metadata", map[string]interface{}{
		"video_id": videoID,
		"duration": metadata.DurationSeconds,
		"resolution": fmt.Sprintf("%dx%d", metadata.Width, metadata.Height),
		"codec": metadata.Codec,
	})

	// Generate multiple resolution variants
	resolutions := []string{"1080p", "720p", "480p", "360p"}
	for _, resolution := range resolutions {
		// Skip if original resolution is lower than target
		if !p.shouldGenerateResolution(metadata, resolution) {
			p.log.Info("skipping resolution variant", map[string]interface{}{
				"video_id": videoID,
				"resolution": resolution,
				"reason": "original resolution is lower",
			})
			continue
		}

		if err := p.generateVariant(ctx, videoID, originalPath, resolution); err != nil {
			p.log.Error("failed to generate variant", err, map[string]interface{}{
				"video_id": videoID,
				"resolution": resolution,
			})
			// Continue with other resolutions
		}
	}

	// Generate HLS manifest for adaptive streaming
	if err := p.generateHLS(ctx, videoID, originalPath); err != nil {
		p.log.Error("failed to generate HLS manifest", err, map[string]interface{}{
			"video_id": videoID,
		})
		// Don't fail the entire job if HLS generation fails
	}

	// Generate thumbnails at 0%, 25%, 50%, 75%
	thumbnailPercents := []int32{0, 25, 50, 75}
	for _, percent := range thumbnailPercents {
		if err := p.generateThumbnail(ctx, videoID, originalPath, percent); err != nil {
			p.log.Error("failed to generate thumbnail", err, map[string]interface{}{
				"video_id": videoID,
				"percent": percent,
			})
			// Continue with other thumbnails
		}
	}

	// Update video status to ready
	if err := p.repo.UpdateVideoStatus(ctx, videoID, "ready"); err != nil {
		return fmt.Errorf("failed to update video status: %w", err)
	}

	p.log.Info("video processing completed", map[string]interface{}{
		"video_id": videoID,
	})

	return nil
}

// shouldGenerateResolution determines if a resolution variant should be generated
func (p *VideoProcessor) shouldGenerateResolution(metadata *ffmpeg.VideoMetadata, resolution string) bool {
	var targetHeight int32
	switch resolution {
	case "1080p":
		targetHeight = 1080
	case "720p":
		targetHeight = 720
	case "480p":
		targetHeight = 480
	case "360p":
		targetHeight = 360
	default:
		return false
	}

	// Only generate if original height is greater than or equal to target
	return metadata.Height >= targetHeight
}

// generateVariant generates a video variant at a specific resolution
func (p *VideoProcessor) generateVariant(ctx context.Context, videoID, inputPath, resolution string) error {
	// Create output file
	outputPath := filepath.Join(p.tempDir, fmt.Sprintf("%s_%s.mp4", videoID, resolution))
	defer os.Remove(outputPath)

	// Transcode video
	bitrate := ffmpeg.GetRecommendedBitrate(resolution)
	opts := &ffmpeg.TranscodeOptions{
		Resolution:  resolution,
		BitrateKbps: bitrate,
		OutputPath:  outputPath,
	}

	if err := p.ffmpeg.Transcode(ctx, inputPath, opts); err != nil {
		return fmt.Errorf("transcoding failed: %w", err)
	}

	// Get file size
	fileInfo, err := os.Stat(outputPath)
	if err != nil {
		return fmt.Errorf("failed to stat output file: %w", err)
	}

	// Upload to storage
	storagePath := fmt.Sprintf("videos/%s/variants/%s.mp4", videoID, resolution)
	file, err := os.Open(outputPath)
	if err != nil {
		return fmt.Errorf("failed to open output file: %w", err)
	}
	defer file.Close()

	if _, err := p.storageClient.Upload(ctx, p.videoBucket, storagePath, file, nil); err != nil {
		return fmt.Errorf("failed to upload variant: %w", err)
	}

	// Create variant record in database
	variant := &models.VideoVariant{
		VideoID:       videoID,
		Resolution:    resolution,
		BitrateKbps:   bitrate,
		StoragePath:   storagePath,
		FileSizeBytes: fileInfo.Size(),
	}

	if err := p.repo.CreateVideoVariant(ctx, variant); err != nil {
		return fmt.Errorf("failed to create variant record: %w", err)
	}

	p.log.Info("generated video variant", map[string]interface{}{
		"video_id": videoID,
		"resolution": resolution,
		"size_mb": fileInfo.Size() / (1024 * 1024),
	})

	return nil
}

// generateHLS generates HLS manifest and segments for adaptive streaming
func (p *VideoProcessor) generateHLS(ctx context.Context, videoID, inputPath string) error {
	// Create HLS output directory
	hlsDir := filepath.Join(p.tempDir, fmt.Sprintf("%s_hls", videoID))
	if err := os.MkdirAll(hlsDir, 0755); err != nil {
		return fmt.Errorf("failed to create HLS directory: %w", err)
	}
	defer os.RemoveAll(hlsDir)

	// Generate HLS manifest and segments
	if err := p.ffmpeg.GenerateHLSManifest(ctx, inputPath, hlsDir); err != nil {
		return fmt.Errorf("failed to generate HLS: %w", err)
	}

	// Upload all HLS files to storage
	files, err := os.ReadDir(hlsDir)
	if err != nil {
		return fmt.Errorf("failed to read HLS directory: %w", err)
	}

	for _, file := range files {
		if file.IsDir() {
			continue
		}

		filePath := filepath.Join(hlsDir, file.Name())
		storagePath := fmt.Sprintf("videos/%s/hls/%s", videoID, file.Name())

		f, err := os.Open(filePath)
		if err != nil {
			p.log.Error("failed to open HLS file", err, map[string]interface{}{
				"file": file.Name(),
			})
			continue
		}

		if _, err := p.storageClient.Upload(ctx, p.videoBucket, storagePath, f, nil); err != nil {
			f.Close()
			p.log.Error("failed to upload HLS file", err, map[string]interface{}{
				"file": file.Name(),
			})
			continue
		}
		f.Close()
	}

	p.log.Info("generated HLS manifest", map[string]interface{}{
		"video_id": videoID,
		"files": len(files),
	})

	return nil
}

// generateThumbnail generates a thumbnail at a specific timestamp percentage
func (p *VideoProcessor) generateThumbnail(ctx context.Context, videoID, inputPath string, percent int32) error {
	// Create output file
	outputPath := filepath.Join(p.tempDir, fmt.Sprintf("%s_thumb_%d.jpg", videoID, percent))
	defer os.Remove(outputPath)

	// Generate thumbnail
	if err := p.ffmpeg.GenerateThumbnail(ctx, inputPath, percent, outputPath); err != nil {
		return fmt.Errorf("thumbnail generation failed: %w", err)
	}

	// Upload to storage
	storagePath := fmt.Sprintf("videos/%s/thumbnails/thumb_%d.jpg", videoID, percent)
	file, err := os.Open(outputPath)
	if err != nil {
		return fmt.Errorf("failed to open thumbnail file: %w", err)
	}
	defer file.Close()

	if _, err := p.storageClient.Upload(ctx, p.videoBucket, storagePath, file, nil); err != nil {
		return fmt.Errorf("failed to upload thumbnail: %w", err)
	}

	// Create thumbnail record in database
	thumbnail := &models.VideoThumbnail{
		VideoID:          videoID,
		TimestampPercent: percent,
		StoragePath:      storagePath,
	}

	if err := p.repo.CreateVideoThumbnail(ctx, thumbnail); err != nil {
		return fmt.Errorf("failed to create thumbnail record: %w", err)
	}

	p.log.Info("generated thumbnail", map[string]interface{}{
		"video_id": videoID,
		"percent": percent,
	})

	return nil
}

// downloadFromStorage downloads a file from S3 storage to local filesystem
func (p *VideoProcessor) downloadFromStorage(ctx context.Context, storagePath, localPath string) error {
	// Get object from storage
	reader, err := p.storageClient.GetObject(ctx, p.videoBucket, storagePath)
	if err != nil {
		return fmt.Errorf("failed to download from storage: %w", err)
	}
	defer reader.Close()

	// Create local file
	file, err := os.Create(localPath)
	if err != nil {
		return fmt.Errorf("failed to create local file: %w", err)
	}
	defer file.Close()

	// Copy data
	if _, err := io.Copy(file, reader); err != nil {
		return fmt.Errorf("failed to copy data: %w", err)
	}

	return nil
}
