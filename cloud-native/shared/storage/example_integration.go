package storage

import (
	"context"
	"fmt"
	"io"
	"log"
	"os"
	"time"
)

// ExampleVideoService demonstrates how to integrate the storage client in a video service
type ExampleVideoService struct {
	storage *Client
}

// NewExampleVideoService creates a new example video service
func NewExampleVideoService() (*ExampleVideoService, error) {
	cfg := DefaultConfig()
	client, err := NewClient(cfg)
	if err != nil {
		return nil, fmt.Errorf("failed to create storage client: %w", err)
	}

	return &ExampleVideoService{
		storage: client,
	}, nil
}

// UploadVideo uploads a video file to storage
func (s *ExampleVideoService) UploadVideo(ctx context.Context, videoID string, file io.Reader) (string, error) {
	key := fmt.Sprintf("originals/%s.mp4", videoID)

	location, err := s.storage.Upload(ctx, "videos", key, file, &UploadOptions{
		ContentType: "video/mp4",
		ACL:         "private",
		Metadata: map[string]string{
			"video-id":    videoID,
			"status":      "uploaded",
			"uploaded-at": time.Now().Format(time.RFC3339),
		},
	})
	if err != nil {
		return "", fmt.Errorf("failed to upload video: %w", err)
	}

	log.Printf("Video uploaded successfully: %s", location)
	return location, nil
}

// GetStreamingURL generates a presigned URL for video streaming
func (s *ExampleVideoService) GetStreamingURL(ctx context.Context, videoID string) (string, error) {
	key := fmt.Sprintf("processed/%s/playlist.m3u8", videoID)

	// Check if processed video exists
	exists, err := s.storage.Exists(ctx, "videos", key)
	if err != nil {
		return "", fmt.Errorf("failed to check video existence: %w", err)
	}
	if !exists {
		return "", fmt.Errorf("processed video not found")
	}

	// Generate presigned URL valid for 1 hour
	url, err := s.storage.GeneratePresignedURL("videos", key, 1*time.Hour)
	if err != nil {
		return "", fmt.Errorf("failed to generate streaming URL: %w", err)
	}

	return url, nil
}

// SaveThumbnail saves a video thumbnail
func (s *ExampleVideoService) SaveThumbnail(ctx context.Context, videoID string, position int, imageData []byte) error {
	key := fmt.Sprintf("%s/thumb-%d.jpg", videoID, position)

	_, err := s.storage.UploadBytes(ctx, "thumbnails", key, imageData, &UploadOptions{
		ContentType: "image/jpeg",
		ACL:         "public-read", // Thumbnails are public for easy display
		Metadata: map[string]string{
			"video-id": videoID,
			"position": fmt.Sprintf("%d", position),
		},
	})
	if err != nil {
		return fmt.Errorf("failed to save thumbnail: %w", err)
	}

	log.Printf("Thumbnail saved: %s at position %d%%", videoID, position)
	return nil
}

// DeleteVideo deletes a video and all its associated files
func (s *ExampleVideoService) DeleteVideo(ctx context.Context, videoID string) error {
	// List all files for this video
	prefix := fmt.Sprintf("%s/", videoID)
	objects, err := s.storage.ListObjects(ctx, "videos", prefix)
	if err != nil {
		return fmt.Errorf("failed to list video files: %w", err)
	}

	// Delete all video files
	keys := make([]string, len(objects))
	for i, obj := range objects {
		keys[i] = obj.Key
	}
	if len(keys) > 0 {
		if err := s.storage.DeleteMultiple(ctx, "videos", keys); err != nil {
			return fmt.Errorf("failed to delete video files: %w", err)
		}
	}

	// Delete thumbnails
	thumbnailObjects, err := s.storage.ListObjects(ctx, "thumbnails", prefix)
	if err != nil {
		return fmt.Errorf("failed to list thumbnails: %w", err)
	}

	thumbnailKeys := make([]string, len(thumbnailObjects))
	for i, obj := range thumbnailObjects {
		thumbnailKeys[i] = obj.Key
	}
	if len(thumbnailKeys) > 0 {
		if err := s.storage.DeleteMultiple(ctx, "thumbnails", thumbnailKeys); err != nil {
			return fmt.Errorf("failed to delete thumbnails: %w", err)
		}
	}

	log.Printf("Video deleted: %s", videoID)
	return nil
}

// ExamplePDFService demonstrates how to integrate the storage client in a PDF service
type ExamplePDFService struct {
	storage *Client
}

// NewExamplePDFService creates a new example PDF service
func NewExamplePDFService() (*ExamplePDFService, error) {
	cfg := DefaultConfig()
	client, err := NewClient(cfg)
	if err != nil {
		return nil, fmt.Errorf("failed to create storage client: %w", err)
	}

	return &ExamplePDFService{
		storage: client,
	}, nil
}

