package middleware

import (
	"context"
	"log"
	"net/http"
	"strings"
	"time"

	authpb "github.com/metlab/shared/proto-gen/go/auth"
)

// Context keys for user information
type userContextKey string

const (
	UserIDKey     userContextKey = "user_id"
	UserRoleKey   userContextKey = "user_role"
	ClassIDsKey   userContextKey = "class_ids"
	TeacherIDKey  userContextKey = "teacher_id"
)

// Authenticate creates an authentication middleware that validates JWT tokens
func Authenticate(authClient authpb.AuthServiceClient) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Extract token from Authorization header
			authHeader := r.Header.Get("Authorization")
			if authHeader == "" {
				log.Printf("Authentication failed: missing Authorization header")
				respondWithError(w, http.StatusUnauthorized, "missing authorization header")
				return
			}

			// Check for Bearer token format
			parts := strings.SplitN(authHeader, " ", 2)
			if len(parts) != 2 || strings.ToLower(parts[0]) != "bearer" {
				log.Printf("Authentication failed: invalid Authorization header format")
				respondWithError(w, http.StatusUnauthorized, "invalid authorization header format")
				return
			}

			token := parts[1]
			if token == "" {
				log.Printf("Authentication failed: empty token")
				respondWithError(w, http.StatusUnauthorized, "empty token")
				return
			}

			// Call Auth service to validate token
			ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
			defer cancel()

			validateResp, err := authClient.ValidateToken(ctx, &authpb.ValidateTokenRequest{
				Token: token,
			})

			if err != nil {
				log.Printf("Authentication failed: error validating token: %v", err)
				respondWithError(w, http.StatusUnauthorized, "invalid or expired token")
				return
			}

			// Check if token is valid
			if !validateResp.Valid {
				log.Printf("Authentication failed: token validation returned invalid")
				respondWithError(w, http.StatusUnauthorized, "invalid or expired token")
				return
			}

			// Add user information to request context
			ctx = context.WithValue(r.Context(), UserIDKey, validateResp.UserId)
			ctx = context.WithValue(ctx, UserRoleKey, validateResp.Role)
			ctx = context.WithValue(ctx, ClassIDsKey, validateResp.ClassIds)
			ctx = context.WithValue(ctx, TeacherIDKey, validateResp.TeacherId)

			log.Printf("Authentication successful: user_id=%s, role=%s", validateResp.UserId, validateResp.Role)

			// Continue to next handler with enriched context
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

// GetUserID retrieves the user ID from the request context
func GetUserID(ctx context.Context) string {
	if userID, ok := ctx.Value(UserIDKey).(string); ok {
		return userID
	}
	return ""
}

// GetUserRole retrieves the user role from the request context
func GetUserRole(ctx context.Context) string {
	if role, ok := ctx.Value(UserRoleKey).(string); ok {
		return role
	}
	return ""
}

// GetClassIDs retrieves the class IDs from the request context
func GetClassIDs(ctx context.Context) []string {
	if classIDs, ok := ctx.Value(ClassIDsKey).([]string); ok {
		return classIDs
	}
	return []string{}
}

// GetTeacherID retrieves the teacher ID from the request context
func GetTeacherID(ctx context.Context) string {
	if teacherID, ok := ctx.Value(TeacherIDKey).(string); ok {
		return teacherID
	}
	return ""
}

// respondWithError sends a JSON error response
func respondWithError(w http.ResponseWriter, statusCode int, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)
	w.Write([]byte(`{"error":"` + message + `"}`))
}
