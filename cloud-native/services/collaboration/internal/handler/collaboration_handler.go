package handler

import (
	"context"
	"fmt"
	"io"
	"log"

	"github.com/google/uuid"
	"github.com/metlab/collaboration/internal/service"
	pb "metlab/proto-gen/go/collaboration"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

// CollaborationHandler implements the gRPC CollaborationService
type CollaborationHandler struct {
	pb.UnimplementedCollaborationServiceServer
	service *service.CollaborationService
}

// NewCollaborationHandler creates a new collaboration handler
func NewCollaborationHandler(svc *service.CollaborationService) *CollaborationHandler {
	return &CollaborationHandler{
		service: svc,
	}
}

// CreateStudyGroup creates a new study group
func (h *CollaborationHandler) CreateStudyGroup(ctx context.Context, req *pb.CreateStudyGroupRequest) (*pb.StudyGroup, error) {
	// Validate request
	if req.ClassId == "" {
		return nil, status.Error(codes.InvalidArgument, "class_id is required")
	}
	if req.StudentId == "" {
		return nil, status.Error(codes.InvalidArgument, "student_id is required")
	}
	if req.Name == "" {
		return nil, status.Error(codes.InvalidArgument, "name is required")
	}
	
	// Create study group
	group, err := h.service.CreateStudyGroup(ctx, req.ClassId, req.StudentId, req.Name, req.Description)
	if err != nil {
		log.Printf("Failed to create study group: %v", err)
		return nil, status.Error(codes.Internal, "failed to create study group")
	}
	
	// Get member count
	memberCount, err := h.service.GetStudyGroupMemberCount(ctx, group.ID)
	if err != nil {
		log.Printf("Failed to get member count: %v", err)
		memberCount = 1 // Creator is the first member
	}
	
	return &pb.StudyGroup{
		Id:          group.ID,
		Name:        group.Name,
		Description: group.Description,
		MemberCount: memberCount,
		MaxMembers:  group.MaxMembers,
		CreatedBy:   group.CreatedBy,
		CreatedAt:   group.CreatedAt.Unix(),
		IsMember:    true, // Creator is always a member
	}, nil
}

// JoinStudyGroup adds a student to a study group
func (h *CollaborationHandler) JoinStudyGroup(ctx context.Context, req *pb.JoinStudyGroupRequest) (*pb.JoinStudyGroupResponse, error) {
	// Validate request
	if req.StudyGroupId == "" {
		return nil, status.Error(codes.InvalidArgument, "study_group_id is required")
	}
	if req.StudentId == "" {
		return nil, status.Error(codes.InvalidArgument, "student_id is required")
	}
	if req.ClassId == "" {
		return nil, status.Error(codes.InvalidArgument, "class_id is required")
	}
	
	// Join study group with class verification
	err := h.service.JoinStudyGroup(ctx, req.StudyGroupId, req.StudentId, req.ClassId)
	if err != nil {
		log.Printf("Failed to join study group: %v", err)
		return &pb.JoinStudyGroupResponse{
			Success: false,
			Message: err.Error(),
		}, nil
	}
	
	return &pb.JoinStudyGroupResponse{
		Success: true,
		Message: "Successfully joined study group",
	}, nil
}

// ListStudyGroups retrieves all study groups for a class
func (h *CollaborationHandler) ListStudyGroups(ctx context.Context, req *pb.ListStudyGroupsRequest) (*pb.ListStudyGroupsResponse, error) {
	// Validate request
	if req.ClassId == "" {
		return nil, status.Error(codes.InvalidArgument, "class_id is required")
	}
	if req.StudentId == "" {
		return nil, status.Error(codes.InvalidArgument, "student_id is required")
	}
	
	// List study groups
	groups, studentGroupCount, err := h.service.ListStudyGroups(ctx, req.ClassId, req.StudentId)
	if err != nil {
		log.Printf("Failed to list study groups: %v", err)
		return nil, status.Error(codes.Internal, "failed to list study groups")
	}
	
	// Convert to proto
	pbGroups := make([]*pb.StudyGroup, 0, len(groups))
	for _, group := range groups {
		// Get member count
		memberCount, err := h.service.GetStudyGroupMemberCount(ctx, group.ID)
		if err != nil {
			log.Printf("Failed to get member count for group %s: %v", group.ID, err)
			memberCount = 0
		}
		
		// Check if student is a member
		isMember, err := h.service.IsStudyGroupMember(ctx, group.ID, req.StudentId)
		if err != nil {
			log.Printf("Failed to check membership for group %s: %v", group.ID, err)
			isMember = false
		}
		
		pbGroups = append(pbGroups, &pb.StudyGroup{
			Id:          group.ID,
			Name:        group.Name,
			Description: group.Description,
			MemberCount: memberCount,
			MaxMembers:  group.MaxMembers,
			CreatedBy:   group.CreatedBy,
			CreatedAt:   group.CreatedAt.Unix(),
			IsMember:    isMember,
		})
	}
	
	return &pb.ListStudyGroupsResponse{
		StudyGroups:       pbGroups,
		StudentGroupCount: studentGroupCount,
	}, nil
}

// CreateChatRoom creates a new chat room
func (h *CollaborationHandler) CreateChatRoom(ctx context.Context, req *pb.CreateChatRoomRequest) (*pb.ChatRoom, error) {
	// Validate request
	if req.ClassId == "" {
		return nil, status.Error(codes.InvalidArgument, "class_id is required")
	}
	if req.StudentId == "" {
		return nil, status.Error(codes.InvalidArgument, "student_id is required")
	}
	if req.Name == "" {
		return nil, status.Error(codes.InvalidArgument, "name is required")
	}
	
	// Create chat room
	room, err := h.service.CreateChatRoom(ctx, req.ClassId, req.StudentId, req.Name, req.Topic)
	if err != nil {
		log.Printf("Failed to create chat room: %v", err)
		return nil, status.Error(codes.Internal, "failed to create chat room")
	}
	
	return &pb.ChatRoom{
		Id:        room.ID,
		Name:      room.Name,
		Topic:     room.Topic,
		CreatedBy: room.CreatedBy,
		CreatedAt: room.CreatedAt.Unix(),
	}, nil
}

// SendMessage sends a message to a chat room
func (h *CollaborationHandler) SendMessage(ctx context.Context, req *pb.SendMessageRequest) (*pb.SendMessageResponse, error) {
	// Validate request
	if req.ChatRoomId == "" {
		return nil, status.Error(codes.InvalidArgument, "chat_room_id is required")
	}
	if req.SenderId == "" {
		return nil, status.Error(codes.InvalidArgument, "sender_id is required")
	}
	if req.MessageText == "" && len(req.ImageData) == 0 {
		return nil, status.Error(codes.InvalidArgument, "message must contain text or image")
	}
	
	// TODO: Handle image upload to S3 if image_data is provided
	var imagePath *string
	if len(req.ImageData) > 0 {
		// For now, we'll just generate a placeholder path
		// In a full implementation, this would upload to S3
		path := fmt.Sprintf("chat-images/%s/%s", req.ChatRoomId, uuid.New().String())
		imagePath = &path
		log.Printf("Image upload not yet implemented, using placeholder path: %s", path)
	}
	
	// Send message
	message, err := h.service.SendMessage(ctx, req.ChatRoomId, req.SenderId, "Student", req.MessageText, imagePath)
	if err != nil {
		log.Printf("Failed to send message: %v", err)
		return nil, status.Error(codes.Internal, "failed to send message")
	}
	
	return &pb.SendMessageResponse{
		MessageId: message.ID,
		SentAt:    message.SentAt.Unix(),
	}, nil
}

// GetMessages retrieves messages for a chat room
func (h *CollaborationHandler) GetMessages(ctx context.Context, req *pb.GetMessagesRequest) (*pb.GetMessagesResponse, error) {
	// Validate request
	if req.ChatRoomId == "" {
		return nil, status.Error(codes.InvalidArgument, "chat_room_id is required")
	}
	
	limit := req.Limit
	if limit == 0 {
		limit = 50
	}
	
	// Get messages
	messages, err := h.service.GetMessages(ctx, req.ChatRoomId, limit, req.BeforeTimestamp)
	if err != nil {
		log.Printf("Failed to get messages: %v", err)
		return nil, status.Error(codes.Internal, "failed to get messages")
	}
	
	// Convert to proto
	pbMessages := make([]*pb.ChatMessage, 0, len(messages))
	for _, msg := range messages {
		imageURL := ""
		if msg.ImagePath != nil {
			imageURL = *msg.ImagePath
		}
		
		pbMessages = append(pbMessages, &pb.ChatMessage{
			Id:          msg.ID,
			SenderId:    msg.SenderID,
			SenderName:  msg.SenderName,
			MessageText: msg.MessageText,
			ImageUrl:    imageURL,
			SentAt:      msg.SentAt.Unix(),
		})
	}
	
	return &pb.GetMessagesResponse{
		Messages: pbMessages,
	}, nil
}

// StreamMessages streams real-time messages for a chat room
func (h *CollaborationHandler) StreamMessages(req *pb.StreamMessagesRequest, stream pb.CollaborationService_StreamMessagesServer) error {
	// Validate request
	if req.ChatRoomId == "" {
		return status.Error(codes.InvalidArgument, "chat_room_id is required")
	}
	
	ctx := stream.Context()
	
	// Subscribe to room
	messageChan, err := h.service.SubscribeToRoom(ctx, req.ChatRoomId)
	if err != nil {
		log.Printf("Failed to subscribe to room: %v", err)
		return status.Error(codes.Internal, "failed to subscribe to room")
	}
	
	// Stream messages
	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		case msg, ok := <-messageChan:
			if !ok {
				return io.EOF
			}
			
			imageURL := ""
			if msg.ImagePath != nil {
				imageURL = *msg.ImagePath
			}
			
			pbMsg := &pb.ChatMessage{
				Id:          msg.ID,
				SenderId:    msg.SenderID,
				SenderName:  msg.SenderName,
				MessageText: msg.MessageText,
				ImageUrl:    imageURL,
				SentAt:      msg.SentAt.Unix(),
			}
			
			if err := stream.Send(pbMsg); err != nil {
				log.Printf("Failed to send message to stream: %v", err)
				return err
			}
		}
	}
}
