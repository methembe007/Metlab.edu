package repository

import (
	"context"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/metlab/homework/internal/models"
)

// GradeRepository handles database operations for grades
type GradeRepository struct {
	db *pgxpool.Pool
}

// NewGradeRepository creates a new grade repository
func NewGradeRepository(db *pgxpool.Pool) *GradeRepository {
	return &GradeRepository{db: db}
}

// Create creates a new grade for a submission
func (r *GradeRepository) Create(ctx context.Context, grade *models.Grade) error {
	query := `
		INSERT INTO homework_grades (id, submission_id, score, feedback, graded_by, graded_at)
		VALUES (gen_random_uuid(), $1, $2, $3, $4, NOW())
		RETURNING id, graded_at
		ON CONFLICT (submission_id)
		DO UPDATE SET
			score = EXCLUDED.score,
			feedback = EXCLUDED.feedback,
			graded_by = EXCLUDED.graded_by,
			graded_at = NOW()
		RETURNING id, graded_at
	`
	
	return r.db.QueryRow(
		ctx,
		query,
		grade.SubmissionID,
		grade.Score,
		grade.Feedback,
		grade.GradedBy,
	).Scan(&grade.ID, &grade.GradedAt)
}

// GetBySubmissionID retrieves a grade by submission ID
func (r *GradeRepository) GetBySubmissionID(ctx context.Context, submissionID string) (*models.Grade, error) {
	query := `
		SELECT id, submission_id, score, feedback, graded_by, graded_at
		FROM homework_grades
		WHERE submission_id = $1
	`
	
	grade := &models.Grade{}
	err := r.db.QueryRow(ctx, query, submissionID).Scan(
		&grade.ID,
		&grade.SubmissionID,
		&grade.Score,
		&grade.Feedback,
		&grade.GradedBy,
		&grade.GradedAt,
	)
	
	if err != nil {
		return nil, err
	}
	
	return grade, nil
}

// Update updates a grade
func (r *GradeRepository) Update(ctx context.Context, grade *models.Grade) error {
	query := `
		UPDATE homework_grades
		SET score = $1, feedback = $2, graded_by = $3, graded_at = NOW()
		WHERE id = $4
		RETURNING graded_at
	`
	
	return r.db.QueryRow(
		ctx,
		query,
		grade.Score,
		grade.Feedback,
		grade.GradedBy,
		grade.ID,
	).Scan(&grade.GradedAt)
}

// Delete deletes a grade
func (r *GradeRepository) Delete(ctx context.Context, id string) error {
	query := `DELETE FROM homework_grades WHERE id = $1`
	_, err := r.db.Exec(ctx, query, id)
	return err
}

// GetClassAverageForAssignment calculates the average score for an assignment
func (r *GradeRepository) GetClassAverageForAssignment(ctx context.Context, assignmentID string) (float64, error) {
	query := `
		SELECT COALESCE(AVG(g.score), 0)
		FROM homework_grades g
		JOIN homework_submissions s ON g.submission_id = s.id
		WHERE s.assignment_id = $1
	`
	
	var average float64
	err := r.db.QueryRow(ctx, query, assignmentID).Scan(&average)
	return average, err
}
