package repository

import (
	"context"
	"fmt"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/metlab/collaboration/internal/models"
)

// StudyGroupRepository handles database operations for study groups
type StudyGroupRepository struct {
	pool *pgxpool.Pool
}

// NewStudyGroupRepository creates a new study group repository
func NewStudyGroupRepository(pool *pgxpool.Pool) *StudyGroupRepository {
	return &StudyGroupRepository{pool: pool}
}

// Create creates a new study group
func (r *StudyGroupRepository) Create(ctx context.Context, group *models.StudyGroup) error {
	query := `
		INSERT INTO study_groups (id, class_id, name, description, created_by, max_members)
		VALUES ($1, $2, $3, $4, $5, $6)
		RETURNING created_at
	`
	
	err := r.pool.QueryRow(
		ctx,
		query,
		group.ID,
		group.ClassID,
		group.Name,
		group.Description,
		group.CreatedBy,
		group.MaxMembers,
	).Scan(&group.CreatedAt)
	
	if err != nil {
		return fmt.Errorf("failed to create study group: %w", err)
	}
	
	return nil
}

// GetByID retrieves a study group by ID
func (r *StudyGroupRepository) GetByID(ctx context.Context, id string) (*models.StudyGroup, error) {
	query := `
		SELECT id, class_id, name, description, created_by, created_at, max_members
		FROM study_groups
		WHERE id = $1
	`
	
	var group models.StudyGroup
	err := r.pool.QueryRow(ctx, query, id).Scan(
		&group.ID,
		&group.ClassID,
		&group.Name,
		&group.Description,
		&group.CreatedBy,
		&group.CreatedAt,
		&group.MaxMembers,
	)
	
	if err == pgx.ErrNoRows {
		return nil, fmt.Errorf("study group not found")
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get study group: %w", err)
	}
	
	return &group, nil
}

// ListByClass retrieves all study groups for a class
func (r *StudyGroupRepository) ListByClass(ctx context.Context, classID string) ([]*models.StudyGroup, error) {
	query := `
		SELECT id, class_id, name, description, created_by, created_at, max_members
		FROM study_groups
		WHERE class_id = $1
		ORDER BY created_at DESC
	`
	
	rows, err := r.pool.Query(ctx, query, classID)
	if err != nil {
		return nil, fmt.Errorf("failed to list study groups: %w", err)
	}
	defer rows.Close()
	
	var groups []*models.StudyGroup
	for rows.Next() {
		var group models.StudyGroup
		err := rows.Scan(
			&group.ID,
			&group.ClassID,
			&group.Name,
			&group.Description,
			&group.CreatedBy,
			&group.CreatedAt,
			&group.MaxMembers,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan study group: %w", err)
		}
		groups = append(groups, &group)
	}
	
	return groups, nil
}

// GetMemberCount returns the number of members in a study group
func (r *StudyGroupRepository) GetMemberCount(ctx context.Context, groupID string) (int32, error) {
	query := `SELECT COUNT(*) FROM study_group_members WHERE study_group_id = $1`
	
	var count int32
	err := r.pool.QueryRow(ctx, query, groupID).Scan(&count)
	if err != nil {
		return 0, fmt.Errorf("failed to get member count: %w", err)
	}
	
	return count, nil
}

// AddMember adds a student to a study group
func (r *StudyGroupRepository) AddMember(ctx context.Context, member *models.StudyGroupMember) error {
	query := `
		INSERT INTO study_group_members (study_group_id, student_id)
		VALUES ($1, $2)
		RETURNING joined_at
	`
	
	err := r.pool.QueryRow(ctx, query, member.StudyGroupID, member.StudentID).Scan(&member.JoinedAt)
	if err != nil {
		return fmt.Errorf("failed to add member: %w", err)
	}
	
	return nil
}

// IsMember checks if a student is a member of a study group
func (r *StudyGroupRepository) IsMember(ctx context.Context, groupID, studentID string) (bool, error) {
	query := `
		SELECT EXISTS(
			SELECT 1 FROM study_group_members 
			WHERE study_group_id = $1 AND student_id = $2
		)
	`
	
	var exists bool
	err := r.pool.QueryRow(ctx, query, groupID, studentID).Scan(&exists)
	if err != nil {
		return false, fmt.Errorf("failed to check membership: %w", err)
	}
	
	return exists, nil
}

// GetStudentGroupCount returns the number of groups a student has joined
func (r *StudyGroupRepository) GetStudentGroupCount(ctx context.Context, studentID string) (int32, error) {
	query := `SELECT COUNT(*) FROM study_group_members WHERE student_id = $1`
	
	var count int32
	err := r.pool.QueryRow(ctx, query, studentID).Scan(&count)
	if err != nil {
		return 0, fmt.Errorf("failed to get student group count: %w", err)
	}
	
	return count, nil
}
