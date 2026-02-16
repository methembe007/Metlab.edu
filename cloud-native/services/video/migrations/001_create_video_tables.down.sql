-- Drop indexes
DROP INDEX IF EXISTS idx_video_views_video;
DROP INDEX IF EXISTS idx_video_views_student;
DROP INDEX IF EXISTS idx_video_views_video_student;
DROP INDEX IF EXISTS idx_video_thumbnails_video;
DROP INDEX IF EXISTS idx_video_variants_video;
DROP INDEX IF EXISTS idx_videos_status;
DROP INDEX IF EXISTS idx_videos_teacher;
DROP INDEX IF EXISTS idx_videos_class;

-- Drop tables in reverse order (respecting foreign key constraints)
DROP TABLE IF EXISTS video_views;
DROP TABLE IF EXISTS video_thumbnails;
DROP TABLE IF EXISTS video_variants;
DROP TABLE IF EXISTS videos;
