package repository

import (
	"context"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/metlab/video/internal/models"
)

// VideoRepository handles database operations for videos
type VideoRepository struct {
	db *pgxpool.Pool
}

// NewVideoRepository creates a new video repository
func NewVideoRepository(db *pgxpool.Pool) *VideoRepository {
	return &VideoRepository{db: db}
}

// CreateVideo creates a new video record
func (r *VideoRepository) CreateVideo(ctx context.Context, video *models.Video) error {
	video.ID = uuid.New().String()
	video.CreatedAt = time.Now()
	video.UpdatedAt = time.Now()

	query := `
		INSERT INTO videos (
			id, teacher_id, class_id, title, description, 
			original_filename, storage_path, duration_seconds, 
			file_size_bytes, status, created_at, updated_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
	`

	_, err := r.db.Exec(ctx, query,
		video.ID, video.TeacherID, video.ClassID, video.Title, video.Description,
		video.OriginalFilename, video.StoragePath, video.DurationSeconds,
		video.FileSizeBytes, video.Status, video.CreatedAt, video.UpdatedAt,
	)

	return err
}

// GetVideoByID retrieves a video by ID
func (r *VideoRepository) GetVideoByID(ctx context.Context, videoID string) (*models.Video, error) {
	query := `
		SELECT id, teacher_id, class_id, title, description, 
			   original_filename, storage_path, duration_seconds, 
			   file_size_bytes, status, created_at, updated_at
		FROM videos
		WHERE id = $1
	`

	var video models.Video
	err := r.db.QueryRow(ctx, query, videoID).Scan(
		&video.ID, &video.TeacherID, &video.ClassID, &video.Title, &video.Description,
		&video.OriginalFilename, &video.StoragePath, &video.DurationSeconds,
		&video.FileSizeBytes, &video.Status, &video.CreatedAt, &video.UpdatedAt,
	)

	if err == pgx.ErrNoRows {
		return nil, fmt.Errorf("video not found")
	}
	if err != nil {
		return nil, err
	}

	return &video, nil
}

// ListVideosByClass retrieves videos for a specific class
func (r *VideoRepository) ListVideosByClass(ctx context.Context, classID string, page, pageSize int32) ([]*models.Video, int32, error) {
	// Get total count
	var totalCount int32
	countQuery := `SELECT COUNT(*) FROM videos WHERE class_id = $1`
	err := r.db.QueryRow(ctx, countQuery, classID).Scan(&totalCount)
	if err != nil {
		return nil, 0, err
	}

	// Get paginated results
	offset := (page - 1) * pageSize
	query := `
		SELECT id, teacher_id, class_id, title, description, 
			   original_filename, storage_path, duration_seconds, 
			   file_size_bytes, status, created_at, updated_at
		FROM videos
		WHERE class_id = $1
		ORDER BY created_at DESC
		LIMIT $2 OFFSET $3
	`

	rows, err := r.db.Query(ctx, query, classID, pageSize, offset)
	if err != nil {
		return nil, 0, err
	}
	defer rows.Close()

	var videos []*models.Video
	for rows.Next() {
		var video models.Video
		err := rows.Scan(
			&video.ID, &video.TeacherID, &video.ClassID, &video.Title, &video.Description,
			&video.OriginalFilename, &video.StoragePath, &video.DurationSeconds,
			&video.FileSizeBytes, &video.Status, &video.CreatedAt, &video.UpdatedAt,
		)
		if err != nil {
			return nil, 0, err
		}
		videos = append(videos, &video)
	}

	return videos, totalCount, nil
}

// UpdateVideoStatus updates the status of a video
func (r *VideoRepository) UpdateVideoStatus(ctx context.Context, videoID, status string) error {
	query := `
		UPDATE videos 
		SET status = $1, updated_at = $2
		WHERE id = $3
	`

	_, err := r.db.Exec(ctx, query, status, time.Now(), videoID)
	return err
}

// UpdateVideoMetadata updates video metadata after processing
func (r *VideoRepository) UpdateVideoMetadata(ctx context.Context, videoID string, durationSeconds int32) error {
	query := `
		UPDATE videos 
		SET duration_seconds = $1, updated_at = $2
		WHERE id = $3
	`

	_, err := r.db.Exec(ctx, query, durationSeconds, time.Now(), videoID)
	return err
}

// CreateVideoVariant creates a new video variant record
func (r *VideoRepository) CreateVideoVariant(ctx context.Context, variant *models.VideoVariant) error {
	variant.ID = uuid.New().String()

	query := `
		INSERT INTO video_variants (
			id, video_id, resolution, bitrate_kbps, storage_path, file_size_bytes
		) VALUES ($1, $2, $3, $4, $5, $6)
	`

	_, err := r.db.Exec(ctx, query,
		variant.ID, variant.VideoID, variant.Resolution,
		variant.BitrateKbps, variant.StoragePath, variant.FileSizeBytes,
	)

	return err
}