// UploadPDF uploads a PDF file to storage
func (s *ExamplePDFService) UploadPDF(ctx context.Context, pdfID string, file io.Reader) (string, error) {
	key := fmt.Sprintf("%s.pdf", pdfID)

	location, err := s.storage.Upload(ctx, "pdfs", key, file, &UploadOptions{
		ContentType: "application/pdf",
		ACL:         "private",
		Metadata: map[string]string{
			"pdf-id":      pdfID,
			"uploaded-at": time.Now().Format(time.RFC3339),
		},
	})
	if err != nil {
		return "", fmt.Errorf("failed to upload PDF: %w", err)
	}

	log.Printf("PDF uploaded successfully: %s", location)
	return location, nil
}

// GetDownloadURL generates a presigned URL for PDF download
func (s *ExamplePDFService) GetDownloadURL(ctx context.Context, pdfID string) (string, error) {
	key := fmt.Sprintf("%s.pdf", pdfID)

	// Check if PDF exists
	exists, err := s.storage.Exists(ctx, "pdfs", key)
	if err != nil {
		return "", fmt.Errorf("failed to check PDF existence: %w", err)
	}
	if !exists {
		return "", fmt.Errorf("PDF not found")
	}

	// Generate presigned URL valid for 1 hour
	url, err := s.storage.GeneratePresignedURL("pdfs", key, 1*time.Hour)
	if err != nil {
		return "", fmt.Errorf("failed to generate download URL: %w", err)
	}

	return url, nil
}

// GetPDFInfo retrieves metadata about a PDF
func (s *ExamplePDFService) GetPDFInfo(ctx context.Context, pdfID string) (*ObjectInfo, error) {
	key := fmt.Sprintf("%s.pdf", pdfID)

	info, err := s.storage.GetObjectInfo(ctx, "pdfs", key)
	if err != nil {
		return nil, fmt.Errorf("failed to get PDF info: %w", err)
	}

	return info, nil
}

// DeletePDF deletes a PDF file
func (s *ExamplePDFService) DeletePDF(ctx context.Context, pdfID string) error {
	key := fmt.Sprintf("%s.pdf", pdfID)

	if err := s.storage.Delete(ctx, "pdfs", key); err != nil {
		return fmt.Errorf("failed to delete PDF: %w", err)
	}

	log.Printf("PDF deleted: %s", pdfID)
	return nil
}

// Example usage functions

// ExampleUploadVideo demonstrates uploading a video
func ExampleUploadVideo() {
	service, err := NewExampleVideoService()
	if err != nil {
		log.Fatalf("Failed to create service: %v", err)
	}

	// Open video file
	file, err := os.Open("sample-video.mp4")
	if err != nil {
		log.Fatalf("Failed to open file: %v", err)
	}
	defer file.Close()

	// Upload video
	ctx := context.Background()
	location, err := service.UploadVideo(ctx, "video-123", file)
	if err != nil {
		log.Fatalf("Failed to upload video: %v", err)
	}

	fmt.Printf("Video uploaded to: %s\n", location)
}

// ExampleGetStreamingURL demonstrates generating a streaming URL
func ExampleGetStreamingURL() {
	service, err := NewExampleVideoService()
	if err != nil {
		log.Fatalf("Failed to create service: %v", err)
	}

	ctx := context.Background()
	url, err := service.GetStreamingURL(ctx, "video-123")
	if err != nil {
		log.Fatalf("Failed to get streaming URL: %v", err)
	}

	fmt.Printf("Streaming URL: %s\n", url)
}

// ExampleUploadPDF demonstrates uploading a PDF
func ExampleUploadPDF() {
	service, err := NewExamplePDFService()
	if err != nil {
		log.Fatalf("Failed to create service: %v", err)
	}

	// Open PDF file
	file, err := os.Open("sample-document.pdf")
	if err != nil {
		log.Fatalf("Failed to open file: %v", err)
	}
	defer file.Close()

	// Upload PDF
	ctx := context.Background()
	location, err := service.UploadPDF(ctx, "pdf-456", file)
	if err != nil {
		log.Fatalf("Failed to upload PDF: %v", err)
	}

	fmt.Printf("PDF uploaded to: %s\n", location)
}

// ExampleGetPDFDownloadURL demonstrates generating a PDF download URL
func ExampleGetPDFDownloadURL() {
	service, err := NewExamplePDFService()
	if err != nil {
		log.Fatalf("Failed to create service: %v", err)
	}

	ctx := context.Background()
	url, err := service.GetDownloadURL(ctx, "pdf-456")
	if err != nil {
		log.Fatalf("Failed to get download URL: %v", err)
	}

	fmt.Printf("Download URL: %s\n", url)
}

// ExampleSaveThumbnails demonstrates saving video thumbnails
func ExampleSaveThumbnails() {
	service, err := NewExampleVideoService()
	if err != nil {
		log.Fatalf("Failed to create service: %v", err)
	}

	ctx := context.Background()
	videoID := "video-123"

	// Save thumbnails at different positions
	positions := []int{0, 25, 50, 75}
	for _, pos := range positions {
		// In real implementation, you would extract frame from video
		// Here we just use dummy data
		thumbnailData := []byte("thumbnail image data")

		if err := service.SaveThumbnail(ctx, videoID, pos, thumbnailData); err != nil {
			log.Fatalf("Failed to save thumbnail at %d%%: %v", pos, err)
		}
	}

	fmt.Println("All thumbnails saved successfully")
}
