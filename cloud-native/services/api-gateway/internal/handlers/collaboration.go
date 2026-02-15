package handlers

import (
	"context"
	"net/http"
	"strconv"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/metlab/api-gateway/internal/transformers"
	collaborationpb "github.com/metlab/shared/proto-gen/go/collaboration"
)

// CreateStudyGroupRequest represents the HTTP request for creating a study group
type CreateStudyGroupRequest struct {
	ClassID     string `json:"class_id"`
	Name        string `json:"name"`
	Description string `json:"description"`
}

// StudyGroupResponse represents a study group in HTTP responses
type StudyGroupResponse struct {
	ID          string `json:"id"`
	Name        string `json:"name"`
	Description string `json:"description"`
	MemberCount int32  `json:"member_count"`
	MaxMembers  int32  `json:"max_members"`
	CreatedBy   string `json:"created_by"`
	CreatedAt   int64  `json:"created_at"`
	IsMember    bool   `json:"is_member"`
}

// ListStudyGroupsResponse represents the HTTP response for listing study groups
type ListStudyGroupsResponse struct {
	StudyGroups       []StudyGroupResponse `json:"study_groups"`
	StudentGroupCount int32                `json:"student_group_count"`
}

// JoinStudyGroupResponse represents the HTTP response for joining a study group
type JoinStudyGroupResponse struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
}

// CreateChatRoomRequest represents the HTTP request for creating a chat room
type CreateChatRoomRequest struct {
	ClassID string `json:"class_id"`
	Name    string `json:"name"`
	Topic   string `json:"topic"`
}

// ChatRoomResponse represents a chat room in HTTP responses
type ChatRoomResponse struct {
	ID        string `json:"id"`
	Name      string `json:"name"`
	Topic     string `json:"topic"`
	CreatedBy string `json:"created_by"`
	CreatedAt int64  `json:"created_at"`
}

// SendMessageRequest represents the HTTP request for sending a message
type SendMessageRequest struct {
	MessageText   string `json:"message_text"`
	ImageFilename string `json:"image_filename,omitempty"`
}

// SendMessageResponse represents the HTTP response for sending a message
type SendMessageResponse struct {
	MessageID string `json:"message_id"`
	SentAt    int64  `json:"sent_at"`
}

// ChatMessageResponse represents a chat message in HTTP responses
type ChatMessageResponse struct {
	ID          string `json:"id"`
	SenderID    string `json:"sender_id"`
	SenderName  string `json:"sender_name"`
	MessageText string `json:"message_text"`
	ImageURL    string `json:"image_url,omitempty"`
	SentAt      int64  `json:"sent_at"`
}

// GetMessagesResponse represents the HTTP response for getting messages
type GetMessagesResponse struct {
	Messages []ChatMessageResponse `json:"messages"`
}

// CreateStudyGroup handles POST /api/study-groups
func (h *Handler) CreateStudyGroup(w http.ResponseWriter, r *http.Request) {
	// Get user ID from context
	userID, ok := r.Context().Value("user_id").(string)
	if !ok || userID == "" {
		transformers.WriteError(w, http.StatusUnauthorized, "UNAUTHORIZED", "User ID not found in context")
		return
	}

	// Decode request
	var req CreateStudyGroupRequest
	if err := transformers.DecodeJSONRequest(r, &req); err != nil {
		transformers.WriteError(w, http.StatusBadRequest, "INVALID_REQUEST", "Invalid request body")
		return
	}

	// Validate required fields
	if req.ClassID == "" || req.Name == "" {
		transformers.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "class_id and name are required")
		return
	}

	// Call gRPC service
	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()

	grpcReq := &collaborationpb.CreateStudyGroupRequest{
		ClassId:     req.ClassID,
		StudentId:   userID,
		Name:        req.Name,
		Description: req.Description,
	}

	resp, err := h.clients.Collaboration.CreateStudyGroup(ctx, grpcReq)
	if err != nil {
		transformers.HandleGRPCError(w, err)
		return
	}

	// Transform response
	httpResp := StudyGroupResponse{
		ID:          resp.Id,
		Name:        resp.Name,
		Description: resp.Description,
		MemberCount: resp.MemberCount,
		MaxMembers:  resp.MaxMembers,
		CreatedBy:   resp.CreatedBy,
		CreatedAt:   resp.CreatedAt,
		IsMember:    resp.IsMember,
	}

	transformers.EncodeJSONResponse(w, http.StatusCreated, httpResp)
}

