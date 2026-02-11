package utils

import (
	"fmt"
	"regexp"
	"strings"
)

// emailRegex is a simple regex for basic email validation
// This follows RFC 5322 simplified pattern
var emailRegex = regexp.MustCompile(`^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$`)

// ValidateEmail validates an email address format
func ValidateEmail(email string) error {
	if email == "" {
		return fmt.Errorf("email is required")
	}
	
	// Trim whitespace
	email = strings.TrimSpace(email)
	
	// Check length
	if len(email) > 255 {
		return fmt.Errorf("email must be less than 255 characters")
	}
	
	// Check format
	if !emailRegex.MatchString(email) {
		return fmt.Errorf("invalid email format")
	}
	
	return nil
}
