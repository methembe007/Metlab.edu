package storage

import (
	"context"
	"testing"
	"time"
)

func TestDefaultConfig(t *testing.T) {
	cfg := DefaultConfig()
	
	if cfg.Endpoint != "http://minio-service:9000" {
		t.Errorf("Expected endpoint 'http://minio-service:9000', got '%s'", cfg.Endpoint)
	}
	
	if cfg.Region != "us-east-1" {
		t.Errorf("Expected region 'us-east-1', got '%s'", cfg.Region)
	}
	
	if cfg.ForcePathStyle != true {
		t.Error("Expected ForcePathStyle to be true")
	}
	
	if cfg.UseSSL != false {
		t.Error("Expected UseSSL to be false")
	}
}

func TestNewClient(t *testing.T) {
	cfg := DefaultConfig()
	
	client, err := NewClient(cfg)
	if err != nil {
		t.Fatalf("Failed to create client: %v", err)
	}
	
	if client == nil {
		t.Fatal("Expected non-nil client")
	}
	
	if client.s3Client == nil {
		t.Error("Expected non-nil s3Client")
	}
	
	if client.uploader == nil {
		t.Error("Expected non-nil uploader")
	}
	
	if client.downloader == nil {
		t.Error("Expected non-nil downloader")
	}
}

func TestGeneratePresignedURL(t *testing.T) {
	cfg := DefaultConfig()
	client, err := NewClient(cfg)
	if err != nil {
		t.Fatalf("Failed to create client: %v", err)
	}
	
	url, err := client.GeneratePresignedURL("videos", "test-video.mp4", 1*time.Hour)
	if err != nil {
		t.Fatalf("Failed to generate presigned URL: %v", err)
	}
	
	if url == "" {
		t.Error("Expected non-empty presigned URL")
	}
}

func TestGeneratePresignedUploadURL(t *testing.T) {
	cfg := DefaultConfig()
	client, err := NewClient(cfg)
	if err != nil {
		t.Fatalf("Failed to create client: %v", err)
	}
	
	url, err := client.GeneratePresignedUploadURL("videos", "test-video.mp4", 1*time.Hour)
	if err != nil {
		t.Fatalf("Failed to generate presigned upload URL: %v", err)
	}
	
	if url == "" {
		t.Error("Expected non-empty presigned upload URL")
	}
}

func TestIsNotFoundError(t *testing.T) {
	tests := []struct {
		name     string
		err      error
		expected bool
	}{
		{
			name:     "nil error",
			err:      nil,
			expected: false,
		},
	}
	
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := isNotFoundError(tt.err)
			if result != tt.expected {
				t.Errorf("Expected %v, got %v", tt.expected, result)
			}
		})
	}
}

// Integration tests (require MinIO to be running)
func TestIntegrationUploadDownload(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test")
	}
	
	cfg := DefaultConfig()
	client, err := NewClient(cfg)
	if err != nil {
		t.Fatalf("Failed to create client: %v", err)
	}
	
	ctx := context.Background()
	bucket := "videos"
	key := "test-upload.txt"
	data := []byte("Hello, MinIO!")
	
	// Upload
	_, err = client.UploadBytes(ctx, bucket, key, data, &UploadOptions{
		ContentType: "text/plain",
		ACL:         "private",
	})
	if err != nil {
		t.Fatalf("Failed to upload: %v", err)
	}
	
	// Check existence
	exists, err := client.Exists(ctx, bucket, key)
	if err != nil {
		t.Fatalf("Failed to check existence: %v", err)
	}
	if !exists {
		t.Error("Expected object to exist")
	}
	
	// Download
	downloaded, err := client.Download(ctx, bucket, key)
	if err != nil {
		t.Fatalf("Failed to download: %v", err)
	}
	
	if string(downloaded) != string(data) {
		t.Errorf("Expected '%s', got '%s'", string(data), string(downloaded))
	}
	
	// Get object info
	info, err := client.GetObjectInfo(ctx, bucket, key)
	if err != nil {
		t.Fatalf("Failed to get object info: %v", err)
	}
	
	if info.Size != int64(len(data)) {
		t.Errorf("Expected size %d, got %d", len(data), info.Size)
	}
	
	// Delete
	err = client.Delete(ctx, bucket, key)
	if err != nil {
		t.Fatalf("Failed to delete: %v", err)
	}
	
	// Verify deletion
	exists, err = client.Exists(ctx, bucket, key)
	if err != nil {
		t.Fatalf("Failed to check existence after deletion: %v", err)
	}
	if exists {
		t.Error("Expected object to not exist after deletion")
	}
}
