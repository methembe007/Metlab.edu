package repository

import (
	"context"
	"fmt"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/metlab/analytics/internal/models"
)

// EngagementRepository handles database operations for class engagement metrics
type EngagementRepository struct {
	pool *pgxpool.Pool
}

// NewEngagementRepository creates a new engagement repository
func NewEngagementRepository(pool *pgxpool.Pool) *EngagementRepository {
	return &EngagementRepository{pool: pool}
}

// GetClassEngagement retrieves engagement metrics for all students in a class
func (r *EngagementRepository) GetClassEngagement(ctx context.Context, classID, teacherID uuid.UUID) ([]models.StudentEngagement, models.ClassStats, error) {
	// Query to get student engagement data
	query := `
		SELECT 
			s.id as student_id,
			u.full_name as student_name,
			COALESCE(login_counts.login_count, 0) as total_logins,
			COALESCE(video_counts.video_count, 0) as videos_watched,
			COALESCE(homework_counts.homework_count, 0) as homework_submitted,
			COALESCE(chat_counts.chat_count, 0) as chat_messages
		FROM students s
		INNER JOIN users u ON s.id = u.id
		LEFT JOIN (
			SELECT student_id, COUNT(*) as login_count
			FROM student_logins
			WHERE login_at >= NOW() - INTERVAL '30 days'
			GROUP BY student_id
		) login_counts ON s.id = login_counts.student_id
		LEFT JOIN (
			SELECT student_id, COUNT(DISTINCT video_id) as video_count
			FROM video_views
			WHERE started_at >= NOW() - INTERVAL '30 days'
			GROUP BY student_id
		) video_counts ON s.id = video_counts.student_id
		LEFT JOIN (
			SELECT student_id, COUNT(*) as homework_count
			FROM homework_submissions
			WHERE submitted_at >= NOW() - INTERVAL '30 days'
			GROUP BY student_id
		) homework_counts ON s.id = homework_counts.student_id
		LEFT JOIN (
			SELECT sender_id, COUNT(*) as chat_count
			FROM chat_messages
			WHERE sent_at >= NOW() - INTERVAL '30 days'
			GROUP BY sender_id
		) chat_counts ON s.id = chat_counts.sender_id
		WHERE s.class_id = $1
		ORDER BY u.full_name
	`

	rows, err := r.pool.Query(ctx, query, classID)
	if err != nil {
		return nil, models.ClassStats{}, fmt.Errorf("failed to get class engagement: %w", err)
	}
	defer rows.Close()

	var students []models.StudentEngagement
	var totalLogins, totalVideos, totalHomework int32
	var studentCount int32

	for rows.Next() {
		var student models.StudentEngagement

		if err := rows.Scan(
			&student.StudentID,
			&student.StudentName,
			&student.TotalLogins,
			&student.VideosWatched,
			&student.HomeworkSubmitted,
			&student.ChatMessages,
		); err != nil {
			return nil, models.ClassStats{}, fmt.Errorf("failed to scan student engagement: %w", err)
		}

		// Calculate engagement score (weighted average)
		// Logins: 20%, Videos: 30%, Homework: 40%, Chat: 10%
		student.EngagementScore = (float64(student.TotalLogins) * 0.2) +
			(float64(student.VideosWatched) * 0.3) +
			(float64(student.HomeworkSubmitted) * 0.4) +
			(float64(student.ChatMessages) * 0.1)

		students = append(students, student)

		totalLogins += student.TotalLogins
		totalVideos += student.VideosWatched
		totalHomework += student.HomeworkSubmitted
		studentCount++
	}

	if err := rows.Err(); err != nil {
		return nil, models.ClassStats{}, fmt.Errorf("error iterating student engagement: %w", err)
	}

	// Calculate class statistics
	var classStats models.ClassStats
	classStats.TotalStudents = studentCount

	if studentCount > 0 {
		classStats.AverageLogins = float64(totalLogins) / float64(studentCount)
		classStats.AverageVideosWatched = float64(totalVideos) / float64(studentCount)

		// Get total homework assignments for completion rate
		var totalAssignments int32
		assignmentQuery := `
			SELECT COUNT(*)
			FROM homework_assignments
			WHERE class_id = $1
				AND created_at >= NOW() - INTERVAL '30 days'
		`
		if err := r.pool.QueryRow(ctx, assignmentQuery, classID).Scan(&totalAssignments); err != nil {
			return nil, models.ClassStats{}, fmt.Errorf("failed to get total assignments: %w", err)
		}

		if totalAssignments > 0 {
			expectedSubmissions := totalAssignments * studentCount
			classStats.HomeworkCompletionRate = (float64(totalHomework) / float64(expectedSubmissions)) * 100
		}
	}

	return students, classStats, nil
}
