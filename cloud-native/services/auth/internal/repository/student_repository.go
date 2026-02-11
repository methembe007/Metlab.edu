package repository

import (
	"context"
	"fmt"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/metlab/auth/internal/models"
)

// StudentRepository handles student database operations
type StudentRepository struct {
	pool *pgxpool.Pool
}

// NewStudentRepository creates a new student repository
func NewStudentRepository(pool *pgxpool.Pool) *StudentRepository {
	return &StudentRepository{pool: pool}
}

// CreateStudent creates a new student record
func (r *StudentRepository) CreateStudent(ctx context.Context, student *models.Student) error {
	query := `
		INSERT INTO students (id, teacher_id, signin_code)
		VALUES ($1, $2, $3)
	`
	
	_, err := r.pool.Exec(ctx, query,
		student.ID,
		student.TeacherID,
		student.SigninCode,
	)
	
	if err != nil {
		return fmt.Errorf("failed to create student: %w", err)
	}
	
	return nil
}

// GetStudentByID retrieves a student by ID
func (r *StudentRepository) GetStudentByID(ctx context.Context, id uuid.UUID) (*models.Student, error) {
	query := `
		SELECT id, teacher_id, signin_code
		FROM students
		WHERE id = $1
	`
	
	var student models.Student
	err := r.pool.QueryRow(ctx, query, id).Scan(
		&student.ID,
		&student.TeacherID,
		&student.SigninCode,
	)
	
	if err == pgx.ErrNoRows {
		return nil, fmt.Errorf("student not found")
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get student: %w", err)
	}
	
	return &student, nil
}

// GetStudentsByTeacher retrieves all students for a teacher
func (r *StudentRepository) GetStudentsByTeacher(ctx context.Context, teacherID uuid.UUID) ([]*models.Student, error) {
	query := `
		SELECT id, teacher_id, signin_code
		FROM students
		WHERE teacher_id = $1
	`
	
	rows, err := r.pool.Query(ctx, query, teacherID)
	if err != nil {
		return nil, fmt.Errorf("failed to get students: %w", err)
	}
	defer rows.Close()
	
	var students []*models.Student
	for rows.Next() {
		var student models.Student
		if err := rows.Scan(&student.ID, &student.TeacherID, &student.SigninCode); err != nil {
			return nil, fmt.Errorf("failed to scan student: %w", err)
		}
		students = append(students, &student)
	}
	
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating students: %w", err)
	}
	
	return students, nil
}

// GetStudentBySigninCode retrieves a student by signin code
func (r *StudentRepository) GetStudentBySigninCode(ctx context.Context, signinCode string) (*models.Student, error) {
	query := `
		SELECT id, teacher_id, signin_code
		FROM students
		WHERE signin_code = $1
	`
	
	var student models.Student
	err := r.pool.QueryRow(ctx, query, signinCode).Scan(
		&student.ID,
		&student.TeacherID,
		&student.SigninCode,
	)
	
	if err == pgx.ErrNoRows {
		return nil, fmt.Errorf("student not found")
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get student: %w", err)
	}
	
	return &student, nil
}
