-- Create chat_rooms table
CREATE TABLE IF NOT EXISTS chat_rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    class_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    topic VARCHAR(500),
    created_by UUID NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create index for efficient queries by class
CREATE INDEX idx_chat_rooms_class ON chat_rooms(class_id);

-- Create index for queries by creator
CREATE INDEX idx_chat_rooms_creator ON chat_rooms(created_by);

-- Create index for queries by creation date
CREATE INDEX idx_chat_rooms_created ON chat_rooms(created_at DESC);

-- Add comments
COMMENT ON TABLE chat_rooms IS 'Chat rooms for student communication within a class';
COMMENT ON COLUMN chat_rooms.class_id IS 'References classes.id (foreign key will be added when classes table exists)';
COMMENT ON COLUMN chat_rooms.created_by IS 'References students.id - the student who created the chat room';
COMMENT ON COLUMN chat_rooms.topic IS 'Optional topic or description of the chat room';
