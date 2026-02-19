package models

import (
	"time"
)

// StudyGroup represents a study group in the database
type StudyGroup struct {
	ID          string    `db:"id"`
	ClassID     string    `db:"class_id"`
	Name        string    `db:"name"`
	Description string    `db:"description"`
	CreatedBy   string    `db:"created_by"`
	CreatedAt   time.Time `db:"created_at"`
	MaxMembers  int32     `db:"max_members"`
}

// StudyGroupMember represents a member of a study group
type StudyGroupMember struct {
	StudyGroupID string    `db:"study_group_id"`
	StudentID    string    `db:"student_id"`
	JoinedAt     time.Time `db:"joined_at"`
}

// ChatRoom represents a chat room in the database
type ChatRoom struct {
	ID        string    `db:"id"`
	ClassID   string    `db:"class_id"`
	Name      string    `db:"name"`
	Topic     string    `db:"topic"`
	CreatedBy string    `db:"created_by"`
	CreatedAt time.Time `db:"created_at"`
}

// ChatMessage represents a chat message in the database
type ChatMessage struct {
	ID         string    `db:"id"`
	ChatRoomID string    `db:"chat_room_id"`
	SenderID   string    `db:"sender_id"`
	SenderName string    `db:"sender_name"`
	MessageText string   `db:"message_text"`
	ImagePath  *string   `db:"image_path"`
	SentAt     time.Time `db:"sent_at"`
}
