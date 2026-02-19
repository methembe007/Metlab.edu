package repository

import (
	"context"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgxpool"
)

// PDFRepository handles database operations for PDF downloads
type PDFRepository struct {
	pool *pgxpool.Pool
}

// NewPDFRepository creates a new PDF repository
func NewPDFRepository(pool *pgxpool.Pool) *PDFRepository {
	return &PDFRepository{pool: pool}
}

// RecordPDFDownload records a PDF download event
func (r *PDFRepository) RecordPDFDownload(ctx context.Context, pdfID, studentID uuid.UUID) error {
	query := `
		INSERT INTO pdf_downloads (id, pdf_id, student_id, downloaded_at)
		VALUES ($1, $2, $3, $4)
	`

	_, err := r.pool.Exec(ctx, query,
		uuid.New(),
		pdfID,
		studentID,
		time.Now(),
	)

	if err != nil {
		return fmt.Errorf("failed to record PDF download: %w", err)
	}

	return nil
}
