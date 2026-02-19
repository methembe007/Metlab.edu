-- Create study_groups table
CREATE TABLE IF NOT EXISTS study_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    class_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_by UUID NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    max_members INT NOT NULL DEFAULT 10,
    CONSTRAINT chk_max_members CHECK (max_members > 0 AND max_members <= 10)
);

-- Create index for efficient queries by class
CREATE INDEX idx_study_groups_class ON study_groups(class_id);

-- Create index for queries by creator
CREATE INDEX idx_study_groups_creator ON study_groups(created_by);

-- Add comments
COMMENT ON TABLE study_groups IS 'Study groups created by students for collaboration';
COMMENT ON COLUMN study_groups.class_id IS 'References classes.id (foreign key will be added when classes table exists)';
COMMENT ON COLUMN study_groups.created_by IS 'References students.id - the student who created the group';
COMMENT ON COLUMN study_groups.max_members IS 'Maximum number of members allowed in the group (default 10)';
