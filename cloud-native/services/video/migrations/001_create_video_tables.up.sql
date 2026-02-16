-- Create videos table
CREATE TABLE IF NOT EXISTS videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID NOT NULL,
    class_id UUID NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    original_filename VARCHAR(255),
    storage_path VARCHAR(500),
    duration_seconds INT DEFAULT 0,
    file_size_bytes BIGINT,
    status VARCHAR(20) NOT NULL CHECK (status IN ('uploading', 'processing', 'ready', 'failed')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create video_variants table
CREATE TABLE IF NOT EXISTS video_variants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    resolution VARCHAR(20) NOT NULL, -- '1080p', '720p', '480p', '360p'
    bitrate_kbps INT NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    file_size_bytes BIGINT
);

-- Create video_thumbnails table
CREATE TABLE IF NOT EXISTS video_thumbnails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    timestamp_percent INT NOT NULL CHECK (timestamp_percent IN (0, 25, 50, 75)),
    storage_path VARCHAR(500) NOT NULL
);

-- Create video_views table
CREATE TABLE IF NOT EXISTS video_views (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    student_id UUID NOT NULL,
    started_at TIMESTAMP DEFAULT NOW(),
    last_position_seconds INT DEFAULT 0,
    total_watch_seconds INT DEFAULT 0,
    completed BOOLEAN DEFAULT false,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(video_id, student_id)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_videos_class ON videos(class_id);
CREATE INDEX IF NOT EXISTS idx_videos_teacher ON videos(teacher_id);
CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status);
CREATE INDEX IF NOT EXISTS idx_video_variants_video ON video_variants(video_id);
CREATE INDEX IF NOT EXISTS idx_video_thumbnails_video ON video_thumbnails(video_id);
CREATE INDEX IF NOT EXISTS idx_video_views_video_student ON video_views(video_id, student_id);
CREATE INDEX IF NOT EXISTS idx_video_views_student ON video_views(student_id);
CREATE INDEX IF NOT EXISTS idx_video_views_video ON video_views(video_id);
