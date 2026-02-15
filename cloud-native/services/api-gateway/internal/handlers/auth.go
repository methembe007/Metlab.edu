package handlers

import (
	"context"
	"net/http"
	"strings"
	"time"

	"github.com/metlab/api-gateway/internal/transformers"
	authpb "github.com/metlab/shared/proto-gen/go/auth"
)

// TeacherSignupRequest represents the HTTP request for teacher signup
type TeacherSignupRequest struct {
	Email       string `json:"email"`
	Password    string `json:"password"`
	FullName    string `json:"full_name"`
	SubjectArea string `json:"subject_area"`
}

// TeacherLoginRequest represents the HTTP request for teacher login
type TeacherLoginRequest struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

// StudentSigninRequest represents the HTTP request for student signin
type StudentSigninRequest struct {
	TeacherName string `json:"teacher_name"`
	StudentName string `json:"student_name"`
	SigninCode  string `json:"signin_code"`
}

// GenerateSigninCodeRequest represents the HTTP request for generating signin codes
type GenerateSigninCodeRequest struct {
	TeacherID string `json:"teacher_id"`
	ClassID   string `json:"class_id"`
}

// AuthResponse represents the HTTP response for authentication endpoints
type AuthResponse struct {
	Token     string `json:"token"`
	UserID    string `json:"user_id"`
	Role      string `json:"role"`
	ExpiresAt int64  `json:"expires_at"`
}

// SigninCodeResponse represents the HTTP response for signin code generation
type SigninCodeResponse struct {
	Code      string `json:"code"`
	ExpiresAt int64  `json:"expires_at"`
}

// TeacherSignup handles POST /api/auth/teacher/signup
func (h *Handler) TeacherSignup(w http.ResponseWriter, r *http.Request) {
	// Decode request
	var req TeacherSignupRequest
	if err := transformers.DecodeJSONRequest(r, &req); err != nil {
		transformers.WriteError(w, http.StatusBadRequest, "INVALID_REQUEST", "Invalid request body")
		return
	}

	// Validate request
	if err := validateTeacherSignupRequest(&req); err != nil {
		transformers.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", err.Error())
		return
	}

	// Call gRPC service
	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()

	grpcReq := &authpb.TeacherSignupRequest{
		Email:       req.Email,
		Password:    req.Password,
		FullName:    req.FullName,
		SubjectArea: req.SubjectArea,
	}

	resp, err := h.clients.Auth.TeacherSignup(ctx, grpcReq)
	if err != nil {
		transformers.HandleGRPCError(w, err)
		return
	}

	// Transform and return response
	httpResp := AuthResponse{
		Token:     resp.Token,
		UserID:    resp.UserId,
		Role:      resp.Role,
		ExpiresAt: resp.ExpiresAt,
	}

	transformers.EncodeJSONResponse(w, http.StatusCreated, httpResp)
}

// TeacherLogin handles POST /api/auth/teacher/login
func (h *Handler) TeacherLogin(w http.ResponseWriter, r *http.Request) {
	// Decode request
	var req TeacherLoginRequest
	if err := transformers.DecodeJSONRequest(r, &req); err != nil {
		transformers.WriteError(w, http.StatusBadRequest, "INVALID_REQUEST", "Invalid request body")
		return
	}

	// Validate request
	if err := validateTeacherLoginRequest(&req); err != nil {
		transformers.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", err.Error())
		return
	}

	// Call gRPC service
	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()

	grpcReq := &authpb.LoginRequest{
		Email:    req.Email,
		Password: req.Password,
	}

	resp, err := h.clients.Auth.TeacherLogin(ctx, grpcReq)
	if err != nil {
		transformers.HandleGRPCError(w, err)
		return
	}

	// Transform and return response
	httpResp := AuthResponse{
		Token:     resp.Token,
		UserID:    resp.UserId,
		Role:      resp.Role,
		ExpiresAt: resp.ExpiresAt,
	}

	transformers.EncodeJSONResponse(w, http.StatusOK, httpResp)
}

// StudentSignin handles POST /api/auth/student/signin
func (h *Handler) StudentSignin(w http.ResponseWriter, r *http.Request) {
	// Decode request
	var req StudentSigninRequest
	if err := transformers.DecodeJSONRequest(r, &req); err != nil {
		transformers.WriteError(w, http.StatusBadRequest, "INVALID_REQUEST", "Invalid request body")
		return
	}

	// Validate request
	if err := validateStudentSigninRequest(&req); err != nil {
		transformers.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", err.Error())
		return
	}

	// Call gRPC service
	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()

	grpcReq := &authpb.StudentSigninRequest{
		TeacherName: req.TeacherName,
		StudentName: req.StudentName,
		SigninCode:  req.SigninCode,
	}

	resp, err := h.clients.Auth.StudentSignin(ctx, grpcReq)
	if err != nil {
		transformers.HandleGRPCError(w, err)
		return
	}

	// Transform and return response
	httpResp := AuthResponse{
		Token:     resp.Token,
		UserID:    resp.UserId,
		Role:      resp.Role,
		ExpiresAt: resp.ExpiresAt,
	}

	transformers.EncodeJSONResponse(w, http.StatusOK, httpResp)
}

