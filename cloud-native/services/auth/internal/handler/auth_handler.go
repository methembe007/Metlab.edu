package handler

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/metlab/auth/internal/service"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/status"
	
	// Import will be updated once proto is generated
	// pb "metlab/proto-gen/go/auth"
)

// AuthHandler implements the gRPC AuthService interface
type AuthHandler struct {
	// Uncomment once proto is generated
	// pb.UnimplementedAuthServiceServer
	authService *service.AuthService
}

// NewAuthHandler creates a new auth handler
func NewAuthHandler(authService *service.AuthService) *AuthHandler {
	return &AuthHandler{
		authService: authService,
	}
}

// TeacherSignup handles teacher registration
// Once proto is generated, signature will be:
// func (h *AuthHandler) TeacherSignup(ctx context.Context, req *pb.TeacherSignupRequest) (*pb.AuthResponse, error)
func (h *AuthHandler) TeacherSignup(ctx context.Context, req interface{}) (interface{}, error) {
	// Type assertion will be replaced with actual proto types
	// For now, this is a placeholder implementation
	
	// Extract request fields (will use req.Email, req.Password, etc. once proto is generated)
	// email := req.Email
	// password := req.Password
	// fullName := req.FullName
	// subjectArea := req.SubjectArea
	
	// Placeholder validation
	email := ""
	password := ""
	fullName := ""
	subjectArea := ""
	
	// Validate required fields
	if email == "" {
		return nil, status.Error(codes.InvalidArgument, "email is required")
	}
	if password == "" {
		return nil, status.Error(codes.InvalidArgument, "password is required")
	}
	if fullName == "" {
		return nil, status.Error(codes.InvalidArgument, "full_name is required")
	}
	
	// Call service layer
	user, token, err := h.authService.TeacherSignup(ctx, email, password, fullName, subjectArea)
	if err != nil {
		// Map service errors to gRPC status codes
		if strings.Contains(err.Error(), "email already registered") {
			return nil, status.Error(codes.AlreadyExists, "email already registered")
		}
		if strings.Contains(err.Error(), "invalid password") {
			return nil, status.Error(codes.InvalidArgument, err.Error())
		}
		if strings.Contains(err.Error(), "invalid email") {
			return nil, status.Error(codes.InvalidArgument, err.Error())
		}
		return nil, status.Error(codes.Internal, fmt.Sprintf("failed to create teacher account: %v", err))
	}
	
	// Calculate token expiration (24 hours for teachers)
	expiresAt := time.Now().Add(24 * time.Hour).Unix()
	
	// Return response (will use pb.AuthResponse once proto is generated)
	// return &pb.AuthResponse{
	// 	Token:     token,
	// 	UserId:    user.ID.String(),
	// 	Role:      string(user.Role),
	// 	ExpiresAt: expiresAt,
	// }, nil
	
	// Placeholder return
	_ = user
	_ = token
	_ = expiresAt
	return nil, nil
}

// TeacherLogin handles teacher login
// Once proto is generated, signature will be:
// func (h *AuthHandler) TeacherLogin(ctx context.Context, req *pb.LoginRequest) (*pb.AuthResponse, error)
func (h *AuthHandler) TeacherLogin(ctx context.Context, req interface{}) (interface{}, error) {
	// Extract request fields (will use req.Email, req.Password once proto is generated)
	// email := req.Email
	// password := req.Password
	
	// Placeholder validation
	email := ""
	password := ""
	
	// Validate required fields
	if email == "" {
		return nil, status.Error(codes.InvalidArgument, "email is required")
	}
	if password == "" {
		return nil, status.Error(codes.InvalidArgument, "password is required")
	}
	
	// Extract IP address from metadata
	ipAddress := ""
	if md, ok := metadata.FromIncomingContext(ctx); ok {
		if ips := md.Get("x-forwarded-for"); len(ips) > 0 {
			ipAddress = ips[0]
		} else if ips := md.Get("x-real-ip"); len(ips) > 0 {
			ipAddress = ips[0]
		}
	}
	
	// Call service layer
	user, token, err := h.authService.TeacherLogin(ctx, email, password, ipAddress)
	if err != nil {
		// Map service errors to gRPC status codes
		if strings.Contains(err.Error(), "invalid credentials") {
			return nil, status.Error(codes.Unauthenticated, "invalid email or password")
		}
		if strings.Contains(err.Error(), "account locked") {
			return nil, status.Error(codes.PermissionDenied, "account locked due to too many failed login attempts. Please try again later.")
		}
		if strings.Contains(err.Error(), "account is inactive") {
			return nil, status.Error(codes.PermissionDenied, "account is inactive")
		}
		return nil, status.Error(codes.Internal, "failed to login")
	}
	
	// Calculate token expiration (24 hours for teachers)
	expiresAt := time.Now().Add(24 * time.Hour).Unix()
	
	// Return response (will use pb.AuthResponse once proto is generated)
	// return &pb.AuthResponse{
	// 	Token:     token,
	// 	UserId:    user.ID.String(),
	// 	Role:      string(user.Role),
	// 	ExpiresAt: expiresAt,
	// }, nil
	
	// Placeholder return
	_ = user
	_ = token
	_ = expiresAt
	return nil, nil
}

