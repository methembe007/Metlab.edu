-- Drop all indexes created in the up migration

BEGIN;

-- Analytics indexes
DROP INDEX IF EXISTS idx_pdf_downloads_downloaded_at;
DROP INDEX IF EXISTS idx_pdf_downloads_pdf;
DROP INDEX IF EXISTS idx_pdf_downloads_student;
DROP INDEX IF EXISTS idx_student_logins_login_at;
DROP INDEX IF EXISTS idx_student_logins_student_date;

-- Collaboration indexes
DROP INDEX IF EXISTS idx_chat_messages_sender;
DROP INDEX IF EXISTS idx_chat_messages_room_time;
DROP INDEX IF EXISTS idx_chat_rooms_created_by;
DROP INDEX IF EXISTS idx_chat_rooms_class;
DROP INDEX IF EXISTS idx_study_group_members_student;
DROP INDEX IF EXISTS idx_study_groups_created_by;
DROP INDEX IF EXISTS idx_study_groups_class;

-- Homework indexes
DROP INDEX IF EXISTS idx_homework_grades_graded_by;
DROP INDEX IF EXISTS idx_homework_grades_submission;
DROP INDEX IF EXISTS idx_homework_submissions_submitted_at;
DROP INDEX IF EXISTS idx_homework_submissions_status;
DROP INDEX IF EXISTS idx_homework_submissions_student;
DROP INDEX IF EXISTS idx_homework_submissions_assignment;
DROP INDEX IF EXISTS idx_homework_assignments_due_date;
DROP INDEX IF EXISTS idx_homework_assignments_teacher;
DROP INDEX IF EXISTS idx_homework_assignments_class;

-- PDF indexes
DROP INDEX IF EXISTS idx_pdfs_created_at;
DROP INDEX IF EXISTS idx_pdfs_teacher;
DROP INDEX IF EXISTS idx_pdfs_class;

-- Video indexes
DROP INDEX IF EXISTS idx_video_views_updated_at;
DROP INDEX IF EXISTS idx_video_views_student;
DROP INDEX IF EXISTS idx_video_views_video_student;
DROP INDEX IF EXISTS idx_video_thumbnails_video;
DROP INDEX IF EXISTS idx_video_variants_video;
DROP INDEX IF EXISTS idx_videos_created_at;
DROP INDEX IF EXISTS idx_videos_status;
DROP INDEX IF EXISTS idx_videos_teacher;
DROP INDEX IF EXISTS idx_videos_class;

-- Authentication and user management indexes
DROP INDEX IF EXISTS idx_classes_is_active;
DROP INDEX IF EXISTS idx_classes_teacher;
DROP INDEX IF EXISTS idx_students_teacher;
DROP INDEX IF EXISTS idx_signin_codes_class;
DROP INDEX IF EXISTS idx_signin_codes_expires;
DROP INDEX IF EXISTS idx_signin_codes_teacher;
DROP INDEX IF EXISTS idx_users_is_active;
DROP INDEX IF EXISTS idx_users_role;
DROP INDEX IF EXISTS idx_users_email;

COMMIT;