// GenerateSigninCode handles POST /api/auth/codes/generate
func (h *Handler) GenerateSigninCode(w http.ResponseWriter, r *http.Request) {
	// Decode request
	var req GenerateSigninCodeRequest
	if err := transformers.DecodeJSONRequest(r, &req); err != nil {
		transformers.WriteError(w, http.StatusBadRequest, "INVALID_REQUEST", "Invalid request body")
		return
	}

	// Validate request
	if err := validateGenerateSigninCodeRequest(&req); err != nil {
		transformers.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", err.Error())
		return
	}

	// Call gRPC service
	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()

	grpcReq := &authpb.GenerateSigninCodeRequest{
		TeacherId: req.TeacherID,
		ClassId:   req.ClassID,
	}

	resp, err := h.clients.Auth.GenerateSigninCode(ctx, grpcReq)
	if err != nil {
		transformers.HandleGRPCError(w, err)
		return
	}

	// Transform and return response
	httpResp := SigninCodeResponse{
		Code:      resp.Code,
		ExpiresAt: resp.ExpiresAt,
	}

	transformers.EncodeJSONResponse(w, http.StatusCreated, httpResp)
}

// Validation functions

func validateTeacherSignupRequest(req *TeacherSignupRequest) error {
	if req.Email == "" {
		return &ValidationError{Field: "email", Message: "email is required"}
	}
	if !isValidEmail(req.Email) {
		return &ValidationError{Field: "email", Message: "email is invalid"}
	}
	if req.Password == "" {
		return &ValidationError{Field: "password", Message: "password is required"}
	}
	if len(req.Password) < 12 {
		return &ValidationError{Field: "password", Message: "password must be at least 12 characters"}
	}
	if req.FullName == "" {
		return &ValidationError{Field: "full_name", Message: "full_name is required"}
	}
	if len(strings.TrimSpace(req.FullName)) < 2 {
		return &ValidationError{Field: "full_name", Message: "full_name must be at least 2 characters"}
	}
	// subject_area is optional
	return nil
}

func validateTeacherLoginRequest(req *TeacherLoginRequest) error {
	if req.Email == "" {
		return &ValidationError{Field: "email", Message: "email is required"}
	}
	if !isValidEmail(req.Email) {
		return &ValidationError{Field: "email", Message: "email is invalid"}
	}
	if req.Password == "" {
		return &ValidationError{Field: "password", Message: "password is required"}
	}
	return nil
}

func validateStudentSigninRequest(req *StudentSigninRequest) error {
	if req.TeacherName == "" {
		return &ValidationError{Field: "teacher_name", Message: "teacher_name is required"}
	}
	if len(strings.TrimSpace(req.TeacherName)) < 2 {
		return &ValidationError{Field: "teacher_name", Message: "teacher_name must be at least 2 characters"}
	}
	if req.StudentName == "" {
		return &ValidationError{Field: "student_name", Message: "student_name is required"}
	}
	if len(strings.TrimSpace(req.StudentName)) < 2 {
		return &ValidationError{Field: "student_name", Message: "student_name must be at least 2 characters"}
	}
	if req.SigninCode == "" {
		return &ValidationError{Field: "signin_code", Message: "signin_code is required"}
	}
	if len(req.SigninCode) != 8 {
		return &ValidationError{Field: "signin_code", Message: "signin_code must be 8 characters"}
	}
	return nil
}

func validateGenerateSigninCodeRequest(req *GenerateSigninCodeRequest) error {
	if req.TeacherID == "" {
		return &ValidationError{Field: "teacher_id", Message: "teacher_id is required"}
	}
	if req.ClassID == "" {
		return &ValidationError{Field: "class_id", Message: "class_id is required"}
	}
	return nil
}

// isValidEmail performs basic email validation
func isValidEmail(email string) bool {
	email = strings.TrimSpace(email)
	if len(email) < 3 || len(email) > 254 {
		return false
	}
	// Basic check for @ symbol and domain
	parts := strings.Split(email, "@")
	if len(parts) != 2 {
		return false
	}
	if len(parts[0]) == 0 || len(parts[1]) == 0 {
		return false
	}
	// Check for at least one dot in domain
	if !strings.Contains(parts[1], ".") {
		return false
	}
	return true
}

// ValidationError represents a validation error
type ValidationError struct {
	Field   string
	Message string
}

func (e *ValidationError) Error() string {
	return e.Message
}

