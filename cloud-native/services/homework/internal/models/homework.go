package models

import (
	"time"
)

// Assignment represents a homework assignment
type Assignment struct {
	ID              string
	TeacherID       string
	ClassID         string
	Title           string
	Description     string
	DueDate         time.Time
	MaxScore        int32
	CreatedAt       time.Time
	UpdatedAt       time.Time
	SubmissionCount int32
	GradedCount     int32
}

// Submission represents a homework submission by a student
type Submission struct {
	ID           string
	AssignmentID string
	StudentID    string
	StudentName  string
	FilePath     string
	FileName     string
	FileSizeBytes int64
	SubmittedAt  time.Time
	IsLate       bool
	Status       string // 'submitted', 'graded', 'returned'
	Grade        *Grade
}

// Grade represents a grade for a homework submission
type Grade struct {
	ID           string
	SubmissionID string
	Score        int32
	Feedback     string
	GradedBy     string
	GradedAt     time.Time
}

// SubmissionStatus constants
const (
	StatusSubmitted = "submitted"
	StatusGraded    = "graded"
	StatusReturned  = "returned"
)
