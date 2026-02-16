package storage

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"time"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/credentials"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/s3"
	"github.com/aws/aws-sdk-go/service/s3/s3manager"
)

// Config holds S3 storage configuration
type Config struct {
	Endpoint        string // S3 endpoint (e.g., "http://minio-service:9000" for MinIO)
	Region          string // AWS region (use "us-east-1" for MinIO)
	AccessKeyID     string // Access key ID
	SecretAccessKey string // Secret access key
	UseSSL          bool   // Use HTTPS (false for local MinIO)
	ForcePathStyle  bool   // Force path-style URLs (true for MinIO)
}

// DefaultConfig returns a configuration with sensible defaults for local MinIO
func DefaultConfig() *Config {
	return &Config{
		Endpoint:       "http://minio-service:9000",
		Region:         "us-east-1",
		AccessKeyID:    "minioadmin",
		SecretAccessKey: "minioadmin123",
		UseSSL:         false,
		ForcePathStyle: true,
	}
}

// Client wraps the AWS S3 client with helper methods
type Client struct {
	s3Client   *s3.S3
	uploader   *s3manager.Uploader
	downloader *s3manager.Downloader
	config     *Config
}

// NewClient creates a new S3 storage client
func NewClient(cfg *Config) (*Client, error) {
	// Create AWS session
	sess, err := session.NewSession(&aws.Config{
		Endpoint:         aws.String(cfg.Endpoint),
		Region:           aws.String(cfg.Region),
		Credentials:      credentials.NewStaticCredentials(cfg.AccessKeyID, cfg.SecretAccessKey, ""),
		S3ForcePathStyle: aws.Bool(cfg.ForcePathStyle),
		DisableSSL:       aws.Bool(!cfg.UseSSL),
	})
	if err != nil {
		return nil, fmt.Errorf("failed to create AWS session: %w", err)
	}

	// Create S3 client
	s3Client := s3.New(sess)

	// Create uploader and downloader
	uploader := s3manager.NewUploader(sess)
	downloader := s3manager.NewDownloader(sess)

	return &Client{
		s3Client:   s3Client,
		uploader:   uploader,
		downloader: downloader,
		config:     cfg,
	}, nil
}

// UploadOptions contains options for uploading files
type UploadOptions struct {
	ContentType string            // MIME type of the file
	Metadata    map[string]string // Custom metadata
	ACL         string            // Access control (e.g., "public-read", "private")
}

// Upload uploads data to S3
func (c *Client) Upload(ctx context.Context, bucket, key string, data io.Reader, opts *UploadOptions) (string, error) {
	if opts == nil {
		opts = &UploadOptions{
			ContentType: "application/octet-stream",
			ACL:         "private",
		}
	}

	// Prepare upload input
	input := &s3manager.UploadInput{
		Bucket:      aws.String(bucket),
		Key:         aws.String(key),
		Body:        data,
		ContentType: aws.String(opts.ContentType),
		ACL:         aws.String(opts.ACL),
	}

	// Add metadata if provided
	if opts.Metadata != nil {
		metadata := make(map[string]*string)
		for k, v := range opts.Metadata {
			metadata[k] = aws.String(v)
		}
		input.Metadata = metadata
	}

	// Upload the file
	result, err := c.uploader.UploadWithContext(ctx, input)
	if err != nil {
		return "", fmt.Errorf("failed to upload to S3: %w", err)
	}

	return result.Location, nil
}

// UploadBytes uploads byte data to S3
func (c *Client) UploadBytes(ctx context.Context, bucket, key string, data []byte, opts *UploadOptions) (string, error) {
	return c.Upload(ctx, bucket, key, bytes.NewReader(data), opts)
}

// Download downloads data from S3
func (c *Client) Download(ctx context.Context, bucket, key string) ([]byte, error) {
	// Create a buffer to write the downloaded data
	buf := aws.NewWriteAtBuffer([]byte{})

	// Download the file
	_, err := c.downloader.DownloadWithContext(ctx, buf, &s3.GetObjectInput{
		Bucket: aws.String(bucket),
		Key:    aws.String(key),
	})
	if err != nil {
		return nil, fmt.Errorf("failed to download from S3: %w", err)
	}

	return buf.Bytes(), nil
}

