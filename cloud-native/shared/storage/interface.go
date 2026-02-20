package storage

import (
	"context"
	"time"
)

// StorageClient defines the interface for object storage operations
type StorageClient interface {
	// Upload uploads byte data to storage
	Upload(ctx context.Context, key string, data []byte) error
	
	// Delete deletes an object from storage
	Delete(ctx context.Context, key string) error
	
	// GetSignedURL generates a presigned URL for downloading with expiration time
	GetSignedURL(ctx context.Context, key string, expiresAt time.Time) (string, error)
}
