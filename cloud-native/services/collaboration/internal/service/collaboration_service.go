package service

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"log"
	"path/filepath"
	"strings"

	"github.com/google/uuid"
	"github.com/metlab/collaboration/internal/config"
	"github.com/metlab/collaboration/internal/models"
	"github.com/metlab/collaboration/internal/repository"
	"github.com/metlab/shared/storage"
	"github.com/redis/go-redis/v9"
)

// CollaborationService handles business logic for collaboration features
type CollaborationService struct {
	config         *config.Config
	studyGroupRepo *repository.StudyGroupRepository
	chatRepo       *repository.ChatRepository
	redisClient    *redis.Client
	storageClient  *storage.Client
}

// NewCollaborationService creates a new collaboration service
func NewCollaborationService(
	cfg *config.Config,
	studyGroupRepo *repository.StudyGroupRepository,
	chatRepo *repository.ChatRepository,
	redisClient *redis.Client,
	storageClient *storage.Client,
) *CollaborationService {
	return &CollaborationService{
		config:         cfg,
		studyGroupRepo: studyGroupRepo,
		chatRepo:       chatRepo,
		redisClient:    redisClient,
		storageClient:  storageClient,
	}
}

// CreateStudyGroup creates a new study group
func (s *CollaborationService) CreateStudyGroup(ctx context.Context, classID, studentID, name, description string) (*models.StudyGroup, error) {
	// Validate input
	if name == "" {
		return nil, fmt.Errorf("study group name is required")
	}

	// Check if student has reached the maximum number of groups
	studentGroupCount, err := s.studyGroupRepo.GetStudentGroupCount(ctx, studentID)
	if err != nil {
		return nil, fmt.Errorf("failed to check student group count: %w", err)
	}

	if studentGroupCount >= int32(s.config.MaxGroupsPerStudent) {
		return nil, fmt.Errorf("student has reached maximum number of groups (%d)", s.config.MaxGroupsPerStudent)
	}

	// Create study group
	group := &models.StudyGroup{
		ID:          uuid.New().String(),
		ClassID:     classID,
		Name:        name,
		Description: description,
		CreatedBy:   studentID,
		MaxMembers:  int32(s.config.MaxGroupMembers),
	}

	if err := s.studyGroupRepo.Create(ctx, group); err != nil {
		return nil, fmt.Errorf("failed to create study group: %w", err)
	}

	// Add creator as first member
	member := &models.StudyGroupMember{
		StudyGroupID: group.ID,
		StudentID:    studentID,
	}

	if err := s.studyGroupRepo.AddMember(ctx, member); err != nil {
		return nil, fmt.Errorf("failed to add creator as member: %w", err)
	}

	return group, nil
}

// JoinStudyGroup adds a student to a study group
func (s *CollaborationService) JoinStudyGroup(ctx context.Context, groupID, studentID, studentClassID string) error {
	// Check if group exists
	group, err := s.studyGroupRepo.GetByID(ctx, groupID)
	if err != nil {
		return fmt.Errorf("failed to get study group: %w", err)
	}

	// Verify student is in the same class as the study group
	if group.ClassID != studentClassID {
		return fmt.Errorf("student is not in the same class as the study group")
	}

	// Check if student is already a member
	isMember, err := s.studyGroupRepo.IsMember(ctx, groupID, studentID)
	if err != nil {
		return fmt.Errorf("failed to check membership: %w", err)
	}
	if isMember {
		return fmt.Errorf("student is already a member of this group")
	}

	// Check if student has reached the maximum number of groups (5 max)
	studentGroupCount, err := s.studyGroupRepo.GetStudentGroupCount(ctx, studentID)
	if err != nil {
		return fmt.Errorf("failed to check student group count: %w", err)
	}

	if studentGroupCount >= int32(s.config.MaxGroupsPerStudent) {
		return fmt.Errorf("student has reached maximum number of groups (%d)", s.config.MaxGroupsPerStudent)
	}

	// Check if group has reached maximum members (10 max)
	memberCount, err := s.studyGroupRepo.GetMemberCount(ctx, groupID)
	if err != nil {
		return fmt.Errorf("failed to get member count: %w", err)
	}

	if memberCount >= group.MaxMembers {
		return fmt.Errorf("study group has reached maximum members (%d)", group.MaxMembers)
	}

	// Add student to group members
	member := &models.StudyGroupMember{
		StudyGroupID: groupID,
		StudentID:    studentID,
	}

	if err := s.studyGroupRepo.AddMember(ctx, member); err != nil {
		return fmt.Errorf("failed to add member: %w", err)
	}

	return nil
}

