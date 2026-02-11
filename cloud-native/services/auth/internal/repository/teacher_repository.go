package repository

import (
	"context"
	"fmt"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/metlab/auth/internal/models"
)

// TeacherRepository handles teacher database operations
type TeacherRepository struct {
	pool *pgxpool.Pool
}

// NewTeacherRepository creates a new teacher repository
func NewTeacherRepository(pool *pgxpool.Pool) *TeacherRepository {
	return &TeacherRepository{pool: pool}
}

// CreateTeacher creates a new teacher record
func (r *TeacherRepository) CreateTeacher(ctx context.Context, teacher *models.Teacher) error {
	query := `
		INSERT INTO teachers (id, subject_area, verified)
		VALUES ($1, $2, $3)
	`
	
	_, err := r.pool.Exec(ctx, query,
		teacher.ID,
		teacher.SubjectArea,
		teacher.Verified,
	)
	
	if err != nil {
		return fmt.Errorf("failed to create teacher: %w", err)
	}
	
	return nil
}

// GetTeacherByID retrieves a teacher by ID
func (r *TeacherRepository) GetTeacherByID(ctx context.Context, id uuid.UUID) (*models.Teacher, error) {
	query := `
		SELECT id, subject_area, verified
		FROM teachers
		WHERE id = $1
	`
	
	var teacher models.Teacher
	err := r.pool.QueryRow(ctx, query, id).Scan(
		&teacher.ID,
		&teacher.SubjectArea,
		&teacher.Verified,
	)
	
	if err == pgx.ErrNoRows {
		return nil, fmt.Errorf("teacher not found")
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get teacher: %w", err)
	}
	
	return &teacher, nil
}

// GetTeacherByName retrieves a teacher by full name
func (r *TeacherRepository) GetTeacherByName(ctx context.Context, fullName string) (*models.Teacher, error) {
	query := `
		SELECT t.id, t.subject_area, t.verified
		FROM teachers t
		JOIN users u ON t.id = u.id
		WHERE u.full_name = $1 AND u.role = 'teacher' AND u.is_active = true
	`
	
	var teacher models.Teacher
	err := r.pool.QueryRow(ctx, query, fullName).Scan(
		&teacher.ID,
		&teacher.SubjectArea,
		&teacher.Verified,
	)
	
	if err == pgx.ErrNoRows {
		return nil, fmt.Errorf("teacher not found")
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get teacher: %w", err)
	}
	
	return &teacher, nil
}
