package middleware

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"

	authpb "github.com/metlab/shared/proto-gen/go/auth"
	"google.golang.org/grpc"
)

// mockAuthClient is a mock implementation of AuthServiceClient for testing
type mockAuthClient struct {
	validateFunc func(ctx context.Context, req *authpb.ValidateTokenRequest, opts ...grpc.CallOption) (*authpb.ValidateTokenResponse, error)
}

func (m *mockAuthClient) ValidateToken(ctx context.Context, req *authpb.ValidateTokenRequest, opts ...grpc.CallOption) (*authpb.ValidateTokenResponse, error) {
	if m.validateFunc != nil {
		return m.validateFunc(ctx, req, opts...)
	}
	return &authpb.ValidateTokenResponse{Valid: true}, nil
}

func (m *mockAuthClient) TeacherSignup(ctx context.Context, req *authpb.TeacherSignupRequest, opts ...grpc.CallOption) (*authpb.AuthResponse, error) {
	return nil, nil
}

func (m *mockAuthClient) TeacherLogin(ctx context.Context, req *authpb.LoginRequest, opts ...grpc.CallOption) (*authpb.AuthResponse, error) {
	return nil, nil
}

func (m *mockAuthClient) StudentSignin(ctx context.Context, req *authpb.StudentSigninRequest, opts ...grpc.CallOption) (*authpb.AuthResponse, error) {
	return nil, nil
}

func (m *mockAuthClient) GenerateSigninCode(ctx context.Context, req *authpb.GenerateSigninCodeRequest, opts ...grpc.CallOption) (*authpb.SigninCodeResponse, error) {
	return nil, nil
}

func TestAuthenticate_MissingAuthorizationHeader(t *testing.T) {
	mockClient := &mockAuthClient{}
	middleware := Authenticate(mockClient)

	handler := middleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		t.Error("Handler should not be called when Authorization header is missing")
	}))

	req := httptest.NewRequest("GET", "/test", nil)
	rr := httptest.NewRecorder()

	handler.ServeHTTP(rr, req)

	if rr.Code != http.StatusUnauthorized {
		t.Errorf("Expected status 401, got %d", rr.Code)
	}
}

func TestAuthenticate_InvalidAuthorizationHeaderFormat(t *testing.T) {
	mockClient := &mockAuthClient{}
	middleware := Authenticate(mockClient)

	handler := middleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		t.Error("Handler should not be called with invalid Authorization header format")
	}))

	req := httptest.NewRequest("GET", "/test", nil)
	req.Header.Set("Authorization", "InvalidFormat")
	rr := httptest.NewRecorder()

	handler.ServeHTTP(rr, req)

	if rr.Code != http.StatusUnauthorized {
		t.Errorf("Expected status 401, got %d", rr.Code)
	}
}

func TestAuthenticate_EmptyToken(t *testing.T) {
	mockClient := &mockAuthClient{}
	middleware := Authenticate(mockClient)

	handler := middleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		t.Error("Handler should not be called with empty token")
	}))

	req := httptest.NewRequest("GET", "/test", nil)
	req.Header.Set("Authorization", "Bearer ")
	rr := httptest.NewRecorder()

	handler.ServeHTTP(rr, req)

	if rr.Code != http.StatusUnauthorized {
		t.Errorf("Expected status 401, got %d", rr.Code)
	}
}

func TestAuthenticate_InvalidToken(t *testing.T) {
	mockClient := &mockAuthClient{
		validateFunc: func(ctx context.Context, req *authpb.ValidateTokenRequest, opts ...grpc.CallOption) (*authpb.ValidateTokenResponse, error) {
			return &authpb.ValidateTokenResponse{Valid: false}, nil
		},
	}
	middleware := Authenticate(mockClient)

	handler := middleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		t.Error("Handler should not be called with invalid token")
	}))

	req := httptest.NewRequest("GET", "/test", nil)
	req.Header.Set("Authorization", "Bearer invalid-token")
	rr := httptest.NewRecorder()

	handler.ServeHTTP(rr, req)

	if rr.Code != http.StatusUnauthorized {
		t.Errorf("Expected status 401, got %d", rr.Code)
	}
}

func TestAuthenticate_ValidToken(t *testing.T) {
	mockClient := &mockAuthClient{
		validateFunc: func(ctx context.Context, req *authpb.ValidateTokenRequest, opts ...grpc.CallOption) (*authpb.ValidateTokenResponse, error) {
			return &authpb.ValidateTokenResponse{
				Valid:     true,
				UserId:    "user-123",
				Role:      "teacher",
				ClassIds:  []string{"class-1", "class-2"},
				TeacherId: "teacher-456",
			}, nil
		},
	}
	middleware := Authenticate(mockClient)

	handlerCalled := false
	handler := middleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		handlerCalled = true

		// Verify user context is set correctly
		userID := GetUserID(r.Context())
		if userID != "user-123" {
			t.Errorf("Expected user_id 'user-123', got '%s'", userID)
		}

		role := GetUserRole(r.Context())
		if role != "teacher" {
			t.Errorf("Expected role 'teacher', got '%s'", role)
		}

		classIDs := GetClassIDs(r.Context())
		if len(classIDs) != 2 || classIDs[0] != "class-1" || classIDs[1] != "class-2" {
			t.Errorf("Expected class_ids ['class-1', 'class-2'], got %v", classIDs)
		}

		teacherID := GetTeacherID(r.Context())
		if teacherID != "teacher-456" {
			t.Errorf("Expected teacher_id 'teacher-456', got '%s'", teacherID)
		}

		w.WriteHeader(http.StatusOK)
	}))

	req := httptest.NewRequest("GET", "/test", nil)
	req.Header.Set("Authorization", "Bearer valid-token")
	rr := httptest.NewRecorder()

	handler.ServeHTTP(rr, req)

	if !handlerCalled {
		t.Error("Handler should be called with valid token")
	}

	if rr.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", rr.Code)
	}
}

func TestGetUserID_NoContext(t *testing.T) {
	ctx := context.Background()
	userID := GetUserID(ctx)
	if userID != "" {
		t.Errorf("Expected empty string, got '%s'", userID)
	}
}

func TestGetUserRole_NoContext(t *testing.T) {
	ctx := context.Background()
	role := GetUserRole(ctx)
	if role != "" {
		t.Errorf("Expected empty string, got '%s'", role)
	}
}

func TestGetClassIDs_NoContext(t *testing.T) {
	ctx := context.Background()
	classIDs := GetClassIDs(ctx)
	if len(classIDs) != 0 {
		t.Errorf("Expected empty slice, got %v", classIDs)
	}
}

func TestGetTeacherID_NoContext(t *testing.T) {
	ctx := context.Background()
	teacherID := GetTeacherID(ctx)
	if teacherID != "" {
		t.Errorf("Expected empty string, got '%s'", teacherID)
	}
}
