package service

import (
	"context"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/metlab/auth/internal/config"
	"github.com/metlab/auth/internal/models"
	"github.com/metlab/auth/internal/repository"
	"github.com/metlab/auth/internal/utils"
	"golang.org/x/crypto/bcrypt"
)

// AuthService handles authentication business logic
type AuthService struct {
	config              *config.Config
	userRepo            *repository.UserRepository
	teacherRepo         *repository.TeacherRepository
	studentRepo         *repository.StudentRepository
	signinCodeRepo      *repository.SigninCodeRepository
	loginAttemptRepo    *repository.LoginAttemptRepository
}

// NewAuthService creates a new auth service
func NewAuthService(
	cfg *config.Config,
	userRepo *repository.UserRepository,
	teacherRepo *repository.TeacherRepository,
	studentRepo *repository.StudentRepository,
	signinCodeRepo *repository.SigninCodeRepository,
	loginAttemptRepo *repository.LoginAttemptRepository,
) *AuthService {
	return &AuthService{
		config:           cfg,
		userRepo:         userRepo,
		teacherRepo:      teacherRepo,
		studentRepo:      studentRepo,
		signinCodeRepo:   signinCodeRepo,
		loginAttemptRepo: loginAttemptRepo,
	}
}

// TeacherSignup handles teacher registration
func (s *AuthService) TeacherSignup(ctx context.Context, email, password, fullName, subjectArea string) (*models.User, string, error) {
	// Validate email format
	if err := utils.ValidateEmail(email); err != nil {
		return nil, "", fmt.Errorf("invalid email: %w", err)
	}
	
	// Validate password requirements
	if err := utils.ValidatePassword(password); err != nil {
		return nil, "", fmt.Errorf("invalid password: %w", err)
	}
	
	// Check if email already exists
	exists, err := s.userRepo.EmailExists(ctx, email)
	if err != nil {
		return nil, "", fmt.Errorf("failed to check email: %w", err)
	}
	if exists {
		return nil, "", fmt.Errorf("email already registered")
	}
	
	// Hash password
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return nil, "", fmt.Errorf("failed to hash password: %w", err)
	}
	
	// Create user
	userID := uuid.New()
	now := time.Now()
	hashedStr := string(hashedPassword)
	
	user := &models.User{
		ID:           userID,
		Email:        &email,
		PasswordHash: &hashedStr,
		FullName:     fullName,
		Role:         models.RoleTeacher,
		CreatedAt:    now,
		UpdatedAt:    now,
		IsActive:     true,
	}
	
	if err := s.userRepo.CreateUser(ctx, user); err != nil {
		return nil, "", fmt.Errorf("failed to create user: %w", err)
	}
	
	// Create teacher record
	teacher := &models.Teacher{
		ID:          userID,
		SubjectArea: &subjectArea,
		Verified:    false,
	}
	
	if err := s.teacherRepo.CreateTeacher(ctx, teacher); err != nil {
		return nil, "", fmt.Errorf("failed to create teacher: %w", err)
	}
	
	// Generate JWT token
	token, err := utils.GenerateJWT(userID, string(models.RoleTeacher), s.config.JWTSecret, s.config.JWTExpiry)
	if err != nil {
		return nil, "", fmt.Errorf("failed to generate token: %w", err)
	}
	
	return user, token, nil
}