// ListStudyGroups retrieves all study groups for a class with membership info
func (s *CollaborationService) ListStudyGroups(ctx context.Context, classID, studentID string) ([]*models.StudyGroup, int32, error) {
	groups, err := s.studyGroupRepo.ListByClass(ctx, classID)
	if err != nil {
		return nil, 0, fmt.Errorf("failed to list study groups: %w", err)
	}

	// Get student's group count
	studentGroupCount, err := s.studyGroupRepo.GetStudentGroupCount(ctx, studentID)
	if err != nil {
		return nil, 0, fmt.Errorf("failed to get student group count: %w", err)
	}

	return groups, studentGroupCount, nil
}

// GetStudyGroupMemberCount returns the number of members in a study group
func (s *CollaborationService) GetStudyGroupMemberCount(ctx context.Context, groupID string) (int32, error) {
	return s.studyGroupRepo.GetMemberCount(ctx, groupID)
}

// IsStudyGroupMember checks if a student is a member of a study group
func (s *CollaborationService) IsStudyGroupMember(ctx context.Context, groupID, studentID string) (bool, error) {
	return s.studyGroupRepo.IsMember(ctx, groupID, studentID)
}

// CreateChatRoom creates a new chat room
func (s *CollaborationService) CreateChatRoom(ctx context.Context, classID, studentID, name, topic string) (*models.ChatRoom, error) {
	// Validate input
	if name == "" {
		return nil, fmt.Errorf("chat room name is required")
	}

	// Create chat room
	room := &models.ChatRoom{
		ID:        uuid.New().String(),
		ClassID:   classID,
		Name:      name,
		Topic:     topic,
		CreatedBy: studentID,
	}

	if err := s.chatRepo.CreateRoom(ctx, room); err != nil {
		return nil, fmt.Errorf("failed to create chat room: %w", err)
	}

	return room, nil
}

// SendMessage sends a message to a chat room
func (s *CollaborationService) SendMessage(ctx context.Context, roomID, senderID, senderName, messageText string, imageData []byte, imageFilename string) (*models.ChatMessage, error) {
	// Validate input
	if messageText == "" && len(imageData) == 0 {
		return nil, fmt.Errorf("message must contain text or image")
	}

	// Validate message text length
	if len(messageText) > s.config.MaxMessageLength {
		return nil, fmt.Errorf("message text exceeds maximum length of %d characters", s.config.MaxMessageLength)
	}

	// Validate image size
	if len(imageData) > 0 && int64(len(imageData)) > s.config.MaxImageSize {
		return nil, fmt.Errorf("image size exceeds maximum of %d bytes (5MB)", s.config.MaxImageSize)
	}

	// Verify chat room exists
	_, err := s.chatRepo.GetRoomByID(ctx, roomID)
	if err != nil {
		return nil, fmt.Errorf("chat room not found: %w", err)
	}

	// Upload image to S3 if provided
	var imagePath *string
	if len(imageData) > 0 {
		// Generate unique filename
		ext := filepath.Ext(imageFilename)
		if ext == "" {
			ext = ".jpg" // Default extension
		}
		
		// Validate file extension
		validExtensions := []string{".jpg", ".jpeg", ".png", ".gif", ".webp"}
		isValid := false
		extLower := strings.ToLower(ext)
		for _, validExt := range validExtensions {
			if extLower == validExt {
				isValid = true
				break
			}
		}
		if !isValid {
			return nil, fmt.Errorf("invalid image format, supported formats: jpg, jpeg, png, gif, webp")
		}
		
		key := fmt.Sprintf("chat-images/%s/%s%s", roomID, uuid.New().String(), ext)
		
		// Determine content type
		contentType := "image/jpeg"
		switch extLower {
		case ".png":
			contentType = "image/png"
		case ".gif":
			contentType = "image/gif"
		case ".webp":
			contentType = "image/webp"
		}
		
		// Upload to S3
		_, err := s.storageClient.Upload(ctx, s.config.S3Bucket, key, bytes.NewReader(imageData), &storage.UploadOptions{
			ContentType: contentType,
			ACL:         "public-read",
		})
		if err != nil {
			log.Printf("Failed to upload image to S3: %v", err)
			return nil, fmt.Errorf("failed to upload image: %w", err)
		}
		
		imagePath = &key
		log.Printf("Successfully uploaded image to S3: %s", key)
	}

	// Create message
	message := &models.ChatMessage{
		ID:          uuid.New().String(),
		ChatRoomID:  roomID,
		SenderID:    senderID,
		SenderName:  senderName,
		MessageText: messageText,
		ImagePath:   imagePath,
	}

	if err := s.chatRepo.CreateMessage(ctx, message); err != nil {
		return nil, fmt.Errorf("failed to create message: %w", err)
	}

	// Publish message to Redis pub/sub for real-time delivery
	if err := s.publishMessage(ctx, message); err != nil {
		log.Printf("Failed to publish message to Redis: %v", err)
		// Don't fail the request if pub/sub fails, message is already stored
	}

	return message, nil
}

