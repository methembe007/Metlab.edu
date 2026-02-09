-- Create indexes for performance optimization

BEGIN;

-- Authentication and user management indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE INDEX idx_signin_codes_teacher ON signin_codes(teacher_id);
CREATE INDEX idx_signin_codes_expires ON signin_codes(expires_at) WHERE NOT used;
CREATE INDEX idx_signin_codes_class ON signin_codes(class_id);
CREATE INDEX idx_students_teacher ON students(teacher_id);
CREATE INDEX idx_classes_teacher ON classes(teacher_id);
CREATE INDEX idx_classes_is_active ON classes(is_active);

-- Video indexes
CREATE INDEX idx_videos_class ON videos(class_id);
CREATE INDEX idx_videos_teacher ON videos(teacher_id);
CREATE INDEX idx_videos_status ON videos(status);
CREATE INDEX idx_videos_created_at ON videos(created_at DESC);
CREATE INDEX idx_video_variants_video ON video_variants(video_id);
CREATE INDEX idx_video_thumbnails_video ON video_thumbnails(video_id);
CREATE INDEX idx_video_views_video_student ON video_views(video_id, student_id);
CREATE INDEX idx_video_views_student ON video_views(student_id);
CREATE INDEX idx_video_views_updated_at ON video_views(updated_at DESC);

-- PDF indexes
CREATE INDEX idx_pdfs_class ON pdfs(class_id);
CREATE INDEX idx_pdfs_teacher ON pdfs(teacher_id);
CREATE INDEX idx_pdfs_created_at ON pdfs(created_at DESC);

-- Homework indexes
CREATE INDEX idx_homework_assignments_class ON homework_assignments(class_id);
CREATE INDEX idx_homework_assignments_teacher ON homework_assignments(teacher_id);
CREATE INDEX idx_homework_assignments_due_date ON homework_assignments(due_date);
CREATE INDEX idx_homework_submissions_assignment ON homework_submissions(assignment_id);
CREATE INDEX idx_homework_submissions_student ON homework_submissions(student_id);
CREATE INDEX idx_homework_submissions_status ON homework_submissions(status);
CREATE INDEX idx_homework_submissions_submitted_at ON homework_submissions(submitted_at DESC);
CREATE INDEX idx_homework_grades_submission ON homework_grades(submission_id);
CREATE INDEX idx_homework_grades_graded_by ON homework_grades(graded_by);

-- Collaboration indexes
CREATE INDEX idx_study_groups_class ON study_groups(class_id);
CREATE INDEX idx_study_groups_created_by ON study_groups(created_by);
CREATE INDEX idx_study_group_members_student ON study_group_members(student_id);
CREATE INDEX idx_chat_rooms_class ON chat_rooms(class_id);
CREATE INDEX idx_chat_rooms_created_by ON chat_rooms(created_by);
CREATE INDEX idx_chat_messages_room_time ON chat_messages(chat_room_id, sent_at DESC);
CREATE INDEX idx_chat_messages_sender ON chat_messages(sender_id);

-- Analytics indexes
CREATE INDEX idx_student_logins_student_date ON student_logins(student_id, login_at DESC);
CREATE INDEX idx_student_logins_login_at ON student_logins(login_at DESC);
CREATE INDEX idx_pdf_downloads_student ON pdf_downloads(student_id);
CREATE INDEX idx_pdf_downloads_pdf ON pdf_downloads(pdf_id);
CREATE INDEX idx_pdf_downloads_downloaded_at ON pdf_downloads(downloaded_at DESC);

COMMIT;
