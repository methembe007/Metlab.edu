package errors

import (
	"context"
	"fmt"

	"google.golang.org/grpc/codes"
)

// ExampleUsage demonstrates how to use the errors package
func ExampleUsage() {
	// Create simple errors
	err1 := NotFound("user not found")
	fmt.Printf("Error: %v\n", err1)

	// Create errors with formatting
	userID := "user-123"
	err2 := NotFoundf("user with id %s not found", userID)
	fmt.Printf("Error: %v\n", err2)

	// Create errors with details
	err3 := InvalidArgument("invalid email").
		WithDetail("field", "email").
		WithDetail("reason", "invalid format")
	fmt.Printf("Error: %v\nDetails: %v\n", err3, err3.Details)

	// Add multiple details
	err4 := InvalidArgument("validation failed").
		WithDetails(map[string]string{
			"field":    "password",
			"reason":   "too short",
			"min_length": "12",
		})
	fmt.Printf("Error: %v\nDetails: %v\n", err4, err4.Details)

	// Wrap an existing error
	originalErr := fmt.Errorf("connection refused")
	err5 := Wrap(originalErr, codes.Internal, "failed to connect to database")
	fmt.Printf("Error: %v\n", err5)

	// Convert to gRPC error
	grpcErr := err3.ToGRPCStatus().Err()
	fmt.Printf("gRPC Error: %v\n", grpcErr)

	// Check error types
	if IsNotFound(err1) {
		fmt.Println("Error is NotFound")
	}

	if IsInvalidArgument(err3) {
		fmt.Println("Error is InvalidArgument")
	}
}

// ExampleGRPCService demonstrates error handling in a gRPC service
func ExampleGRPCService() {
	// Simulate a gRPC service method
	userID := "user-123"
	
	// Example 1: Resource not found
	user, err := findUser(userID)
	if err != nil {
		// Return gRPC error
		grpcErr := NotFoundf("user with id %s not found", userID).
			WithDetail("user_id", userID).
			ToGRPCStatus().Err()
		fmt.Printf("gRPC Error: %v\n", grpcErr)
		return
	}
	fmt.Printf("User found: %v\n", user)

	// Example 2: Validation error
	email := "invalid-email"
	if !isValidEmail(email) {
		grpcErr := InvalidArgument("invalid email format").
			WithDetail("field", "email").
			WithDetail("value", email).
			ToGRPCStatus().Err()
		fmt.Printf("gRPC Error: %v\n", grpcErr)
		return
	}

	// Example 3: Permission denied
	if !hasPermission(userID, "delete_user") {
		grpcErr := PermissionDenied("insufficient permissions").
			WithDetail("user_id", userID).
			WithDetail("required_permission", "delete_user").
			ToGRPCStatus().Err()
		fmt.Printf("gRPC Error: %v\n", grpcErr)
		return
	}

	// Example 4: Internal error with wrapped error
	originalErr := fmt.Errorf("database connection failed")
	grpcErr := Wrap(originalErr, codes.Internal, "failed to process request").
		ToGRPCStatus().Err()
	fmt.Printf("gRPC Error: %v\n", grpcErr)
}

// ExampleGRPCClient demonstrates error handling in a gRPC client
func ExampleGRPCClient() {
	// Simulate receiving a gRPC error from a service call
	grpcErr := NotFound("user not found").ToGRPCStatus().Err()
	
	// Convert gRPC error to AppError
	appErr := FromGRPCError(grpcErr)
	
	// Check error type and handle accordingly
	if appErr.Code == codes.NotFound {
		fmt.Println("User not found, creating new user...")
	} else if appErr.Code == codes.InvalidArgument {
		fmt.Println("Invalid input, please check your data")
	} else {
		fmt.Printf("Unexpected error: %v\n", appErr)
	}
}

// ExampleHTTPHandler demonstrates error handling in an HTTP handler
func ExampleHTTPHandler() {
	// Simulate an HTTP handler
	userID := "user-123"
	
	// Call a service that returns an error
	err := deleteUser(userID)
	if err != nil {
		// Convert to AppError if needed
		appErr := FromGRPCError(err)
		
		// Map to HTTP status code
		var statusCode int
		switch appErr.Code {
		case codes.NotFound:
			statusCode = 404
		case codes.InvalidArgument:
			statusCode = 400
		case codes.Unauthenticated:
			statusCode = 401
		case codes.PermissionDenied:
			statusCode = 403
		case codes.AlreadyExists:
			statusCode = 409
		case codes.ResourceExhausted:
			statusCode = 429
		default:
			statusCode = 500
		}
		
		fmt.Printf("HTTP Status: %d\n", statusCode)
		fmt.Printf("Error: %v\n", appErr.Message)
		fmt.Printf("Details: %v\n", appErr.Details)
	}
}

// ExampleDatabaseErrors demonstrates handling database errors
func ExampleDatabaseErrors() {
	ctx := context.Background()
	email := "user@example.com"
	
	// Simulate database operation
	err := insertUser(ctx, email)
	if err != nil {
		// Check if it's a duplicate key error
		if isDuplicateKeyError(err) {
			appErr := AlreadyExists("user with this email already exists").
				WithDetail("email", email)
			fmt.Printf("Error: %v\n", appErr)
			return
		}
		
		// Wrap other database errors
		appErr := Wrap(err, codes.Internal, "failed to create user")
		fmt.Printf("Error: %v\n", appErr)
	}
}

// ExampleAuthenticationErrors demonstrates handling authentication errors
func ExampleAuthenticationErrors() {
	token := "invalid-token"
	
	// Validate token
	claims, err := validateToken(token)
	if err != nil {
		if isExpiredTokenError(err) {
			appErr := Unauthenticated("token has expired").
				WithDetail("token", token)
			fmt.Printf("Error: %v\n", appErr)
			return
		}
		
		appErr := Unauthenticated("invalid token").
			WithDetail("token", token)
		fmt.Printf("Error: %v\n", appErr)
		return
	}
	
	fmt.Printf("Claims: %v\n", claims)
}

// Helper functions for examples (not actual implementations)
func findUser(userID string) (interface{}, error) {
	return nil, fmt.Errorf("not found")
}

func isValidEmail(email string) bool {
	return false
}

func hasPermission(userID, permission string) bool {
	return false
}

func deleteUser(userID string) error {
	return NotFound("user not found").ToGRPCStatus().Err()
}

func insertUser(ctx context.Context, email string) error {
	return fmt.Errorf("duplicate key")
}

func isDuplicateKeyError(err error) bool {
	return true
}

func validateToken(token string) (interface{}, error) {
	return nil, fmt.Errorf("expired")
}

func isExpiredTokenError(err error) bool {
	return true
}