// GetObject returns a reader for streaming an object from S3
func (c *Client) GetObject(ctx context.Context, bucket, key string) (io.ReadCloser, error) {
	result, err := c.s3Client.GetObjectWithContext(ctx, &s3.GetObjectInput{
		Bucket: aws.String(bucket),
		Key:    aws.String(key),
	})
	if err != nil {
		return nil, fmt.Errorf("failed to get object from S3: %w", err)
	}

	return result.Body, nil
}

// DownloadToWriter downloads data from S3 to a writer
func (c *Client) DownloadToWriter(ctx context.Context, bucket, key string, writer io.WriterAt) (int64, error) {
	n, err := c.downloader.DownloadWithContext(ctx, writer, &s3.GetObjectInput{
		Bucket: aws.String(bucket),
		Key:    aws.String(key),
	})
	if err != nil {
		return 0, fmt.Errorf("failed to download from S3: %w", err)
	}

	return n, nil
}

// Delete deletes an object from S3
func (c *Client) Delete(ctx context.Context, bucket, key string) error {
	_, err := c.s3Client.DeleteObjectWithContext(ctx, &s3.DeleteObjectInput{
		Bucket: aws.String(bucket),
		Key:    aws.String(key),
	})
	if err != nil {
		return fmt.Errorf("failed to delete from S3: %w", err)
	}

	return nil
}

// DeleteMultiple deletes multiple objects from S3
func (c *Client) DeleteMultiple(ctx context.Context, bucket string, keys []string) error {
	if len(keys) == 0 {
		return nil
	}

	// Prepare objects to delete
	objects := make([]*s3.ObjectIdentifier, len(keys))
	for i, key := range keys {
		objects[i] = &s3.ObjectIdentifier{
			Key: aws.String(key),
		}
	}

	// Delete objects
	_, err := c.s3Client.DeleteObjectsWithContext(ctx, &s3.DeleteObjectsInput{
		Bucket: aws.String(bucket),
		Delete: &s3.Delete{
			Objects: objects,
			Quiet:   aws.Bool(true),
		},
	})
	if err != nil {
		return fmt.Errorf("failed to delete multiple objects from S3: %w", err)
	}

	return nil
}

// Exists checks if an object exists in S3
func (c *Client) Exists(ctx context.Context, bucket, key string) (bool, error) {
	_, err := c.s3Client.HeadObjectWithContext(ctx, &s3.HeadObjectInput{
		Bucket: aws.String(bucket),
		Key:    aws.String(key),
	})
	if err != nil {
		// Check if error is "not found"
		if isNotFoundError(err) {
			return false, nil
		}
		return false, fmt.Errorf("failed to check object existence: %w", err)
	}

	return true, nil
}

// GetObjectInfo returns metadata about an object
type ObjectInfo struct {
	Key          string
	Size         int64
	LastModified time.Time
	ContentType  string
	ETag         string
	Metadata     map[string]string
}

// GetObjectInfo retrieves metadata about an object
func (c *Client) GetObjectInfo(ctx context.Context, bucket, key string) (*ObjectInfo, error) {
	result, err := c.s3Client.HeadObjectWithContext(ctx, &s3.HeadObjectInput{
		Bucket: aws.String(bucket),
		Key:    aws.String(key),
	})
	if err != nil {
		return nil, fmt.Errorf("failed to get object info: %w", err)
	}

	info := &ObjectInfo{
		Key:          key,
		Size:         aws.Int64Value(result.ContentLength),
		LastModified: aws.TimeValue(result.LastModified),
		ContentType:  aws.StringValue(result.ContentType),
		ETag:         aws.StringValue(result.ETag),
		Metadata:     make(map[string]string),
	}

	// Copy metadata
	for k, v := range result.Metadata {
		info.Metadata[k] = aws.StringValue(v)
	}

	return info, nil
}

