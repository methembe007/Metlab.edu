package handlers

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/metlab/api-gateway/internal/grpc"
	authpb "github.com/metlab/shared/proto-gen/go/auth"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

// MockAuthServiceClient is a mock implementation of AuthServiceClient
type MockAuthServiceClient struct {
	mock.Mock
}

func (m *MockAuthServiceClient) TeacherSignup(ctx context.Context, req *authpb.TeacherSignupRequest, opts ...interface{}) (*authpb.AuthResponse, error) {
	args := m.Called(ctx, req)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*authpb.AuthResponse), args.Error(1)
}

func (m *MockAuthServiceClient) TeacherLogin(ctx context.Context, req *authpb.LoginRequest, opts ...interface{}) (*authpb.AuthResponse, error) {
	args := m.Called(ctx, req)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*authpb.AuthResponse), args.Error(1)
}

func (m *MockAuthServiceClient) StudentSignin(ctx context.Context, req *authpb.StudentSigninRequest, opts ...interface{}) (*authpb.AuthResponse, error) {
	args := m.Called(ctx, req)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*authpb.AuthResponse), args.Error(1)
}

func (m *MockAuthServiceClient) ValidateToken(ctx context.Context, req *authpb.ValidateTokenRequest, opts ...interface{}) (*authpb.ValidateTokenResponse, error) {
	args := m.Called(ctx, req)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*authpb.ValidateTokenResponse), args.Error(1)
}

func (m *MockAuthServiceClient) GenerateSigninCode(ctx context.Context, req *authpb.GenerateSigninCodeRequest, opts ...interface{}) (*authpb.SigninCodeResponse, error) {
	args := m.Called(ctx, req)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*authpb.SigninCodeResponse), args.Error(1)
}

func TestTeacherSignup(t *testing.T) {
	tests := []struct {
		name           string
		requestBody    interface{}
		mockResponse   *authpb.AuthResponse
		mockError      error
		expectedStatus int
	}{
		{
			name: "successful signup",
			requestBody: TeacherSignupRequest{
				Email:       "teacher@example.com",
				Password:    "SecurePass123!",
				FullName:    "John Doe",
				SubjectArea: "Mathematics",
			},
			mockResponse: &authpb.AuthResponse{
				Token:     "mock-jwt-token",
				UserId:    "user-123",
				Role:      "teacher",
				ExpiresAt: 1234567890,
			},
			mockError:      nil,
			expectedStatus: http.StatusCreated,
		},
		{
			name: "missing email",
			requestBody: TeacherSignupRequest{
				Password:    "SecurePass123!",
				FullName:    "John Doe",
				SubjectArea: "Mathematics",
			},
			mockResponse:   nil,
			mockError:      nil,
			expectedStatus: http.StatusBadRequest,
		},
		{
			name: "invalid email",
			requestBody: TeacherSignupRequest{
				Email:       "invalid-email",
				Password:    "SecurePass123!",
				FullName:    "John Doe",
				SubjectArea: "Mathematics",
			},
			mockResponse:   nil,
			mockError:      nil,
			expectedStatus: http.StatusBadRequest,
		},
		{
			name: "password too short",
			requestBody: TeacherSignupRequest{
				Email:       "teacher@example.com",
				Password:    "short",
				FullName:    "John Doe",
				SubjectArea: "Mathematics",
			},
			mockResponse:   nil,
			mockError:      nil,
			expectedStatus: http.StatusBadRequest,
		},
		{
			name: "missing full name",
			requestBody: TeacherSignupRequest{
				Email:       "teacher@example.com",
				Password:    "SecurePass123!",
				SubjectArea: "Mathematics",
			},
			mockResponse:   nil,
			mockError:      nil,
			expectedStatus: http.StatusBadRequest,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create mock client
			mockAuthClient := new(MockAuthServiceClient)
			
			// Set up expectations only for valid requests
			if tt.expectedStatus == http.StatusCreated {
				mockAuthClient.On("TeacherSignup", mock.Anything, mock.Anything).
					Return(tt.mockResponse, tt.mockError)
			}

			// Create handler with mock client
			handler := &Handler{
				clients: &grpc.ServiceClients{
					Auth: mockAuthClient,
				},
			}

			// Create request
			body, _ := json.Marshal(tt.requestBody)
			req := httptest.NewRequest(http.MethodPost, "/api/auth/teacher/signup", bytes.NewReader(body))
			req.Header.Set("Content-Type", "application/json")
			w := httptest.NewRecorder()

			// Call handler
			handler.TeacherSignup(w, req)

			// Assert status code
			assert.Equal(t, tt.expectedStatus, w.Code)

			// For successful requests, verify response body
			if tt.expectedStatus == http.StatusCreated {
				var response AuthResponse
				err := json.NewDecoder(w.Body).Decode(&response)
				assert.NoError(t, err)
				assert.Equal(t, tt.mockResponse.Token, response.Token)
				assert.Equal(t, tt.mockResponse.UserId, response.UserID)
				assert.Equal(t, tt.mockResponse.Role, response.Role)
			}

			// Verify mock expectations
			if tt.expectedStatus == http.StatusCreated {
				mockAuthClient.AssertExpectations(t)
			}
		})
	}
}

