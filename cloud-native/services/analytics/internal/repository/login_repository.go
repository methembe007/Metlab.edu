package repository

import (
	"context"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/metlab/analytics/internal/models"
)

// LoginRepository handles database operations for student logins
type LoginRepository struct {
	pool *pgxpool.Pool
}

// NewLoginRepository creates a new login repository
func NewLoginRepository(pool *pgxpool.Pool) *LoginRepository {
	return &LoginRepository{pool: pool}
}

// RecordLogin records a student login event
func (r *LoginRepository) RecordLogin(ctx context.Context, studentID uuid.UUID, ipAddress, userAgent string) error {
	query := `
		INSERT INTO student_logins (id, student_id, login_at, ip_address, user_agent)
		VALUES ($1, $2, $3, $4, $5)
	`

	_, err := r.pool.Exec(ctx, query,
		uuid.New(),
		studentID,
		time.Now(),
		ipAddress,
		userAgent,
	)

	if err != nil {
		return fmt.Errorf("failed to record login: %w", err)
	}

	return nil
}

// GetStudentLoginStats retrieves login statistics for a student
func (r *LoginRepository) GetStudentLoginStats(ctx context.Context, studentID uuid.UUID, days int32) ([]models.DailyLoginCount, int32, float64, error) {
	// Get daily login counts
	query := `
		SELECT 
			DATE(login_at) as date,
			COUNT(*) as count
		FROM student_logins
		WHERE student_id = $1
			AND login_at >= NOW() - INTERVAL '1 day' * $2
		GROUP BY DATE(login_at)
		ORDER BY date DESC
	`

	rows, err := r.pool.Query(ctx, query, studentID, days)
	if err != nil {
		return nil, 0, 0, fmt.Errorf("failed to get daily login counts: %w", err)
	}
	defer rows.Close()

	var dailyCounts []models.DailyLoginCount
	var totalLogins int32

	for rows.Next() {
		var date time.Time
		var count int32

		if err := rows.Scan(&date, &count); err != nil {
			return nil, 0, 0, fmt.Errorf("failed to scan daily login count: %w", err)
		}

		dailyCounts = append(dailyCounts, models.DailyLoginCount{
			Date:  date.Format("2006-01-02"),
			Count: count,
		})
		totalLogins += count
	}

	if err := rows.Err(); err != nil {
		return nil, 0, 0, fmt.Errorf("error iterating daily login counts: %w", err)
	}

	// Calculate average per week
	var averagePerWeek float64
	if days > 0 {
		weeks := float64(days) / 7.0
		if weeks < 1 {
			weeks = 1
		}
		averagePerWeek = float64(totalLogins) / weeks
	}

	return dailyCounts, totalLogins, averagePerWeek, nil
}

// GetClassLoginStats retrieves login statistics for all students in a class
func (r *LoginRepository) GetClassLoginStats(ctx context.Context, classID uuid.UUID) (map[uuid.UUID]int32, error) {
	query := `
		SELECT 
			sl.student_id,
			COUNT(*) as login_count
		FROM student_logins sl
		INNER JOIN students s ON sl.student_id = s.id
		WHERE s.class_id = $1
			AND sl.login_at >= NOW() - INTERVAL '30 days'
		GROUP BY sl.student_id
	`

	rows, err := r.pool.Query(ctx, query, classID)
	if err != nil {
		return nil, fmt.Errorf("failed to get class login stats: %w", err)
	}
	defer rows.Close()

	loginStats := make(map[uuid.UUID]int32)

	for rows.Next() {
		var studentID uuid.UUID
		var loginCount int32

		if err := rows.Scan(&studentID, &loginCount); err != nil {
			return nil, fmt.Errorf("failed to scan login stats: %w", err)
		}

		loginStats[studentID] = loginCount
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating login stats: %w", err)
	}

	return loginStats, nil
}