// ListObjects lists objects in a bucket with a given prefix
func (c *Client) ListObjects(ctx context.Context, bucket, prefix string) ([]*ObjectInfo, error) {
	var objects []*ObjectInfo

	err := c.s3Client.ListObjectsV2PagesWithContext(ctx, &s3.ListObjectsV2Input{
		Bucket: aws.String(bucket),
		Prefix: aws.String(prefix),
	}, func(page *s3.ListObjectsV2Output, lastPage bool) bool {
		for _, obj := range page.Contents {
			objects = append(objects, &ObjectInfo{
				Key:          aws.StringValue(obj.Key),
				Size:         aws.Int64Value(obj.Size),
				LastModified: aws.TimeValue(obj.LastModified),
				ETag:         aws.StringValue(obj.ETag),
			})
		}
		return !lastPage
	})
	if err != nil {
		return nil, fmt.Errorf("failed to list objects: %w", err)
	}

	return objects, nil
}

// GeneratePresignedURL generates a presigned URL for temporary access to an object
func (c *Client) GeneratePresignedURL(bucket, key string, expiration time.Duration) (string, error) {
	req, _ := c.s3Client.GetObjectRequest(&s3.GetObjectInput{
		Bucket: aws.String(bucket),
		Key:    aws.String(key),
	})

	url, err := req.Presign(expiration)
	if err != nil {
		return "", fmt.Errorf("failed to generate presigned URL: %w", err)
	}

	return url, nil
}

// GeneratePresignedUploadURL generates a presigned URL for uploading an object
func (c *Client) GeneratePresignedUploadURL(bucket, key string, expiration time.Duration) (string, error) {
	req, _ := c.s3Client.PutObjectRequest(&s3.PutObjectInput{
		Bucket: aws.String(bucket),
		Key:    aws.String(key),
	})

	url, err := req.Presign(expiration)
	if err != nil {
		return "", fmt.Errorf("failed to generate presigned upload URL: %w", err)
	}

	return url, nil
}

// CopyObject copies an object from one location to another
func (c *Client) CopyObject(ctx context.Context, sourceBucket, sourceKey, destBucket, destKey string) error {
	_, err := c.s3Client.CopyObjectWithContext(ctx, &s3.CopyObjectInput{
		Bucket:     aws.String(destBucket),
		Key:        aws.String(destKey),
		CopySource: aws.String(fmt.Sprintf("%s/%s", sourceBucket, sourceKey)),
	})
	if err != nil {
		return fmt.Errorf("failed to copy object: %w", err)
	}

	return nil
}

// CreateBucket creates a new bucket
func (c *Client) CreateBucket(ctx context.Context, bucket string) error {
	_, err := c.s3Client.CreateBucketWithContext(ctx, &s3.CreateBucketInput{
		Bucket: aws.String(bucket),
	})
	if err != nil {
		return fmt.Errorf("failed to create bucket: %w", err)
	}

	return nil
}

// BucketExists checks if a bucket exists
func (c *Client) BucketExists(ctx context.Context, bucket string) (bool, error) {
	_, err := c.s3Client.HeadBucketWithContext(ctx, &s3.HeadBucketInput{
		Bucket: aws.String(bucket),
	})
	if err != nil {
		if isNotFoundError(err) {
			return false, nil
		}
		return false, fmt.Errorf("failed to check bucket existence: %w", err)
	}

	return true, nil
}

// isNotFoundError checks if an error is a "not found" error
func isNotFoundError(err error) bool {
	if err == nil {
		return false
	}
	// Check for common "not found" error messages
	errStr := err.Error()
	return contains(errStr, "NotFound") || contains(errStr, "NoSuchKey") || contains(errStr, "NoSuchBucket")
}

// contains checks if a string contains a substring
func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(s) > len(substr) && containsHelper(s, substr))
}

func containsHelper(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}