// ListStudyGroups handles GET /api/study-groups
func (h *Handler) ListStudyGroups(w http.ResponseWriter, r *http.Request) {
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

	grpcReq := &collaborationpb.ListStudyGroupsRequest{
		ClassId:   classID,
		StudentId: userID,
	}

	resp, err := h.clients.Collaboration.ListStudyGroups(ctx, grpcReq)
	if err != nil {
		transformers.HandleGRPCError(w, err)
		return
	}

	// Transform response
	studyGroups := make([]StudyGroupResponse, len(resp.StudyGroups))
	for i, sg := range resp.StudyGroups {
		studyGroups[i] = StudyGroupResponse{
			ID:          sg.Id,
			Name:        sg.Name,
			Description: sg.Description,
			MemberCount: sg.MemberCount,
			MaxMembers:  sg.MaxMembers,
			CreatedBy:   sg.CreatedBy,
			CreatedAt:   sg.CreatedAt,
			IsMember:    sg.IsMember,
		}
	}

	httpResp := ListStudyGroupsResponse{
		StudyGroups:       studyGroups,
		StudentGroupCount: resp.StudentGroupCount,
	}

	transformers.EncodeJSONResponse(w, http.StatusOK, httpResp)
}

// JoinStudyGroup handles POST /api/study-groups/:id/join
func (h *Handler) JoinStudyGroup(w http.ResponseWriter, r *http.Request) {
	// Get user ID from context
	userID, ok := r.Context().Value("user_id").(string)
	if !ok || userID == "" {
		transformers.WriteError(w, http.StatusUnauthorized, "UNAUTHORIZED", "User ID not found in context")
		return
	}

	// Get study group ID from URL
	studyGroupID := chi.URLParam(r, "id")
	if studyGroupID == "" {
		transformers.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "study group ID is required")
		return
	}

	// Call gRPC service
	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()

	grpcReq := &collaborationpb.JoinStudyGroupRequest{
		StudyGroupId: studyGroupID,
		StudentId:    userID,
	}

	resp, err := h.clients.Collaboration.JoinStudyGroup(ctx, grpcReq)
	if err != nil {
		transformers.HandleGRPCError(w, err)
		return
	}

	// Transform and return response
	httpResp := JoinStudyGroupResponse{
		Success: resp.Success,
		Message: resp.Message,
	}

	transformers.EncodeJSONResponse(w, http.StatusOK, httpResp)
}

// CreateChatRoom handles POST /api/chat/rooms
func (h *Handler) CreateChatRoom(w http.ResponseWriter, r *http.Request) {
	// Get user ID from context
	userID, ok := r.Context().Value("user_id").(string)
	if !ok || userID == "" {
		transformers.WriteError(w, http.StatusUnauthorized, "UNAUTHORIZED", "User ID not found in context")
		return
	}

	// Decode request
	var req CreateChatRoomRequest
	if err := transformers.DecodeJSONRequest(r, &req); err != nil {
		transformers.WriteError(w, http.StatusBadRequest, "INVALID_REQUEST", "Invalid request body")
		return
	}

	// Validate required fields
	if req.ClassID == "" || req.Name == "" {
		transformers.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "class_id and name are required")
		return
	}

	// Call gRPC service
	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()

	grpcReq := &collaborationpb.CreateChatRoomRequest{
		ClassId:   req.ClassID,
		StudentId: userID,
		Name:      req.Name,
		Topic:     req.Topic,
	}

	resp, err := h.clients.Collaboration.CreateChatRoom(ctx, grpcReq)
	if err != nil {
		transformers.HandleGRPCError(w, err)
		return
	}

	// Transform response
	httpResp := ChatRoomResponse{
		ID:        resp.Id,
		Name:      resp.Name,
		Topic:     resp.Topic,
		CreatedBy: resp.CreatedBy,
		CreatedAt: resp.CreatedAt,
	}

	transformers.EncodeJSONResponse(w, http.StatusCreated, httpResp)
}

