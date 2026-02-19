package models

import (
	"time"

	"github.com/google/uuid"
)

// StudentLogin represents a student login event
type StudentLogin struct {
	ID        uuid.UUID `db:"id"`
	StudentID uuid.UUID `db:"student_id"`
	LoginAt   time.Time `db:"login_at"`
	IPAddress string    `db:"ip_address"`
	UserAgent string    `db:"user_agent"`
}

// PDFDownload represents a PDF download event
type PDFDownload struct {
	ID           uuid.UUID `db:"id"`
	PDFID        uuid.UUID `db:"pdf_id"`
	StudentID    uuid.UUID `db:"student_id"`
	DownloadedAt time.Time `db:"downloaded_at"`
}

// DailyLoginCount represents login count for a specific date
type DailyLoginCount struct {
	Date  string
	Count int32
}

// StudentEngagement represents engagement metrics for a student
type StudentEngagement struct {
	StudentID         uuid.UUID
	StudentName       string
	TotalLogins       int32
	VideosWatched     int32
	HomeworkSubmitted int32
	ChatMessages      int32
	EngagementScore   float64
}

// ClassStats represents aggregated statistics for a class
type ClassStats struct {
	AverageLogins            float64
	AverageVideosWatched     float64
	HomeworkCompletionRate   float64
	TotalStudents            int32
}