func TestTeacherLogin(t *testing.T) {
	tests := []struct {
		name           string
		requestBody    interface{}
		mockResponse   *authpb.AuthResponse
		mockError      error
		expectedStatus int
	}{
		{
			name: "successful login",
			requestBody: TeacherLoginRequest{
				Email:    "teacher@example.com",
				Password: "SecurePass123!",
			},
			mockResponse: &authpb.AuthResponse{
				Token:     "mock-jwt-token",
				UserId:    "user-123",
				Role:      "teacher",
				ExpiresAt: 1234567890,
			},
			mockError:      nil,
			expectedStatus: http.StatusOK,
		},
		{
			name: "missing email",
			requestBody: TeacherLoginRequest{
				Password: "SecurePass123!",
			},
			mockResponse:   nil,
			mockError:      nil,
			expectedStatus: http.StatusBadRequest,
		},
		{
			name: "missing password",
			requestBody: TeacherLoginRequest{
				Email: "teacher@example.com",
			},
			mockResponse:   nil,
			mockError:      nil,
			expectedStatus: http.StatusBadRequest,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create mock client
			mockAuthClient := new(MockAuthServiceClient)
			
			// Set up expectations only for valid requests
			if tt.expectedStatus == http.StatusOK {
				mockAuthClient.On("TeacherLogin", mock.Anything, mock.Anything).
					Return(tt.mockResponse, tt.mockError)
			}

			// Create handler with mock client
			handler := &Handler{
				clients: &grpc.ServiceClients{
					Auth: mockAuthClient,
				},
			}

			// Create request
			body, _ := json.Marshal(tt.requestBody)
			req := httptest.NewRequest(http.MethodPost, "/api/auth/teacher/login", bytes.NewReader(body))
			req.Header.Set("Content-Type", "application/json")
			w := httptest.NewRecorder()

			// Call handler
			handler.TeacherLogin(w, req)

			// Assert status code
			assert.Equal(t, tt.expectedStatus, w.Code)

			// Verify mock expectations
			if tt.expectedStatus == http.StatusOK {
				mockAuthClient.AssertExpectations(t)
			}
		})
	}
}

func TestStudentSignin(t *testing.T) {
	tests := []struct {
		name           string
		requestBody    interface{}
		mockResponse   *authpb.AuthResponse
		mockError      error
		expectedStatus int
	}{
		{
			name: "successful signin",
			requestBody: StudentSigninRequest{
				TeacherName: "John Doe",
				StudentName: "Jane Smith",
				SigninCode:  "ABC12345",
			},
			mockResponse: &authpb.AuthResponse{
				Token:     "mock-jwt-token",
				UserId:    "student-123",
				Role:      "student",
				ExpiresAt: 1234567890,
			},
			mockError:      nil,
			expectedStatus: http.StatusOK,
		},
		{
			name: "missing teacher name",
			requestBody: StudentSigninRequest{
				StudentName: "Jane Smith",
				SigninCode:  "ABC12345",
			},
			mockResponse:   nil,
			mockError:      nil,
			expectedStatus: http.StatusBadRequest,
		},
		{
			name: "missing student name",
			requestBody: StudentSigninRequest{
				TeacherName: "John Doe",
				SigninCode:  "ABC12345",
			},
			mockResponse:   nil,
			mockError:      nil,
			expectedStatus: http.StatusBadRequest,
		},
		{
			name: "missing signin code",
			requestBody: StudentSigninRequest{
				TeacherName: "John Doe",
				StudentName: "Jane Smith",
			},
			mockResponse:   nil,
			mockError:      nil,
			expectedStatus: http.StatusBadRequest,
		},
		{
			name: "invalid signin code length",
			requestBody: StudentSigninRequest{
				TeacherName: "John Doe",
				StudentName: "Jane Smith",
				SigninCode:  "ABC",
			},
			mockResponse:   nil,
			mockError:      nil,
			expectedStatus: http.StatusBadRequest,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create mock client
			mockAuthClient := new(MockAuthServiceClient)
			
			// Set up expectations only for valid requests
			if tt.expectedStatus == http.StatusOK {
				mockAuthClient.On("StudentSignin", mock.Anything, mock.Anything).
					Return(tt.mockResponse, tt.mockError)
			}

			// Create handler with mock client
			handler := &Handler{
				clients: &grpc.ServiceClients{
					Auth: mockAuthClient,
				},
			}

			// Create request
			body, _ := json.Marshal(tt.requestBody)
			req := httptest.NewRequest(http.MethodPost, "/api/auth/student/signin", bytes.NewReader(body))
			req.Header.Set("Content-Type", "application/json")
			w := httptest.NewRecorder()

			// Call handler
			handler.StudentSignin(w, req)

			// Assert status code
			assert.Equal(t, tt.expectedStatus, w.Code)

			// Verify mock expectations
			if tt.expectedStatus == http.StatusOK {
				mockAuthClient.AssertExpectations(t)
			}
		})
	}
}

