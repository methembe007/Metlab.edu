package repository

import (
	"context"
	"fmt"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/metlab/collaboration/internal/models"
)

// ChatRepository handles database operations for chat rooms and messages
type ChatRepository struct {
	pool *pgxpool.Pool
}

// NewChatRepository creates a new chat repository
func NewChatRepository(pool *pgxpool.Pool) *ChatRepository {
	return &ChatRepository{pool: pool}
}

// CreateRoom creates a new chat room
func (r *ChatRepository) CreateRoom(ctx context.Context, room *models.ChatRoom) error {
	query := `
		INSERT INTO chat_rooms (id, class_id, name, topic, created_by)
		VALUES ($1, $2, $3, $4, $5)
		RETURNING created_at
	`
	
	err := r.pool.QueryRow(
		ctx,
		query,
		room.ID,
		room.ClassID,
		room.Name,
		room.Topic,
		room.CreatedBy,
	).Scan(&room.CreatedAt)
	
	if err != nil {
		return fmt.Errorf("failed to create chat room: %w", err)
	}
	
	return nil
}

// GetRoomByID retrieves a chat room by ID
func (r *ChatRepository) GetRoomByID(ctx context.Context, id string) (*models.ChatRoom, error) {
	query := `
		SELECT id, class_id, name, topic, created_by, created_at
		FROM chat_rooms
		WHERE id = $1
	`
	
	var room models.ChatRoom
	err := r.pool.QueryRow(ctx, query, id).Scan(
		&room.ID,
		&room.ClassID,
		&room.Name,
		&room.Topic,
		&room.CreatedBy,
		&room.CreatedAt,
	)
	
	if err == pgx.ErrNoRows {
		return nil, fmt.Errorf("chat room not found")
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get chat room: %w", err)
	}
	
	return &room, nil
}

// ListRoomsByClass retrieves all chat rooms for a class
func (r *ChatRepository) ListRoomsByClass(ctx context.Context, classID string) ([]*models.ChatRoom, error) {
	query := `
		SELECT id, class_id, name, topic, created_by, created_at
		FROM chat_rooms
		WHERE class_id = $1
		ORDER BY created_at DESC
	`
	
	rows, err := r.pool.Query(ctx, query, classID)
	if err != nil {
		return nil, fmt.Errorf("failed to list chat rooms: %w", err)
	}
	defer rows.Close()
	
	var rooms []*models.ChatRoom
	for rows.Next() {
		var room models.ChatRoom
		err := rows.Scan(
			&room.ID,
			&room.ClassID,
			&room.Name,
			&room.Topic,
			&room.CreatedBy,
			&room.CreatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan chat room: %w", err)
		}
		rooms = append(rooms, &room)
	}
	
	return rooms, nil
}

// CreateMessage creates a new chat message
func (r *ChatRepository) CreateMessage(ctx context.Context, message *models.ChatMessage) error {
	query := `
		INSERT INTO chat_messages (id, chat_room_id, sender_id, sender_name, message_text, image_path)
		VALUES ($1, $2, $3, $4, $5, $6)
		RETURNING sent_at
	`
	
	err := r.pool.QueryRow(
		ctx,
		query,
		message.ID,
		message.ChatRoomID,
		message.SenderID,
		message.SenderName,
		message.MessageText,
		message.ImagePath,
	).Scan(&message.SentAt)
	
	if err != nil {
		return fmt.Errorf("failed to create message: %w", err)
	}
	
	return nil
}

// GetMessages retrieves messages for a chat room (past 7 days only)
func (r *ChatRepository) GetMessages(ctx context.Context, roomID string, limit int32, beforeTimestamp int64) ([]*models.ChatMessage, error) {
	query := `
		SELECT id, chat_room_id, sender_id, sender_name, message_text, image_path, sent_at
		FROM chat_messages
		WHERE chat_room_id = $1 
		  AND sent_at < $2
		  AND sent_at >= NOW() - INTERVAL '7 days'
		ORDER BY sent_at DESC
		LIMIT $3
	`
	
	// Convert Unix timestamp to time.Time
	beforeTime := time.Unix(beforeTimestamp, 0)
	if beforeTimestamp == 0 {
		beforeTime = time.Now()
	}
	
	rows, err := r.pool.Query(ctx, query, roomID, beforeTime, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to get messages: %w", err)
	}
	defer rows.Close()
	
	var messages []*models.ChatMessage
	for rows.Next() {
		var message models.ChatMessage
		err := rows.Scan(
			&message.ID,
			&message.ChatRoomID,
			&message.SenderID,
			&message.SenderName,
			&message.MessageText,
			&message.ImagePath,
			&message.SentAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan message: %w", err)
		}
		messages = append(messages, &message)
	}
	
	// Reverse to get chronological order
	for i, j := 0, len(messages)-1; i < j; i, j = i+1, j-1 {
		messages[i], messages[j] = messages[j], messages[i]
	}
	
	return messages, nil
}

// DeleteOldMessages deletes messages older than the retention period
func (r *ChatRepository) DeleteOldMessages(ctx context.Context, retentionDays int) (int64, error) {
	query := `
		DELETE FROM chat_messages
		WHERE sent_at < NOW() - INTERVAL '1 day' * $1
	`
	
	result, err := r.pool.Exec(ctx, query, retentionDays)
	if err != nil {
		return 0, fmt.Errorf("failed to delete old messages: %w", err)
	}
	
	return result.RowsAffected(), nil
}
