package models

import (
	"time"
)

// PDF represents a PDF document in the system
type PDF struct {
	ID            string
	TeacherID     string
	ClassID       string
	Title         string
	Description   string
	FileName      string
	StoragePath   string
	FileSizeBytes int64
	CreatedAt     time.Time
}

// PDFDownload represents a PDF download event for analytics
type PDFDownload struct {
	ID           string
	PDFID        string
	StudentID    string
	DownloadedAt time.Time
}