func TestGenerateSigninCode(t *testing.T) {
	tests := []struct {
		name           string
		requestBody    interface{}
		mockResponse   *authpb.SigninCodeResponse
		mockError      error
		expectedStatus int
	}{
		{
			name: "successful code generation",
			requestBody: GenerateSigninCodeRequest{
				TeacherID: "teacher-123",
				ClassID:   "class-456",
			},
			mockResponse: &authpb.SigninCodeResponse{
				Code:      "ABC12345",
				ExpiresAt: 1234567890,
			},
			mockError:      nil,
			expectedStatus: http.StatusCreated,
		},
		{
			name: "missing teacher id",
			requestBody: GenerateSigninCodeRequest{
				ClassID: "class-456",
			},
			mockResponse:   nil,
			mockError:      nil,
			expectedStatus: http.StatusBadRequest,
		},
		{
			name: "missing class id",
			requestBody: GenerateSigninCodeRequest{
				TeacherID: "teacher-123",
			},
			mockResponse:   nil,
			mockError:      nil,
			expectedStatus: http.StatusBadRequest,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create mock client
			mockAuthClient := new(MockAuthServiceClient)
			
			// Set up expectations only for valid requests
			if tt.expectedStatus == http.StatusCreated {
				mockAuthClient.On("GenerateSigninCode", mock.Anything, mock.Anything).
					Return(tt.mockResponse, tt.mockError)
			}

			// Create handler with mock client
			handler := &Handler{
				clients: &grpc.ServiceClients{
					Auth: mockAuthClient,
				},
			}

			// Create request
			body, _ := json.Marshal(tt.requestBody)
			req := httptest.NewRequest(http.MethodPost, "/api/auth/codes/generate", bytes.NewReader(body))
			req.Header.Set("Content-Type", "application/json")
			w := httptest.NewRecorder()

			// Call handler
			handler.GenerateSigninCode(w, req)

			// Assert status code
			assert.Equal(t, tt.expectedStatus, w.Code)

			// For successful requests, verify response body
			if tt.expectedStatus == http.StatusCreated {
				var response SigninCodeResponse
				err := json.NewDecoder(w.Body).Decode(&response)
				assert.NoError(t, err)
				assert.Equal(t, tt.mockResponse.Code, response.Code)
				assert.Equal(t, tt.mockResponse.ExpiresAt, response.ExpiresAt)
			}

			// Verify mock expectations
			if tt.expectedStatus == http.StatusCreated {
				mockAuthClient.AssertExpectations(t)
			}
		})
	}
}

func TestValidationFunctions(t *testing.T) {
	t.Run("isValidEmail", func(t *testing.T) {
		tests := []struct {
			email string
			valid bool
		}{
			{"test@example.com", true},
			{"user.name@domain.co.uk", true},
			{"invalid", false},
			{"@example.com", false},
			{"test@", false},
			{"test@domain", false},
			{"", false},
		}

		for _, tt := range tests {
			result := isValidEmail(tt.email)
			assert.Equal(t, tt.valid, result, "Email: %s", tt.email)
		}
	})
}