// GetMessages retrieves messages for a chat room
func (s *CollaborationService) GetMessages(ctx context.Context, roomID string, limit int32, beforeTimestamp int64) ([]*models.ChatMessage, error) {
	if limit <= 0 {
		limit = 50 // Default limit
	}
	if limit > 100 {
		limit = 100 // Maximum limit
	}

	return s.chatRepo.GetMessages(ctx, roomID, limit, beforeTimestamp)
}

// SubscribeToRoom subscribes to real-time messages for a chat room
func (s *CollaborationService) SubscribeToRoom(ctx context.Context, roomID string) (<-chan *models.ChatMessage, error) {
	// Verify chat room exists
	_, err := s.chatRepo.GetRoomByID(ctx, roomID)
	if err != nil {
		return nil, fmt.Errorf("chat room not found: %w", err)
	}

	// Subscribe to Redis channel
	channel := fmt.Sprintf("chat:room:%s", roomID)
	pubsub := s.redisClient.Subscribe(ctx, channel)

	// Create message channel
	messageChan := make(chan *models.ChatMessage, 10)

	// Start goroutine to receive messages
	go func() {
		defer close(messageChan)
		defer pubsub.Close()

		ch := pubsub.Channel()
		for {
			select {
			case <-ctx.Done():
				return
			case msg, ok := <-ch:
				if !ok {
					return
				}

				var chatMessage models.ChatMessage
				if err := json.Unmarshal([]byte(msg.Payload), &chatMessage); err != nil {
					log.Printf("Failed to unmarshal message: %v", err)
					continue
				}

				select {
				case messageChan <- &chatMessage:
				case <-ctx.Done():
					return
				}
			}
		}
	}()

	return messageChan, nil
}

// publishMessage publishes a message to Redis pub/sub
func (s *CollaborationService) publishMessage(ctx context.Context, message *models.ChatMessage) error {
	channel := fmt.Sprintf("chat:room:%s", message.ChatRoomID)

	data, err := json.Marshal(message)
	if err != nil {
		return fmt.Errorf("failed to marshal message: %w", err)
	}

	return s.redisClient.Publish(ctx, channel, data).Err()
}

// CleanupOldMessages deletes messages older than the retention period
func (s *CollaborationService) CleanupOldMessages(ctx context.Context) (int64, error) {
	return s.chatRepo.DeleteOldMessages(ctx, s.config.MessageRetentionDays)
}

// ListChatRooms retrieves all chat rooms for a class
func (s *CollaborationService) ListChatRooms(ctx context.Context, classID string) ([]*models.ChatRoom, error) {
	return s.chatRepo.ListRoomsByClass(ctx, classID)
}
