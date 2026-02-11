package models

import (
	"time"

	"github.com/google/uuid"
)

// UserRole represents the role of a user
type UserRole string

const (
	RoleTeacher UserRole = "teacher"
	RoleStudent UserRole = "student"
)

// User represents a user in the system
type User struct {
	ID           uuid.UUID  `db:"id"`
	Email        *string    `db:"email"`
	PasswordHash *string    `db:"password_hash"`
	FullName     string     `db:"full_name"`
	Role         UserRole   `db:"role"`
	CreatedAt    time.Time  `db:"created_at"`
	UpdatedAt    time.Time  `db:"updated_at"`
	LastLogin    *time.Time `db:"last_login"`
	IsActive     bool       `db:"is_active"`
}

// Teacher represents a teacher user
type Teacher struct {
	ID          uuid.UUID `db:"id"`
	SubjectArea *string   `db:"subject_area"`
	Verified    bool      `db:"verified"`
}

// Student represents a student user
type Student struct {
	ID         uuid.UUID  `db:"id"`
	TeacherID  uuid.UUID  `db:"teacher_id"`
	SigninCode *string    `db:"signin_code"`
}

// SigninCode represents a signin code for student registration
type SigninCode struct {
	Code      string     `db:"code"`
	TeacherID uuid.UUID  `db:"teacher_id"`
	ClassID   uuid.UUID  `db:"class_id"`
	CreatedAt time.Time  `db:"created_at"`
	ExpiresAt time.Time  `db:"expires_at"`
	Used      bool       `db:"used"`
	UsedBy    *uuid.UUID `db:"used_by"`
	UsedAt    *time.Time `db:"used_at"`
}

// LoginAttempt tracks failed login attempts for account lockout
type LoginAttempt struct {
	ID         uuid.UUID `db:"id"`
	Email      string    `db:"email"`
	AttemptAt  time.Time `db:"attempt_at"`
	Successful bool      `db:"successful"`
	IPAddress  *string   `db:"ip_address"`
}
