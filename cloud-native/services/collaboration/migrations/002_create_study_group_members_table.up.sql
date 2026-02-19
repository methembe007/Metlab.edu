-- Create study_group_members table
CREATE TABLE IF NOT EXISTS study_group_members (
    study_group_id UUID NOT NULL REFERENCES study_groups(id) ON DELETE CASCADE,
    student_id UUID NOT NULL,
    joined_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (study_group_id, student_id)
);

-- Create index for efficient queries by student
CREATE INDEX idx_study_group_members_student ON study_group_members(student_id);

-- Create index for queries by join date
CREATE INDEX idx_study_group_members_joined ON study_group_members(joined_at DESC);

-- Add comments
COMMENT ON TABLE study_group_members IS 'Members of study groups';
COMMENT ON COLUMN study_group_members.student_id IS 'References students.id (foreign key will be added when students table exists)';
COMMENT ON COLUMN study_group_members.joined_at IS 'Timestamp when the student joined the group';
