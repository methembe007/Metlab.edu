package handlers

import (
	"context"
	"io"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/metlab/api-gateway/internal/transformers"
	pdfpb "github.com/metlab/shared/proto-gen/go/pdf"
)

// UploadPDFRequest represents the HTTP request for PDF upload
type UploadPDFRequest struct {
	TeacherID   string `json:"teacher_id"`
	ClassID     string `json:"class_id"`
	Title       string `json:"title"`
	Description string `json:"description"`
	Filename    string `json:"filename"`
	FileSize    int64  `json:"file_size"`
}

// PDFResponse represents a PDF in HTTP responses
type PDFResponse struct {
	ID              string `json:"id"`
	Title           string `json:"title"`
	Description     string `json:"description"`
	FileSizeBytes   int64  `json:"file_size_bytes"`
	CreatedAt       int64  `json:"created_at"`
	Filename        string `json:"filename"`
	DownloadedByUser bool  `json:"downloaded_by_user"`
}

// UploadPDFResponse represents the HTTP response for PDF upload
type UploadPDFResponse struct {
	PDFID  string `json:"pdf_id"`
	Status string `json:"status"`
}

// ListPDFsResponse represents the HTTP response for listing PDFs
type ListPDFsResponse struct {
	PDFs []PDFResponse `json:"pdfs"`
}

// DownloadURLResponse represents the HTTP response for PDF download URL
type DownloadURLResponse struct {
	URL       string `json:"url"`
	ExpiresAt int64  `json:"expires_at"`
}

// UploadPDF handles POST /api/pdfs
func (h *Handler) UploadPDF(w http.ResponseWriter, r *http.Request) {
	// Get user ID from context
	userID, ok := r.Context().Value("user_id").(string)
	if !ok || userID == "" {
		transformers.WriteError(w, http.StatusUnauthorized, "UNAUTHORIZED", "User ID not found in context")
		return
	}

	// Parse multipart form
	err := r.ParseMultipartForm(50 << 20) // 50MB max
	if err != nil {
		transformers.WriteError(w, http.StatusBadRequest, "INVALID_REQUEST", "Failed to parse multipart form")
		return
	}

	// Get form fields
	teacherID := r.FormValue("teacher_id")
	classID := r.FormValue("class_id")
	title := r.FormValue("title")
	description := r.FormValue("description")

	// Validate required fields
	if teacherID == "" || classID == "" || title == "" {
		transformers.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "teacher_id, class_id, and title are required")
		return
	}

	// Get file from form
	file, header, err := r.FormFile("pdf")
	if err != nil {
		transformers.WriteError(w, http.StatusBadRequest, "INVALID_REQUEST", "pdf file is required")
		return
	}
	defer file.Close()

	// Call gRPC streaming service
	ctx, cancel := context.WithTimeout(r.Context(), 15*time.Minute) // Long timeout for large uploads
	defer cancel()

	stream, err := h.clients.PDF.UploadPDF(ctx)
	if err != nil {
		transformers.HandleGRPCError(w, err)
		return
	}

	// Send metadata first
	metadataReq := &pdfpb.UploadPDFRequest{
		Data: &pdfpb.UploadPDFRequest_Metadata{
			Metadata: &pdfpb.PDFMetadata{
				TeacherId:   teacherID,
				ClassId:     classID,
				Title:       title,
				Description: description,
				Filename:    header.Filename,
				FileSize:    header.Size,
			},
		},
	}

	if err := stream.Send(metadataReq); err != nil {
		transformers.HandleGRPCError(w, err)
		return
	}

	// Stream file chunks
	buffer := make([]byte, 1024*1024) // 1MB chunks
	for {
		n, err := file.Read(buffer)
		if err == io.EOF {
			break
		}
		if err != nil {
			transformers.WriteError(w, http.StatusInternalServerError, "UPLOAD_ERROR", "Failed to read file")
			return
		}

		chunkReq := &pdfpb.UploadPDFRequest{
			Data: &pdfpb.UploadPDFRequest_Chunk{
				Chunk: buffer[:n],
			},
		}

		if err := stream.Send(chunkReq); err != nil {
			transformers.HandleGRPCError(w, err)
			return
		}
	}

	// Close stream and get response
	resp, err := stream.CloseAndRecv()
	if err != nil {
		transformers.HandleGRPCError(w, err)
		return
	}

	// Transform and return response
	httpResp := UploadPDFResponse{
		PDFID:  resp.PdfId,
		Status: resp.Status,
	}

	transformers.EncodeJSONResponse(w, http.StatusCreated, httpResp)
}

// ListPDFs handles GET /api/pdfs
func (h *Handler) ListPDFs(w http.ResponseWriter, r *http.Request) {
	// Get user ID from context
	userID, ok := r.Context().Value("user_id").(string)
	if !ok || userID == "" {
		transformers.WriteError(w, http.StatusUnauthorized, "UNAUTHORIZED", "User ID not found in context")
		return
	}

	// Get query parameters
	classID := r.URL.Query().Get("class_id")
	if classID == "" {
		transformers.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "class_id is required")
		return
	}

	// Call gRPC service
	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()

	grpcReq := &pdfpb.ListPDFsRequest{
		ClassId: classID,
		UserId:  userID,
	}

	resp, err := h.clients.PDF.ListPDFs(ctx, grpcReq)
	if err != nil {
		transformers.HandleGRPCError(w, err)
		return
	}

	// Transform response
	pdfs := make([]PDFResponse, len(resp.Pdfs))
	for i, p := range resp.Pdfs {
		pdfs[i] = PDFResponse{
			ID:              p.Id,
			Title:           p.Title,
			Description:     p.Description,
			FileSizeBytes:   p.FileSizeBytes,
			CreatedAt:       p.CreatedAt,
			Filename:        p.Filename,
			DownloadedByUser: p.DownloadedByUser,
		}
	}

	httpResp := ListPDFsResponse{
		PDFs: pdfs,
	}

	transformers.EncodeJSONResponse(w, http.StatusOK, httpResp)
}

// GetPDFDownloadURL handles GET /api/pdfs/:id/download
func (h *Handler) GetPDFDownloadURL(w http.ResponseWriter, r *http.Request) {
	// Get user ID from context
	userID, ok := r.Context().Value("user_id").(string)
	if !ok || userID == "" {
		transformers.WriteError(w, http.StatusUnauthorized, "UNAUTHORIZED", "User ID not found in context")
		return
	}

	// Get PDF ID from URL
	pdfID := chi.URLParam(r, "id")
	if pdfID == "" {
		transformers.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "pdf ID is required")
		return
	}

	// Call gRPC service
	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()

	grpcReq := &pdfpb.GetDownloadURLRequest{
		PdfId:  pdfID,
		UserId: userID,
	}

	resp, err := h.clients.PDF.GetDownloadURL(ctx, grpcReq)
	if err != nil {
		transformers.HandleGRPCError(w, err)
		return
	}

	// Transform and return response
	httpResp := DownloadURLResponse{
		URL:       resp.Url,
		ExpiresAt: resp.ExpiresAt,
	}

	transformers.EncodeJSONResponse(w, http.StatusOK, httpResp)
}
