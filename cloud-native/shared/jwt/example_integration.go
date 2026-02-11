package jwt

import (
	"fmt"
	"time"
)

// ExampleUsage demonstrates how to use the JWT package
func ExampleUsage() {
	// Create a token manager with custom configuration
	config := &Config{
		SecretKey:            "your-secret-key-change-in-production",
		Issuer:               "metlab.edu",
		TeacherTokenDuration: 24 * time.Hour,
		StudentTokenDuration: 7 * 24 * time.Hour,
	}
	tm := NewTokenManager(config)

	// Generate a teacher token
	teacherToken, expiresAt, err := tm.GenerateTeacherToken(
		"teacher-123",
		[]string{"class-1", "class-2"},
	)
	if err != nil {
		fmt.Printf("Error generating teacher token: %v\n", err)
		return
	}
	fmt.Printf("Teacher Token: %s\n", teacherToken)
	fmt.Printf("Expires at: %d\n", expiresAt)

	// Validate the token
	claims, err := tm.ValidateToken(teacherToken)
	if err != nil {
		fmt.Printf("Error validating token: %v\n", err)
		return
	}
	fmt.Printf("User ID: %s\n", claims.UserID)
	fmt.Printf("Role: %s\n", claims.Role)
	fmt.Printf("Class IDs: %v\n", claims.ClassIDs)

	// Generate a student token
	studentToken, expiresAt, err := tm.GenerateStudentToken(
		"student-456",
		"teacher-123",
		[]string{"class-1"},
	)
	if err != nil {
		fmt.Printf("Error generating student token: %v\n", err)
		return
	}
	fmt.Printf("Student Token: %s\n", studentToken)
	fmt.Printf("Expires at: %d\n", expiresAt)

	// Validate student token
	studentClaims, err := tm.ValidateToken(studentToken)
	if err != nil {
		fmt.Printf("Error validating student token: %v\n", err)
		return
	}
	fmt.Printf("Student User ID: %s\n", studentClaims.UserID)
	fmt.Printf("Student Role: %s\n", studentClaims.Role)
	fmt.Printf("Student Teacher ID: %s\n", studentClaims.TeacherID)

	// Extract user ID without full validation
	userID, err := tm.ExtractUserID(teacherToken)
	if err != nil {
		fmt.Printf("Error extracting user ID: %v\n", err)
		return
	}
	fmt.Printf("Extracted User ID: %s\n", userID)

	// Refresh token
	newToken, newExpiresAt, err := tm.RefreshToken(teacherToken)
	if err != nil {
		fmt.Printf("Error refreshing token: %v\n", err)
		return
	}
	fmt.Printf("Refreshed Token: %s\n", newToken)
	fmt.Printf("New Expires at: %d\n", newExpiresAt)
}
