-- Create chat_messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_room_id UUID NOT NULL REFERENCES chat_rooms(id) ON DELETE CASCADE,
    sender_id UUID NOT NULL,
    sender_name VARCHAR(255) NOT NULL,
    message_text TEXT,
    image_path VARCHAR(500),
    sent_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_message_content CHECK (
        (message_text IS NOT NULL AND message_text != '') OR 
        (image_path IS NOT NULL AND image_path != '')
    )
);

-- Create index for efficient queries by chat room and time
CREATE INDEX idx_chat_messages_room_time ON chat_messages(chat_room_id, sent_at DESC);

-- Create index for queries by sender
CREATE INDEX idx_chat_messages_sender ON chat_messages(sender_id);

-- Create index for time-based cleanup queries
CREATE INDEX idx_chat_messages_sent_at ON chat_messages(sent_at DESC);

-- Add comments
COMMENT ON TABLE chat_messages IS 'Messages sent in chat rooms';
COMMENT ON COLUMN chat_messages.sender_id IS 'References students.id (foreign key will be added when students table exists)';
COMMENT ON COLUMN chat_messages.sender_name IS 'Cached sender name for display purposes';
COMMENT ON COLUMN chat_messages.message_text IS 'Text content of the message (max 1000 characters)';
COMMENT ON COLUMN chat_messages.image_path IS 'Path to image attachment in S3 storage';
COMMENT ON COLUMN chat_messages.sent_at IS 'Timestamp when the message was sent';
