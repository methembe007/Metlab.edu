package handler

import (
	"context"
	"fmt"
	"io"
	"path/filepath"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/metlab/pdf/internal/models"
	"github.com/metlab/pdf/internal/repository"
	"github.com/metlab/shared/logger"
	"github.com/metlab/shared/storage"
	pb "metlab/proto-gen/go/pdf"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

// PDFHandler implements the PDF service gRPC server
type PDFHandler struct {
	pb.UnimplementedPDFServiceServer
	repo          *repository.PDFRepository
	storage       storage.StorageClient
	logger        *logger.Logger
	maxUploadSize int64
}

// NewPDFHandler creates a new PDF handler
func NewPDFHandler(
	db *pgxpool.Pool,
	storageClient storage.StorageClient,
	logger *logger.Logger,
	maxUploadSize int64,
) *PDFHandler {
	return &PDFHandler{
		repo:          repository.NewPDFRepository(db),
		storage:       storageClient,
		logger:        logger,
		maxUploadSize: maxUploadSize,
	}
}

// UploadPDF handles streaming PDF upload
func (h *PDFHandler) UploadPDF(stream pb.PDFService_UploadPDFServer) error {
	ctx := stream.Context()
	
	// Receive metadata first
	req, err := stream.Recv()
	if err != nil {
		h.logger.Error("Failed to receive metadata", err)
		return status.Error(codes.Internal, "failed to receive metadata")
	}
	
	metadata := req.GetMetadata()
	if metadata == nil {
		return status.Error(codes.InvalidArgument, "first message must contain metadata")
	}
	
	// Validate metadata
	if metadata.TeacherId == "" {
		return status.Error(codes.InvalidArgument, "teacher_id is required")
	}
	if metadata.ClassId == "" {
		return status.Error(codes.InvalidArgument, "class_id is required")
	}
	if metadata.Title == "" {
		return status.Error(codes.InvalidArgument, "title is required")
	}
	if metadata.Filename == "" {
		return status.Error(codes.InvalidArgument, "filename is required")
	}
	
	// Validate file size
	if metadata.FileSize > h.maxUploadSize {
		return status.Errorf(codes.InvalidArgument, 
			"file size %d exceeds maximum allowed size %d", 
			metadata.FileSize, h.maxUploadSize)
	}
	
	// Validate file extension
	ext := filepath.Ext(metadata.Filename)
	if ext != ".pdf" && ext != ".PDF" {
		return status.Error(codes.InvalidArgument, "only PDF files are allowed")
	}
	
	h.logger.Info("Starting PDF upload", map[string]interface{}{
		"teacher_id": metadata.TeacherId,
		"class_id":   metadata.ClassId,
		"title":      metadata.Title,
		"filename":   metadata.Filename,
		"file_size":  metadata.FileSize,
	})
	
	// Generate storage path
	timestamp := time.Now().Unix()
	storagePath := fmt.Sprintf("pdfs/%s/%s/%d_%s",
		metadata.ClassId,
		metadata.TeacherId,
		timestamp,
		metadata.Filename,
	)
	
	// Create a buffer to collect file chunks
	var fileData []byte
	var totalSize int64
	
	// Receive file chunks
	for {
		req, err := stream.Recv()
		if err == io.EOF {
			break
		}
		if err != nil {
			h.logger.Error("Failed to receive chunk", err)
			return status.Error(codes.Internal, "failed to receive file data")
		}
		
		chunk := req.GetChunk()
		if chunk == nil {
			continue
		}
		
		totalSize += int64(len(chunk))
		if totalSize > h.maxUploadSize {
			return status.Error(codes.InvalidArgument, "file size exceeds maximum allowed size")
		}
		
		fileData = append(fileData, chunk...)
	}
	
	// Verify received size matches metadata
	if totalSize != metadata.FileSize {
		h.logger.Warn("File size mismatch", map[string]interface{}{
			"expected": metadata.FileSize,
			"received": totalSize,
		})
	}
	
	// Upload to S3
	err = h.storage.Upload(ctx, storagePath, fileData)
	if err != nil {
		h.logger.Error("Failed to upload to storage", err)
		return status.Error(codes.Internal, "failed to upload file")
	}
	
	h.logger.Info("PDF uploaded to storage", map[string]interface{}{
		"storage_path": storagePath,
		"size":         totalSize,
	})
	
	// Create database record
	pdf := &models.PDF{
		TeacherID:     metadata.TeacherId,
		ClassID:       metadata.ClassId,
		Title:         metadata.Title,
		Description:   metadata.Description,
		FileName:      metadata.Filename,
		StoragePath:   storagePath,
		FileSizeBytes: totalSize,
	}
	
	err = h.repo.Create(ctx, pdf)
	if err != nil {
		h.logger.Error("Failed to create PDF record", err)
		// Try to clean up uploaded file
		_ = h.storage.Delete(ctx, storagePath)
		return status.Error(codes.Internal, "failed to create PDF record")
	}
	
	h.logger.Info("PDF record created", map[string]interface{}{
		"pdf_id": pdf.ID,
	})
	
	// Send response
	return stream.SendAndClose(&pb.UploadPDFResponse{
		PdfId:  pdf.ID,
		Status: "uploaded",
	})
}

// ListPDFs returns a list of PDFs for a class
func (h *PDFHandler) ListPDFs(ctx context.Context, req *pb.ListPDFsRequest) (*pb.ListPDFsResponse, error) {
	if req.ClassId == "" {
		return nil, status.Error(codes.InvalidArgument, "class_id is required")
	}
	
	h.logger.Debug("Listing PDFs", map[string]interface{}{
		"class_id": req.ClassId,
		"user_id":  req.UserId,
	})
	
	// Get PDFs from database
	pdfs, err := h.repo.ListByClass(ctx, req.ClassId)
	if err != nil {
		h.logger.Error("Failed to list PDFs", err)
		return nil, status.Error(codes.Internal, "failed to retrieve PDFs")
	}
	
	// Convert to proto messages
	var pbPDFs []*pb.PDF
	for _, pdf := range pdfs {
		// Check if user has downloaded this PDF
		downloaded := false
		if req.UserId != "" {
			downloaded, _ = h.repo.HasDownloaded(ctx, pdf.ID, req.UserId)
		}
		
		pbPDFs = append(pbPDFs, &pb.PDF{
			Id:                pdf.ID,
			Title:             pdf.Title,
			Description:       pdf.Description,
			FileSizeBytes:     pdf.FileSizeBytes,
			CreatedAt:         pdf.CreatedAt.Unix(),
			Filename:          pdf.FileName,
			DownloadedByUser:  downloaded,
		})
	}
	
	h.logger.Info("PDFs listed", map[string]interface{}{
		"count": len(pbPDFs),
	})
	
	return &pb.ListPDFsResponse{
		Pdfs: pbPDFs,
	}, nil
}

// GetDownloadURL generates a signed download URL for a PDF
func (h *PDFHandler) GetDownloadURL(ctx context.Context, req *pb.GetDownloadURLRequest) (*pb.DownloadURLResponse, error) {
	if req.PdfId == "" {
		return nil, status.Error(codes.InvalidArgument, "pdf_id is required")
	}
	if req.UserId == "" {
		return nil, status.Error(codes.InvalidArgument, "user_id is required")
	}
	
	h.logger.Debug("Generating download URL", map[string]interface{}{
		"pdf_id":  req.PdfId,
		"user_id": req.UserId,
	})
	
	// Get PDF from database
	pdf, err := h.repo.GetByID(ctx, req.PdfId)
	if err != nil {
		h.logger.Error("Failed to get PDF", err)
		return nil, status.Error(codes.NotFound, "PDF not found")
	}
	
	// Generate signed URL (valid for 1 hour)
	expiresAt := time.Now().Add(1 * time.Hour)
	url, err := h.storage.GetSignedURL(ctx, pdf.StoragePath, expiresAt)
	if err != nil {
		h.logger.Error("Failed to generate signed URL", err)
		return nil, status.Error(codes.Internal, "failed to generate download URL")
	}
	
	// Record download event
	err = h.repo.RecordDownload(ctx, req.PdfId, req.UserId)
	if err != nil {
		h.logger.Warn("Failed to record download", map[string]interface{}{
			"error": err.Error(),
		})
		// Don't fail the request if we can't record the download
	}
	
	h.logger.Info("Download URL generated", map[string]interface{}{
		"pdf_id":     req.PdfId,
		"user_id":    req.UserId,
		"expires_at": expiresAt.Unix(),
	})
	
	return &pb.DownloadURLResponse{
		Url:       url,
		ExpiresAt: expiresAt.Unix(),
	}, nil
}
