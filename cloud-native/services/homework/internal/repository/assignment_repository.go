package repository

import (
	"context"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/metlab/homework/internal/models"
)

// AssignmentRepository handles database operations for assignments
type AssignmentRepository struct {
	db *pgxpool.Pool
}

// NewAssignmentRepository creates a new assignment repository
func NewAssignmentRepository(db *pgxpool.Pool) *AssignmentRepository {
	return &AssignmentRepository{db: db}
}

// Create creates a new homework assignment
func (r *AssignmentRepository) Create(ctx context.Context, assignment *models.Assignment) error {
	query := `
		INSERT INTO homework_assignments (id, teacher_id, class_id, title, description, due_date, max_score, created_at, updated_at)
		VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, NOW(), NOW())
		RETURNING id, created_at, updated_at
	`
	
	return r.db.QueryRow(
		ctx,
		query,
		assignment.TeacherID,
		assignment.ClassID,
		assignment.Title,
		assignment.Description,
		assignment.DueDate,
		assignment.MaxScore,
	).Scan(&assignment.ID, &assignment.CreatedAt, &assignment.UpdatedAt)
}

// GetByID retrieves an assignment by ID
func (r *AssignmentRepository) GetByID(ctx context.Context, id string) (*models.Assignment, error) {
	query := `
		SELECT id, teacher_id, class_id, title, description, due_date, max_score, created_at, updated_at
		FROM homework_assignments
		WHERE id = $1
	`
	
	assignment := &models.Assignment{}
	err := r.db.QueryRow(ctx, query, id).Scan(
		&assignment.ID,
		&assignment.TeacherID,
		&assignment.ClassID,
		&assignment.Title,
		&assignment.Description,
		&assignment.DueDate,
		&assignment.MaxScore,
		&assignment.CreatedAt,
		&assignment.UpdatedAt,
	)
	
	if err != nil {
		return nil, err
	}
	
	return assignment, nil
}

// ListByClass retrieves all assignments for a class
func (r *AssignmentRepository) ListByClass(ctx context.Context, classID string) ([]*models.Assignment, error) {
	query := `
		SELECT 
			a.id, a.teacher_id, a.class_id, a.title, a.description, 
			a.due_date, a.max_score, a.created_at, a.updated_at,
			COUNT(DISTINCT s.id) as submission_count,
			COUNT(DISTINCT CASE WHEN s.status = 'graded' THEN s.id END) as graded_count
		FROM homework_assignments a
		LEFT JOIN homework_submissions s ON a.id = s.assignment_id
		WHERE a.class_id = $1
		GROUP BY a.id
		ORDER BY a.due_date DESC
	`
	
	rows, err := r.db.Query(ctx, query, classID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	
	var assignments []*models.Assignment
	for rows.Next() {
		assignment := &models.Assignment{}
		err := rows.Scan(
			&assignment.ID,
			&assignment.TeacherID,
			&assignment.ClassID,
			&assignment.Title,
			&assignment.Description,
			&assignment.DueDate,
			&assignment.MaxScore,
			&assignment.CreatedAt,
			&assignment.UpdatedAt,
			&assignment.SubmissionCount,
			&assignment.GradedCount,
		)
		if err != nil {
			return nil, err
		}
		assignments = append(assignments, assignment)
	}
	
	return assignments, rows.Err()
}

// ListByTeacher retrieves all assignments for a teacher
func (r *AssignmentRepository) ListByTeacher(ctx context.Context, teacherID string) ([]*models.Assignment, error) {
	query := `
		SELECT 
			a.id, a.teacher_id, a.class_id, a.title, a.description, 
			a.due_date, a.max_score, a.created_at, a.updated_at,
			COUNT(DISTINCT s.id) as submission_count,
			COUNT(DISTINCT CASE WHEN s.status = 'graded' THEN s.id END) as graded_count
		FROM homework_assignments a
		LEFT JOIN homework_submissions s ON a.id = s.assignment_id
		WHERE a.teacher_id = $1
		GROUP BY a.id
		ORDER BY a.due_date DESC
	`
	
	rows, err := r.db.Query(ctx, query, teacherID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	
	var assignments []*models.Assignment
	for rows.Next() {
		assignment := &models.Assignment{}
		err := rows.Scan(
			&assignment.ID,
			&assignment.TeacherID,
			&assignment.ClassID,
			&assignment.Title,
			&assignment.Description,
			&assignment.DueDate,
			&assignment.MaxScore,
			&assignment.CreatedAt,
			&assignment.UpdatedAt,
			&assignment.SubmissionCount,
			&assignment.GradedCount,
		)
		if err != nil {
			return nil, err
		}
		assignments = append(assignments, assignment)
	}
	
	return assignments, rows.Err()
}

// Update updates an assignment
func (r *AssignmentRepository) Update(ctx context.Context, assignment *models.Assignment) error {
	query := `
		UPDATE homework_assignments
		SET title = $1, description = $2, due_date = $3, max_score = $4, updated_at = NOW()
		WHERE id = $5
		RETURNING updated_at
	`
	
	return r.db.QueryRow(
		ctx,
		query,
		assignment.Title,
		assignment.Description,
		assignment.DueDate,
		assignment.MaxScore,
		assignment.ID,
	).Scan(&assignment.UpdatedAt)
}

// Delete deletes an assignment
func (r *AssignmentRepository) Delete(ctx context.Context, id string) error {
	query := `DELETE FROM homework_assignments WHERE id = $1`
	_, err := r.db.Exec(ctx, query, id)
	return err
}

// IsLate checks if a submission would be late
func (r *AssignmentRepository) IsLate(ctx context.Context, assignmentID string, submissionTime time.Time) (bool, error) {
	query := `SELECT due_date FROM homework_assignments WHERE id = $1`
	
	var dueDate time.Time
	err := r.db.QueryRow(ctx, query, assignmentID).Scan(&dueDate)
	if err != nil {
		return false, err
	}
	
	return submissionTime.After(dueDate), nil
}
