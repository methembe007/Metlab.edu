package repository

import (
	"context"
	"fmt"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/metlab/auth/internal/models"
)

// LoginAttemptRepository handles login attempt database operations
type LoginAttemptRepository struct {
	pool *pgxpool.Pool
}

// NewLoginAttemptRepository creates a new login attempt repository
func NewLoginAttemptRepository(pool *pgxpool.Pool) *LoginAttemptRepository {
	return &LoginAttemptRepository{pool: pool}
}

// RecordLoginAttempt records a login attempt
func (r *LoginAttemptRepository) RecordLoginAttempt(ctx context.Context, attempt *models.LoginAttempt) error {
	query := `
		INSERT INTO login_attempts (id, email, attempt_at, successful, ip_address)
		VALUES ($1, $2, $3, $4, $5)
	`
	
	_, err := r.pool.Exec(ctx, query,
		attempt.ID,
		attempt.Email,
		attempt.AttemptAt,
		attempt.Successful,
		attempt.IPAddress,
	)
	
	if err != nil {
		return fmt.Errorf("failed to record login attempt: %w", err)
	}
	
	return nil
}

// GetRecentFailedAttempts gets the count of recent failed login attempts
func (r *LoginAttemptRepository) GetRecentFailedAttempts(ctx context.Context, email string, since time.Time) (int, error) {
	query := `
		SELECT COUNT(*)
		FROM login_attempts
		WHERE email = $1 AND successful = false AND attempt_at > $2
	`
	
	var count int
	err := r.pool.QueryRow(ctx, query, email, since).Scan(&count)
	if err != nil {
		return 0, fmt.Errorf("failed to get recent failed attempts: %w", err)
	}
	
	return count, nil
}

// HasRecentSuccessfulLogin checks if there was a successful login after the given time
func (r *LoginAttemptRepository) HasRecentSuccessfulLogin(ctx context.Context, email string, since time.Time) (bool, error) {
	query := `
		SELECT EXISTS(
			SELECT 1 FROM login_attempts
			WHERE email = $1 AND successful = true AND attempt_at > $2
		)
	`
	
	var exists bool
	err := r.pool.QueryRow(ctx, query, email, since).Scan(&exists)
	if err != nil {
		return false, fmt.Errorf("failed to check recent successful login: %w", err)
	}
	
	return exists, nil
}