// TeacherLogin handles teacher login
func (s *AuthService) TeacherLogin(ctx context.Context, email, password, ipAddress string) (*models.User, string, error) {
	// Validate email format
	if err := utils.ValidateEmail(email); err != nil {
		return nil, "", fmt.Errorf("invalid credentials")
	}
	
	// Check for account lockout
	lockoutTime := time.Now().Add(-s.config.LockoutDuration)
	failedAttempts, err := s.loginAttemptRepo.GetRecentFailedAttempts(ctx, email, lockoutTime)
	if err != nil {
		return nil, "", fmt.Errorf("failed to check login attempts: %w", err)
	}
	
	// Check if there was a successful login after the lockout period
	hasSuccessfulLogin, err := s.loginAttemptRepo.HasRecentSuccessfulLogin(ctx, email, lockoutTime)
	if err != nil {
		return nil, "", fmt.Errorf("failed to check successful login: %w", err)
	}
	
	// If there are too many failed attempts and no successful login, account is locked
	if failedAttempts >= s.config.MaxLoginAttempts && !hasSuccessfulLogin {
		return nil, "", fmt.Errorf("account locked due to too many failed login attempts")
	}
	
	// Get user by email
	user, err := s.userRepo.GetUserByEmail(ctx, email)
	if err != nil {
		// Record failed attempt
		s.recordLoginAttempt(ctx, email, false, ipAddress)
		return nil, "", fmt.Errorf("invalid credentials")
	}
	
	// Verify user is a teacher
	if user.Role != models.RoleTeacher {
		s.recordLoginAttempt(ctx, email, false, ipAddress)
		return nil, "", fmt.Errorf("invalid credentials")
	}
	
	// Check if user is active
	if !user.IsActive {
		return nil, "", fmt.Errorf("account is inactive")
	}
	
	// Verify password
	if user.PasswordHash == nil {
		s.recordLoginAttempt(ctx, email, false, ipAddress)
		return nil, "", fmt.Errorf("invalid credentials")
	}
	
	if err := bcrypt.CompareHashAndPassword([]byte(*user.PasswordHash), []byte(password)); err != nil {
		s.recordLoginAttempt(ctx, email, false, ipAddress)
		return nil, "", fmt.Errorf("invalid credentials")
	}
	
	// Record successful login attempt
	s.recordLoginAttempt(ctx, email, true, ipAddress)
	
	// Update last login
	if err := s.userRepo.UpdateLastLogin(ctx, user.ID); err != nil {
		// Log error but don't fail the login
		fmt.Printf("failed to update last login: %v\n", err)
	}
	
	// Generate JWT token
	token, err := utils.GenerateJWT(user.ID, string(user.Role), s.config.JWTSecret, s.config.JWTExpiry)
	if err != nil {
		return nil, "", fmt.Errorf("failed to generate token: %w", err)
	}
	
	return user, token, nil
}

// GenerateSigninCode generates a unique signin code for student registration
func (s *AuthService) GenerateSigninCode(ctx context.Context, teacherID, classID uuid.UUID) (*models.SigninCode, error) {
	// Validate teacher exists
	teacher, err := s.teacherRepo.GetTeacherByID(ctx, teacherID)
	if err != nil {
		return nil, fmt.Errorf("teacher not found: %w", err)
	}
	if teacher == nil {
		return nil, fmt.Errorf("teacher not found")
	}
	
	// Generate unique code with retry logic
	const maxRetries = 10
	var code string
	var exists bool
	
	for i := 0; i < maxRetries; i++ {
		code, err = utils.GenerateSigninCode()
		if err != nil {
			return nil, fmt.Errorf("failed to generate code: %w", err)
		}
		
		// Check if code already exists
		exists, err = s.signinCodeRepo.CodeExists(ctx, code)
		if err != nil {
			return nil, fmt.Errorf("failed to check code existence: %w", err)
		}
		
		if !exists {
			break
		}
	}
	
	if exists {
		return nil, fmt.Errorf("failed to generate unique code after %d attempts", maxRetries)
	}
	
	// Create signin code with 30-day expiration
	now := time.Now()
	expiresAt := now.Add(30 * 24 * time.Hour) // 30 days
	
	signinCode := &models.SigninCode{
		Code:      code,
		TeacherID: teacherID,
		ClassID:   classID,
		CreatedAt: now,
		ExpiresAt: expiresAt,
		Used:      false,
	}
	
	// Save to database
	if err := s.signinCodeRepo.CreateSigninCode(ctx, signinCode); err != nil {
		return nil, fmt.Errorf("failed to create signin code: %w", err)
	}
	
	return signinCode, nil
}

// ValidateSigninCode validates a signin code and checks if it's usable
func (s *AuthService) ValidateSigninCode(ctx context.Context, code string) (*models.SigninCode, error) {
	// Get signin code
	signinCode, err := s.signinCodeRepo.GetSigninCode(ctx, code)
	if err != nil {
		return nil, fmt.Errorf("invalid signin code")
	}
	
	// Check if already used
	if signinCode.Used {
		return nil, fmt.Errorf("signin code has already been used")
	}
	
	// Check if expired
	if time.Now().After(signinCode.ExpiresAt) {
		return nil, fmt.Errorf("signin code has expired")
	}
	
	return signinCode, nil
}