// SendMessage handles POST /api/chat/rooms/:id/messages
func (h *Handler) SendMessage(w http.ResponseWriter, r *http.Request) {
	// Get user ID from context
	userID, ok := r.Context().Value("user_id").(string)
	if !ok || userID == "" {
		transformers.WriteError(w, http.StatusUnauthorized, "UNAUTHORIZED", "User ID not found in context")
		return
	}

	// Get chat room ID from URL
	chatRoomID := chi.URLParam(r, "id")
	if chatRoomID == "" {
		transformers.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "chat room ID is required")
		return
	}

	// Check content type
	contentType := r.Header.Get("Content-Type")
	var messageText string
	var imageData []byte
	var imageFilename string

	if contentType == "application/json" {
		// JSON request (text message only)
		var req SendMessageRequest
		if err := transformers.DecodeJSONRequest(r, &req); err != nil {
			transformers.WriteError(w, http.StatusBadRequest, "INVALID_REQUEST", "Invalid request body")
			return
		}
		messageText = req.MessageText
	} else {
		// Multipart form (text + optional image)
		err := r.ParseMultipartForm(5 << 20) // 5MB max
		if err != nil {
			transformers.WriteError(w, http.StatusBadRequest, "INVALID_REQUEST", "Failed to parse multipart form")
			return
		}

		messageText = r.FormValue("message_text")

		// Get optional image file
		if file, header, err := r.FormFile("image"); err == nil {
			defer file.Close()
			imageFilename = header.Filename

			// Read image data
			buffer := make([]byte, header.Size)
			if _, err := file.Read(buffer); err != nil {
				transformers.WriteError(w, http.StatusInternalServerError, "UPLOAD_ERROR", "Failed to read image")
				return
			}
			imageData = buffer
		}
	}

	// Validate message text
	if messageText == "" && len(imageData) == 0 {
		transformers.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "message_text or image is required")
		return
	}

	if len(messageText) > 1000 {
		transformers.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "message_text must be 1000 characters or less")
		return
	}

	// Call gRPC service
	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()

	grpcReq := &collaborationpb.SendMessageRequest{
		ChatRoomId:    chatRoomID,
		SenderId:      userID,
		MessageText:   messageText,
		ImageData:     imageData,
		ImageFilename: imageFilename,
	}

	resp, err := h.clients.Collaboration.SendMessage(ctx, grpcReq)
	if err != nil {
		transformers.HandleGRPCError(w, err)
		return
	}

	// Transform and return response
	httpResp := SendMessageResponse{
		MessageID: resp.MessageId,
		SentAt:    resp.SentAt,
	}

	transformers.EncodeJSONResponse(w, http.StatusCreated, httpResp)
}

// GetMessages handles GET /api/chat/rooms/:id/messages
func (h *Handler) GetMessages(w http.ResponseWriter, r *http.Request) {
	// Get user ID from context
	userID, ok := r.Context().Value("user_id").(string)
	if !ok || userID == "" {
		transformers.WriteError(w, http.StatusUnauthorized, "UNAUTHORIZED", "User ID not found in context")
		return
	}

	// Get chat room ID from URL
	chatRoomID := chi.URLParam(r, "id")
	if chatRoomID == "" {
		transformers.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "chat room ID is required")
		return
	}

	// Get query parameters
	limit := int32(50) // Default limit
	if limitStr := r.URL.Query().Get("limit"); limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil && l > 0 && l <= 200 {
			limit = int32(l)
		}
	}

	beforeTimestamp := int64(0)
	if beforeStr := r.URL.Query().Get("before"); beforeStr != "" {
		if bt, err := strconv.ParseInt(beforeStr, 10, 64); err == nil {
			beforeTimestamp = bt
		}
	}

	// Call gRPC service
	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()

	grpcReq := &collaborationpb.GetMessagesRequest{
		ChatRoomId:      chatRoomID,
		UserId:          userID,
		Limit:           limit,
		BeforeTimestamp: beforeTimestamp,
	}

	resp, err := h.clients.Collaboration.GetMessages(ctx, grpcReq)
	if err != nil {
		transformers.HandleGRPCError(w, err)
		return
	}

	// Transform response
	messages := make([]ChatMessageResponse, len(resp.Messages))
	for i, m := range resp.Messages {
		messages[i] = ChatMessageResponse{
			ID:          m.Id,
			SenderID:    m.SenderId,
			SenderName:  m.SenderName,
			MessageText: m.MessageText,
			ImageURL:    m.ImageUrl,
			SentAt:      m.SentAt,
		}
	}

	httpResp := GetMessagesResponse{
		Messages: messages,
	}

	transformers.EncodeJSONResponse(w, http.StatusOK, httpResp)
}