// GetVideoVariants retrieves all variants for a video
func (r *VideoRepository) GetVideoVariants(ctx context.Context, videoID string) ([]*models.VideoVariant, error) {
	query := `
		SELECT id, video_id, resolution, bitrate_kbps, storage_path, file_size_bytes
		FROM video_variants
		WHERE video_id = $1
		ORDER BY bitrate_kbps DESC
	`

	rows, err := r.db.Query(ctx, query, videoID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var variants []*models.VideoVariant
	for rows.Next() {
		var variant models.VideoVariant
		err := rows.Scan(
			&variant.ID, &variant.VideoID, &variant.Resolution,
			&variant.BitrateKbps, &variant.StoragePath, &variant.FileSizeBytes,
		)
		if err != nil {
			return nil, err
		}
		variants = append(variants, &variant)
	}

	return variants, nil
}

// CreateVideoThumbnail creates a new video thumbnail record
func (r *VideoRepository) CreateVideoThumbnail(ctx context.Context, thumbnail *models.VideoThumbnail) error {
	thumbnail.ID = uuid.New().String()

	query := `
		INSERT INTO video_thumbnails (
			id, video_id, timestamp_percent, storage_path
		) VALUES ($1, $2, $3, $4)
	`

	_, err := r.db.Exec(ctx, query,
		thumbnail.ID, thumbnail.VideoID, thumbnail.TimestampPercent, thumbnail.StoragePath,
	)

	return err
}

// GetVideoThumbnails retrieves all thumbnails for a video
func (r *VideoRepository) GetVideoThumbnails(ctx context.Context, videoID string) ([]*models.VideoThumbnail, error) {
	query := `
		SELECT id, video_id, timestamp_percent, storage_path
		FROM video_thumbnails
		WHERE video_id = $1
		ORDER BY timestamp_percent ASC
	`

	rows, err := r.db.Query(ctx, query, videoID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var thumbnails []*models.VideoThumbnail
	for rows.Next() {
		var thumbnail models.VideoThumbnail
		err := rows.Scan(
			&thumbnail.ID, &thumbnail.VideoID, &thumbnail.TimestampPercent, &thumbnail.StoragePath,
		)
		if err != nil {
			return nil, err
		}
		thumbnails = append(thumbnails, &thumbnail)
	}

	return thumbnails, nil
}

// RecordVideoView creates or updates a video view record
func (r *VideoRepository) RecordVideoView(ctx context.Context, view *models.VideoView) error {
	// Check if view record exists
	existingID := ""
	checkQuery := `SELECT id FROM video_views WHERE video_id = $1 AND student_id = $2`
	err := r.db.QueryRow(ctx, checkQuery, view.VideoID, view.StudentID).Scan(&existingID)

	if err == pgx.ErrNoRows {
		// Create new record
		view.ID = uuid.New().String()
		view.StartedAt = time.Now()
		view.UpdatedAt = time.Now()

		query := `
			INSERT INTO video_views (
				id, video_id, student_id, started_at, last_position_seconds,
				total_watch_seconds, completed, updated_at
			) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
		`

		_, err = r.db.Exec(ctx, query,
			view.ID, view.VideoID, view.StudentID, view.StartedAt,
			view.LastPositionSeconds, view.TotalWatchSeconds, view.Completed, view.UpdatedAt,
		)
		return err
	} else if err != nil {
		return err
	}

	// Update existing record
	view.UpdatedAt = time.Now()
	query := `
		UPDATE video_views 
		SET last_position_seconds = $1, 
		    total_watch_seconds = total_watch_seconds + $2,
		    completed = $3,
		    updated_at = $4
		WHERE id = $5
	`

	_, err = r.db.Exec(ctx, query,
		view.LastPositionSeconds, view.TotalWatchSeconds, view.Completed, view.UpdatedAt, existingID,
	)
	return err
}

// GetVideoAnalytics retrieves viewing analytics for a video
func (r *VideoRepository) GetVideoAnalytics(ctx context.Context, videoID string) ([]*models.StudentViewData, error) {
	query := `
		SELECT 
			vv.student_id,
			COALESCE(u.full_name, 'Unknown') as student_name,
			CASE 
				WHEN v.duration_seconds > 0 THEN 
					CAST((vv.total_watch_seconds * 100.0 / v.duration_seconds) AS INTEGER)
				ELSE 0
			END as percentage_watched,
			vv.total_watch_seconds,
			vv.completed,
			vv.updated_at as last_viewed_at
		FROM video_views vv
		JOIN videos v ON vv.video_id = v.id
		LEFT JOIN users u ON vv.student_id = u.id
		WHERE vv.video_id = $1
		ORDER BY student_name ASC
	`

	rows, err := r.db.Query(ctx, query, videoID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var analytics []*models.StudentViewData
	for rows.Next() {
		var data models.StudentViewData
		err := rows.Scan(
			&data.StudentID, &data.StudentName, &data.PercentageWatched,
			&data.TotalWatchSeconds, &data.Completed, &data.LastViewedAt,
		)
		if err != nil {
			return nil, err
		}
		analytics = append(analytics, &data)
	}

	return analytics, nil
}

// GetTotalViews returns the total number of views for a video
func (r *VideoRepository) GetTotalViews(ctx context.Context, videoID string) (int32, error) {
	var count int32
	query := `SELECT COUNT(*) FROM video_views WHERE video_id = $1`
	err := r.db.QueryRow(ctx, query, videoID).Scan(&count)
	return count, err
}
