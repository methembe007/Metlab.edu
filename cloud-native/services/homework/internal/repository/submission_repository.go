package repository

import (
	"context"
	"database/sql"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/metlab/homework/internal/models"
)

// SubmissionRepository handles database operations for submissions
type SubmissionRepository struct {
	db *pgxpool.Pool
}

// NewSubmissionRepository creates a new submission repository
func NewSubmissionRepository(db *pgxpool.Pool) *SubmissionRepository {
	return &SubmissionRepository{db: db}
}

// Create creates a new homework submission
func (r *SubmissionRepository) Create(ctx context.Context, submission *models.Submission) error {
	query := `
		INSERT INTO homework_submissions (
			id, assignment_id, student_id, file_path, file_name, 
			file_size_bytes, submitted_at, is_late, status
		)
		VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, NOW(), $6, $7)
		RETURNING id, submitted_at
		ON CONFLICT (assignment_id, student_id) 
		DO UPDATE SET 
			file_path = EXCLUDED.file_path,
			file_name = EXCLUDED.file_name,
			file_size_bytes = EXCLUDED.file_size_bytes,
			submitted_at = NOW(),
			is_late = EXCLUDED.is_late,
			status = EXCLUDED.status
		RETURNING id, submitted_at
	`
	
	return r.db.QueryRow(
		ctx,
		query,
		submission.AssignmentID,
		submission.StudentID,
		submission.FilePath,
		submission.FileName,
		submission.FileSizeBytes,
		submission.IsLate,
		submission.Status,
	).Scan(&submission.ID, &submission.SubmittedAt)
}

// GetByID retrieves a submission by ID
func (r *SubmissionRepository) GetByID(ctx context.Context, id string) (*models.Submission, error) {
	query := `
		SELECT 
			s.id, s.assignment_id, s.student_id, s.file_path, s.file_name,
			s.file_size_bytes, s.submitted_at, s.is_late, s.status,
			u.full_name as student_name,
			g.id, g.score, g.feedback, g.graded_by, g.graded_at
		FROM homework_submissions s
		JOIN users u ON s.student_id = u.id
		LEFT JOIN homework_grades g ON s.id = g.submission_id
		WHERE s.id = $1
	`
	
	submission := &models.Submission{}
	var gradeID, gradedBy sql.NullString
	var score sql.NullInt32
	var feedback sql.NullString
	var gradedAt sql.NullTime
	
	err := r.db.QueryRow(ctx, query, id).Scan(
		&submission.ID,
		&submission.AssignmentID,
		&submission.StudentID,
		&submission.FilePath,
		&submission.FileName,
		&submission.FileSizeBytes,
		&submission.SubmittedAt,
		&submission.IsLate,
		&submission.Status,
		&submission.StudentName,
		&gradeID,
		&score,
		&feedback,
		&gradedBy,
		&gradedAt,
	)
	
	if err != nil {
		return nil, err
	}
	
	// Populate grade if it exists
	if gradeID.Valid {
		submission.Grade = &models.Grade{
			ID:           gradeID.String,
			SubmissionID: submission.ID,
			Score:        score.Int32,
			Feedback:     feedback.String,
			GradedBy:     gradedBy.String,
			GradedAt:     gradedAt.Time,
		}
	}
	
	return submission, nil
}

