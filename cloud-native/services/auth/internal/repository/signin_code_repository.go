package repository

import (
	"context"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/metlab/auth/internal/models"
)

// SigninCodeRepository handles signin code database operations
type SigninCodeRepository struct {
	pool *pgxpool.Pool
}

// NewSigninCodeRepository creates a new signin code repository
func NewSigninCodeRepository(pool *pgxpool.Pool) *SigninCodeRepository {
	return &SigninCodeRepository{pool: pool}
}

// CreateSigninCode creates a new signin code
func (r *SigninCodeRepository) CreateSigninCode(ctx context.Context, code *models.SigninCode) error {
	query := `
		INSERT INTO signin_codes (code, teacher_id, class_id, created_at, expires_at, used)
		VALUES ($1, $2, $3, $4, $5, $6)
	`
	
	_, err := r.pool.Exec(ctx, query,
		code.Code,
		code.TeacherID,
		code.ClassID,
		code.CreatedAt,
		code.ExpiresAt,
		code.Used,
	)
	
	if err != nil {
		return fmt.Errorf("failed to create signin code: %w", err)
	}
	
	return nil
}

// GetSigninCode retrieves a signin code by code string
func (r *SigninCodeRepository) GetSigninCode(ctx context.Context, code string) (*models.SigninCode, error) {
	query := `
		SELECT code, teacher_id, class_id, created_at, expires_at, used, used_by, used_at
		FROM signin_codes
		WHERE code = $1
	`
	
	var signinCode models.SigninCode
	err := r.pool.QueryRow(ctx, query, code).Scan(
		&signinCode.Code,
		&signinCode.TeacherID,
		&signinCode.ClassID,
		&signinCode.CreatedAt,
		&signinCode.ExpiresAt,
		&signinCode.Used,
		&signinCode.UsedBy,
		&signinCode.UsedAt,
	)
	
	if err == pgx.ErrNoRows {
		return nil, fmt.Errorf("signin code not found")
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get signin code: %w", err)
	}
	
	return &signinCode, nil
}

// MarkSigninCodeAsUsed marks a signin code as used
func (r *SigninCodeRepository) MarkSigninCodeAsUsed(ctx context.Context, code string, userID uuid.UUID) error {
	query := `
		UPDATE signin_codes
		SET used = true, used_by = $1, used_at = $2
		WHERE code = $3
	`
	
	now := time.Now()
	_, err := r.pool.Exec(ctx, query, userID, now, code)
	if err != nil {
		return fmt.Errorf("failed to mark signin code as used: %w", err)
	}
	
	return nil
}

// CodeExists checks if a signin code already exists
func (r *SigninCodeRepository) CodeExists(ctx context.Context, code string) (bool, error) {
	query := `SELECT EXISTS(SELECT 1 FROM signin_codes WHERE code = $1)`
	
	var exists bool
	err := r.pool.QueryRow(ctx, query, code).Scan(&exists)
	if err != nil {
		return false, fmt.Errorf("failed to check code existence: %w", err)
	}
	
	return exists, nil
}

// IsCodeValid checks if a signin code is valid (not used and not expired)
func (r *SigninCodeRepository) IsCodeValid(ctx context.Context, code string) (bool, error) {
	query := `
		SELECT EXISTS(
			SELECT 1 FROM signin_codes 
			WHERE code = $1 AND used = false AND expires_at > $2
		)
	`
	
	var valid bool
	err := r.pool.QueryRow(ctx, query, code, time.Now()).Scan(&valid)
	if err != nil {
		return false, fmt.Errorf("failed to check code validity: %w", err)
	}
	
	return valid, nil
}
