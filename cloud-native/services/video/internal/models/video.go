package models

import (
	"time"
)

// Video represents a video in the database
type Video struct {
	ID               string    `db:"id"`
	TeacherID        string    `db:"teacher_id"`
	ClassID          string    `db:"class_id"`
	Title            string    `db:"title"`
	Description      string    `db:"description"`
	OriginalFilename string    `db:"original_filename"`
	StoragePath      string    `db:"storage_path"`
	DurationSeconds  int32     `db:"duration_seconds"`
	FileSizeBytes    int64     `db:"file_size_bytes"`
	Status           string    `db:"status"` // uploading, processing, ready, failed
	CreatedAt        time.Time `db:"created_at"`
	UpdatedAt        time.Time `db:"updated_at"`
}

// VideoVariant represents a processed video variant (different resolutions)
type VideoVariant struct {
	ID            string `db:"id"`
	VideoID       string `db:"video_id"`
	Resolution    string `db:"resolution"`    // 1080p, 720p, 480p, 360p
	BitrateKbps   int32  `db:"bitrate_kbps"`
	StoragePath   string `db:"storage_path"`
	FileSizeBytes int64  `db:"file_size_bytes"`
}

// VideoThumbnail represents a video thumbnail
type VideoThumbnail struct {
	ID              string `db:"id"`
	VideoID         string `db:"video_id"`
	TimestampPercent int32  `db:"timestamp_percent"` // 0, 25, 50, 75
	StoragePath     string `db:"storage_path"`
}

// VideoView represents a student's video viewing record
type VideoView struct {
	ID                 string    `db:"id"`
	VideoID            string    `db:"video_id"`
	StudentID          string    `db:"student_id"`
	StartedAt          time.Time `db:"started_at"`
	LastPositionSeconds int32     `db:"last_position_seconds"`
	TotalWatchSeconds  int32     `db:"total_watch_seconds"`
	Completed          bool      `db:"completed"`
	UpdatedAt          time.Time `db:"updated_at"`
}

// StudentViewData represents aggregated view data for analytics
type StudentViewData struct {
	StudentID         string
	StudentName       string
	PercentageWatched int32
	TotalWatchSeconds int32
	Completed         bool
	LastViewedAt      time.Time
}
