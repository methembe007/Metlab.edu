package storage

import (
	"context"
	"fmt"
	"io"
	"os"
	"time"
)

// S3Client is a wrapper around Client with additional helper methods
type S3Client struct {
	*Client
	bucket string
}

// S3Config holds configuration for S3Client
type S3Config struct {
	Endpoint  string
	AccessKey string
	SecretKey string
	Bucket    string
	Region    string
	UseSSL    bool
}

// NewS3Client creates a new S3Client with bucket configuration
func NewS3Client(cfg *S3Config) (*S3Client, error) {
	client, err := NewClient(&Config{
		Endpoint:       cfg.Endpoint,
		Region:         cfg.Region,
		AccessKeyID:    cfg.AccessKey,
		SecretAccessKey: cfg.SecretKey,
		UseSSL:         cfg.UseSSL,
		ForcePathStyle: true,
	})
	if err != nil {
		return nil, err
	}

	return &S3Client{
		Client: client,
		bucket: cfg.Bucket,
	}, nil
}

// UploadFile uploads a file from the local filesystem to S3
func (c *S3Client) UploadFile(ctx context.Context, localPath, key string) error {
	file, err := os.Open(localPath)
	if err != nil {
		return fmt.Errorf("failed to open file: %w", err)
	}
	defer file.Close()

	_, err = c.Client.Upload(ctx, c.bucket, key, file, nil)
	if err != nil {
		return fmt.Errorf("failed to upload file: %w", err)
	}

	return nil
}

// DownloadFile downloads a file from S3 to the local filesystem
func (c *S3Client) DownloadFile(ctx context.Context, key, localPath string) error {
	file, err := os.Create(localPath)
	if err != nil {
		return fmt.Errorf("failed to create file: %w", err)
	}
	defer file.Close()

	data, err := c.Download(ctx, c.bucket, key)
	if err != nil {
		return fmt.Errorf("failed to download file: %w", err)
	}

	_, err = file.Write(data)
	if err != nil {
		return fmt.Errorf("failed to write file: %w", err)
	}

	return nil
}

// GetObjectReader returns a reader for streaming an object from S3
func (c *S3Client) GetObjectReader(ctx context.Context, key string) (io.ReadCloser, error) {
	return c.GetObject(ctx, c.bucket, key)
}

// DeleteFile deletes a file from S3
func (c *S3Client) DeleteFile(ctx context.Context, key string) error {
	return c.Client.Delete(ctx, c.bucket, key)
}

// FileExists checks if a file exists in S3
func (c *S3Client) FileExists(ctx context.Context, key string) (bool, error) {
	return c.Exists(ctx, c.bucket, key)
}

// GenerateDownloadURL generates a presigned URL for downloading a file
func (c *S3Client) GenerateDownloadURL(key string, expiration time.Duration) (string, error) {
	return c.GeneratePresignedURL(c.bucket, key, expiration)
}

// Upload uploads byte data to S3 with the configured bucket
func (c *S3Client) Upload(ctx context.Context, key string, data []byte) error {
	_, err := c.Client.UploadBytes(ctx, c.bucket, key, data, &UploadOptions{
		ContentType: "application/pdf",
		ACL:         "private",
	})
	return err
}

// Delete deletes a file from S3 using the configured bucket
func (c *S3Client) Delete(ctx context.Context, key string) error {
	return c.Client.Delete(ctx, c.bucket, key)
}

// GetSignedURL generates a presigned URL for downloading a file with expiration time
func (c *S3Client) GetSignedURL(ctx context.Context, key string, expiresAt time.Time) (string, error) {
	duration := time.Until(expiresAt)
	if duration <= 0 {
		return "", fmt.Errorf("expiration time must be in the future")
	}
	return c.GeneratePresignedURL(c.bucket, key, duration)
}