// StudentSignin handles student signin with code
func (s *AuthService) StudentSignin(ctx context.Context, teacherName, studentName, signinCode string) (*models.User, string, error) {
	// Validate signin code
	code, err := s.ValidateSigninCode(ctx, signinCode)
	if err != nil {
		return nil, "", err
	}
	
	// Get teacher by name to verify it matches the signin code
	teacher, err := s.teacherRepo.GetTeacherByName(ctx, teacherName)
	if err != nil {
		return nil, "", fmt.Errorf("invalid teacher name")
	}
	
	// Verify the signin code belongs to the specified teacher
	if teacher.ID != code.TeacherID {
		return nil, "", fmt.Errorf("signin code does not match the specified teacher")
	}
	
	// Check if this is a first-time signin or returning student
	// Try to find existing student by signin code
	existingStudent, err := s.studentRepo.GetStudentBySigninCode(ctx, signinCode)
	if err == nil && existingStudent != nil {
		// Returning student - get their user record
		user, err := s.userRepo.GetUserByID(ctx, existingStudent.ID)
		if err != nil {
			return nil, "", fmt.Errorf("failed to get student user: %w", err)
		}
		
		// Verify student name matches
		if user.FullName != studentName {
			return nil, "", fmt.Errorf("student name does not match the signin code")
		}
		
		// Check if user is active
		if !user.IsActive {
			return nil, "", fmt.Errorf("account is inactive")
		}
		
		// Update last login
		if err := s.userRepo.UpdateLastLogin(ctx, user.ID); err != nil {
			fmt.Printf("failed to update last login: %v\n", err)
		}
		
		// Generate JWT token with 7-day expiration for students
		token, err := utils.GenerateJWT(user.ID, string(models.RoleStudent), s.config.JWTSecret, 7*24*time.Hour)
		if err != nil {
			return nil, "", fmt.Errorf("failed to generate token: %w", err)
		}
		
		return user, token, nil
	}
	
	// First-time signin - create new student account
	userID := uuid.New()
	now := time.Now()
	
	// Create user record (students don't have email or password)
	user := &models.User{
		ID:           userID,
		Email:        nil,
		PasswordHash: nil,
		FullName:     studentName,
		Role:         models.RoleStudent,
		CreatedAt:    now,
		UpdatedAt:    now,
		IsActive:     true,
	}
	
	if err := s.userRepo.CreateUser(ctx, user); err != nil {
		return nil, "", fmt.Errorf("failed to create student user: %w", err)
	}
	
	// Create student record
	student := &models.Student{
		ID:         userID,
		TeacherID:  teacher.ID,
		SigninCode: &signinCode,
	}
	
	if err := s.studentRepo.CreateStudent(ctx, student); err != nil {
		return nil, "", fmt.Errorf("failed to create student: %w", err)
	}
	
	// Mark signin code as used
	if err := s.signinCodeRepo.MarkSigninCodeAsUsed(ctx, signinCode, userID); err != nil {
		return nil, "", fmt.Errorf("failed to mark signin code as used: %w", err)
	}
	
	// Generate JWT token with 7-day expiration for students
	token, err := utils.GenerateJWT(userID, string(models.RoleStudent), s.config.JWTSecret, 7*24*time.Hour)
	if err != nil {
		return nil, "", fmt.Errorf("failed to generate token: %w", err)
	}
	
	return user, token, nil
}

// ValidateToken validates a JWT token and returns user information
func (s *AuthService) ValidateToken(ctx context.Context, token string) (bool, string, string, []string, string, error) {
	// Validate the JWT token
	claims, err := utils.ValidateJWT(token, s.config.JWTSecret)
	if err != nil {
		return false, "", "", nil, "", fmt.Errorf("invalid token: %w", err)
	}
	
	// Parse user ID
	userID, err := uuid.Parse(claims.UserID)
	if err != nil {
		return false, "", "", nil, "", fmt.Errorf("invalid user_id in token: %w", err)
	}
	
	// Verify user exists and is active
	user, err := s.userRepo.GetUserByID(ctx, userID)
	if err != nil {
		return false, "", "", nil, "", fmt.Errorf("user not found: %w", err)
	}
	
	if !user.IsActive {
		return false, "", "", nil, "", fmt.Errorf("user account is inactive")
	}
	
	// Extract teacher_id if the user is a student
	teacherID := claims.TeacherID
	if user.Role == models.RoleStudent && teacherID == "" {
		// Get student record to retrieve teacher_id
		student, err := s.studentRepo.GetStudentByID(ctx, userID)
		if err == nil && student != nil {
			teacherID = student.TeacherID.String()
		}
	}
	
	// Return validation result with user information
	return true, claims.UserID, claims.Role, claims.ClassIDs, teacherID, nil
}

// recordLoginAttempt records a login attempt (helper method)
func (s *AuthService) recordLoginAttempt(ctx context.Context, email string, successful bool, ipAddress string) {
	attempt := &models.LoginAttempt{
		ID:         uuid.New(),
		Email:      email,
		AttemptAt:  time.Now(),
		Successful: successful,
		IPAddress:  &ipAddress,
	}
	
	if err := s.loginAttemptRepo.RecordLoginAttempt(ctx, attempt); err != nil {
		// Log error but don't fail the operation
		fmt.Printf("failed to record login attempt: %v\n", err)
	}
}