// ValidateToken validates a JWT token
// Once proto is generated, signature will be:
// func (h *AuthHandler) ValidateToken(ctx context.Context, req *pb.ValidateTokenRequest) (*pb.ValidateTokenResponse, error)
func (h *AuthHandler) ValidateToken(ctx context.Context, req interface{}) (interface{}, error) {
	// This will be implemented in a future task
	// For now, return not implemented
	return nil, status.Error(codes.Unimplemented, "ValidateToken not yet implemented")
}

// GenerateSigninCode generates a signin code for student registration
// Once proto is generated, signature will be:
// func (h *AuthHandler) GenerateSigninCode(ctx context.Context, req *pb.GenerateSigninCodeRequest) (*pb.SigninCodeResponse, error)
func (h *AuthHandler) GenerateSigninCode(ctx context.Context, req interface{}) (interface{}, error) {
	// Extract request fields (will use req.TeacherId, req.ClassId once proto is generated)
	// teacherID := req.TeacherId
	// classID := req.ClassId
	
	// Placeholder validation - these will be replaced with actual proto fields
	teacherIDStr := ""
	classIDStr := ""
	
	// Validate required fields
	if teacherIDStr == "" {
		return nil, status.Error(codes.InvalidArgument, "teacher_id is required")
	}
	if classIDStr == "" {
		return nil, status.Error(codes.InvalidArgument, "class_id is required")
	}
	
	// Parse UUIDs
	teacherID, err := uuid.Parse(teacherIDStr)
	if err != nil {
		return nil, status.Error(codes.InvalidArgument, "invalid teacher_id format")
	}
	
	classID, err := uuid.Parse(classIDStr)
	if err != nil {
		return nil, status.Error(codes.InvalidArgument, "invalid class_id format")
	}
	
	// Call service layer
	signinCode, err := h.authService.GenerateSigninCode(ctx, teacherID, classID)
	if err != nil {
		// Map service errors to gRPC status codes
		if strings.Contains(err.Error(), "teacher not found") {
			return nil, status.Error(codes.NotFound, "teacher not found")
		}
		if strings.Contains(err.Error(), "failed to generate unique code") {
			return nil, status.Error(codes.Internal, "failed to generate unique code, please try again")
		}
		return nil, status.Error(codes.Internal, fmt.Sprintf("failed to generate signin code: %v", err))
	}
	
	// Return response (will use pb.SigninCodeResponse once proto is generated)
	// return &pb.SigninCodeResponse{
	// 	Code:      signinCode.Code,
	// 	ExpiresAt: signinCode.ExpiresAt.Unix(),
	// }, nil
	
	// Placeholder return
	_ = signinCode
	return nil, nil
}

// StudentSignin handles student signin with code
// Once proto is generated, signature will be:
// func (h *AuthHandler) StudentSignin(ctx context.Context, req *pb.StudentSigninRequest) (*pb.AuthResponse, error)
func (h *AuthHandler) StudentSignin(ctx context.Context, req interface{}) (interface{}, error) {
	// Extract request fields (will use req.TeacherName, req.StudentName, req.SigninCode once proto is generated)
	// teacherName := req.TeacherName
	// studentName := req.StudentName
	// signinCode := req.SigninCode
	
	// Placeholder validation - these will be replaced with actual proto fields
	teacherName := ""
	studentName := ""
	signinCode := ""
	
	// Validate required fields
	if teacherName == "" {
		return nil, status.Error(codes.InvalidArgument, "teacher_name is required")
	}
	if studentName == "" {
		return nil, status.Error(codes.InvalidArgument, "student_name is required")
	}
	if signinCode == "" {
		return nil, status.Error(codes.InvalidArgument, "signin_code is required")
	}
	
	// Call service layer
	user, token, err := h.authService.StudentSignin(ctx, teacherName, studentName, signinCode)
	if err != nil {
		// Map service errors to gRPC status codes
		if strings.Contains(err.Error(), "invalid signin code") || 
		   strings.Contains(err.Error(), "signin code has already been used") ||
		   strings.Contains(err.Error(), "signin code has expired") {
			return nil, status.Error(codes.InvalidArgument, err.Error())
		}
		if strings.Contains(err.Error(), "invalid teacher name") {
			return nil, status.Error(codes.NotFound, "teacher not found with the provided name")
		}
		if strings.Contains(err.Error(), "signin code does not match") {
			return nil, status.Error(codes.PermissionDenied, "signin code does not match the specified teacher")
		}
		if strings.Contains(err.Error(), "student name does not match") {
			return nil, status.Error(codes.PermissionDenied, "student name does not match the signin code")
		}
		if strings.Contains(err.Error(), "account is inactive") {
			return nil, status.Error(codes.PermissionDenied, "account is inactive")
		}
		return nil, status.Error(codes.Internal, "failed to signin student")
	}
	
	// Calculate token expiration (7 days for students)
	expiresAt := time.Now().Add(7 * 24 * time.Hour).Unix()
	
	// Return response (will use pb.AuthResponse once proto is generated)
	// return &pb.AuthResponse{
	// 	Token:     token,
	// 	UserId:    user.ID.String(),
	// 	Role:      string(user.Role),
	// 	ExpiresAt: expiresAt,
	// }, nil
	
	// Placeholder return
	_ = user
	_ = token
	_ = expiresAt
	return nil, nil
}
