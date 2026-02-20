package repository

import (
	"context"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/metlab/pdf/internal/models"
)

// PDFRepository handles database operations for PDFs
type PDFRepository struct {
	db *pgxpool.Pool
}

// NewPDFRepository creates a new PDF repository
func NewPDFRepository(db *pgxpool.Pool) *PDFRepository {
	return &PDFRepository{db: db}
}

// Create creates a new PDF record in the database
func (r *PDFRepository) Create(ctx context.Context, pdf *models.PDF) error {
	query := `
		INSERT INTO pdfs (
			id, teacher_id, class_id, title, description,
			file_name, storage_path, file_size_bytes, created_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
	`
	
	pdf.ID = uuid.New().String()
	pdf.CreatedAt = time.Now()
	
	_, err := r.db.Exec(ctx, query,
		pdf.ID,
		pdf.TeacherID,
		pdf.ClassID,
		pdf.Title,
		pdf.Description,
		pdf.FileName,
		pdf.StoragePath,
		pdf.FileSizeBytes,
		pdf.CreatedAt,
	)
	
	return err
}

// GetByID retrieves a PDF by its ID
func (r *PDFRepository) GetByID(ctx context.Context, id string) (*models.PDF, error) {
	query := `
		SELECT id, teacher_id, class_id, title, description,
		       file_name, storage_path, file_size_bytes, created_at
		FROM pdfs
		WHERE id = $1
	`
	
	pdf := &models.PDF{}
	err := r.db.QueryRow(ctx, query, id).Scan(
		&pdf.ID,
		&pdf.TeacherID,
		&pdf.ClassID,
		&pdf.Title,
		&pdf.Description,
		&pdf.FileName,
		&pdf.StoragePath,
		&pdf.FileSizeBytes,
		&pdf.CreatedAt,
	)
	
	if err != nil {
		return nil, err
	}
	
	return pdf, nil
}

// ListByClass retrieves all PDFs for a specific class
func (r *PDFRepository) ListByClass(ctx context.Context, classID string) ([]*models.PDF, error) {
	query := `
		SELECT id, teacher_id, class_id, title, description,
		       file_name, storage_path, file_size_bytes, created_at
		FROM pdfs
		WHERE class_id = $1
		ORDER BY created_at DESC
	`
	
	rows, err := r.db.Query(ctx, query, classID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	
	var pdfs []*models.PDF
	for rows.Next() {
		pdf := &models.PDF{}
		err := rows.Scan(
			&pdf.ID,
			&pdf.TeacherID,
			&pdf.ClassID,
			&pdf.Title,
			&pdf.Description,
			&pdf.FileName,
			&pdf.StoragePath,
			&pdf.FileSizeBytes,
			&pdf.CreatedAt,
		)
		if err != nil {
			return nil, err
		}
		pdfs = append(pdfs, pdf)
	}
	
	return pdfs, rows.Err()
}

// RecordDownload records a PDF download event
func (r *PDFRepository) RecordDownload(ctx context.Context, pdfID, studentID string) error {
	query := `
		INSERT INTO pdf_downloads (id, pdf_id, student_id, downloaded_at)
		VALUES ($1, $2, $3, $4)
	`
	
	downloadID := uuid.New().String()
	downloadedAt := time.Now()
	
	_, err := r.db.Exec(ctx, query, downloadID, pdfID, studentID, downloadedAt)
	return err
}

// HasDownloaded checks if a student has downloaded a specific PDF
func (r *PDFRepository) HasDownloaded(ctx context.Context, pdfID, studentID string) (bool, error) {
	query := `
		SELECT EXISTS(
			SELECT 1 FROM pdf_downloads
			WHERE pdf_id = $1 AND student_id = $2
		)
	`
	
	var exists bool
	err := r.db.QueryRow(ctx, query, pdfID, studentID).Scan(&exists)
	return exists, err
}

// Delete removes a PDF record from the database
func (r *PDFRepository) Delete(ctx context.Context, id string) error {
	query := `DELETE FROM pdfs WHERE id = $1`
	_, err := r.db.Exec(ctx, query, id)
	return err
}