// ListByAssignment retrieves all submissions for an assignment
func (r *SubmissionRepository) ListByAssignment(ctx context.Context, assignmentID string, statusFilter string) ([]*models.Submission, error) {
	query := `
		SELECT 
			s.id, s.assignment_id, s.student_id, s.file_path, s.file_name,
			s.file_size_bytes, s.submitted_at, s.is_late, s.status,
			u.full_name as student_name,
			g.id, g.score, g.feedback, g.graded_by, g.graded_at
		FROM homework_submissions s
		JOIN users u ON s.student_id = u.id
		LEFT JOIN homework_grades g ON s.id = g.submission_id
		WHERE s.assignment_id = $1
	`
	
	args := []interface{}{assignmentID}
	
	if statusFilter != "" {
		query += ` AND s.status = $2`
		args = append(args, statusFilter)
	}
	
	query += ` ORDER BY s.submitted_at DESC`
	
	rows, err := r.db.Query(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	
	var submissions []*models.Submission
	for rows.Next() {
		submission := &models.Submission{}
		var gradeID, gradedBy sql.NullString
		var score sql.NullInt32
		var feedback sql.NullString
		var gradedAt sql.NullTime
		
		err := rows.Scan(
			&submission.ID,
			&submission.AssignmentID,
			&submission.StudentID,
			&submission.FilePath,
			&submission.FileName,
			&submission.FileSizeBytes,
			&submission.SubmittedAt,
			&submission.IsLate,
			&submission.Status,
			&submission.StudentName,
			&gradeID,
			&score,
			&feedback,
			&gradedBy,
			&gradedAt,
		)
		if err != nil {
			return nil, err
		}
		
		// Populate grade if it exists
		if gradeID.Valid {
			submission.Grade = &models.Grade{
				ID:           gradeID.String,
				SubmissionID: submission.ID,
				Score:        score.Int32,
				Feedback:     feedback.String,
				GradedBy:     gradedBy.String,
				GradedAt:     gradedAt.Time,
			}
		}
		
		submissions = append(submissions, submission)
	}
	
	return submissions, rows.Err()
}

// ListByStudent retrieves all submissions for a student
func (r *SubmissionRepository) ListByStudent(ctx context.Context, studentID string) ([]*models.Submission, error) {
	query := `
		SELECT 
			s.id, s.assignment_id, s.student_id, s.file_path, s.file_name,
			s.file_size_bytes, s.submitted_at, s.is_late, s.status,
			u.full_name as student_name,
			g.id, g.score, g.feedback, g.graded_by, g.graded_at
		FROM homework_submissions s
		JOIN users u ON s.student_id = u.id
		LEFT JOIN homework_grades g ON s.id = g.submission_id
		WHERE s.student_id = $1
		ORDER BY s.submitted_at DESC
	`
	
	rows, err := r.db.Query(ctx, query, studentID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	
	var submissions []*models.Submission
	for rows.Next() {
		submission := &models.Submission{}
		var gradeID, gradedBy sql.NullString
		var score sql.NullInt32
		var feedback sql.NullString
		var gradedAt sql.NullTime
		
		err := rows.Scan(
			&submission.ID,
			&submission.AssignmentID,
			&submission.StudentID,
			&submission.FilePath,
			&submission.FileName,
			&submission.FileSizeBytes,
			&submission.SubmittedAt,
			&submission.IsLate,
			&submission.Status,
			&submission.StudentName,
			&gradeID,
			&score,
			&feedback,
			&gradedBy,
			&gradedAt,
		)
		if err != nil {
			return nil, err
		}
		
		// Populate grade if it exists
		if gradeID.Valid {
			submission.Grade = &models.Grade{
				ID:           gradeID.String,
				SubmissionID: submission.ID,
				Score:        score.Int32,
				Feedback:     feedback.String,
				GradedBy:     gradedBy.String,
				GradedAt:     gradedAt.Time,
			}
		}
		
		submissions = append(submissions, submission)
	}
	
	return submissions, rows.Err()
}

// UpdateStatus updates the status of a submission
func (r *SubmissionRepository) UpdateStatus(ctx context.Context, id string, status string) error {
	query := `UPDATE homework_submissions SET status = $1 WHERE id = $2`
	_, err := r.db.Exec(ctx, query, status, id)
	return err
}

// Delete deletes a submission
func (r *SubmissionRepository) Delete(ctx context.Context, id string) error {
	query := `DELETE FROM homework_submissions WHERE id = $1`
	_, err := r.db.Exec(ctx, query, id)
	return err
}

// Exists checks if a submission exists for a student and assignment
func (r *SubmissionRepository) Exists(ctx context.Context, assignmentID, studentID string) (bool, error) {
	query := `SELECT EXISTS(SELECT 1 FROM homework_submissions WHERE assignment_id = $1 AND student_id = $2)`
	
	var exists bool
	err := r.db.QueryRow(ctx, query, assignmentID, studentID).Scan(&exists)
	return exists, err
}
