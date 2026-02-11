package jwt

import (
	"errors"
	"fmt"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

var (
	// ErrInvalidToken is returned when the token is invalid
	ErrInvalidToken = errors.New("invalid token")
	// ErrExpiredToken is returned when the token has expired
	ErrExpiredToken = errors.New("token has expired")
	// ErrInvalidClaims is returned when the token claims are invalid
	ErrInvalidClaims = errors.New("invalid token claims")
)

// Config holds JWT configuration
type Config struct {
	SecretKey            string        // Secret key for signing tokens
	Issuer               string        // Token issuer
	TeacherTokenDuration time.Duration // Token duration for teachers (default: 24 hours)
	StudentTokenDuration time.Duration // Token duration for students (default: 7 days)
}

// DefaultConfig returns a configuration with sensible defaults
func DefaultConfig() *Config {
	return &Config{
		SecretKey:            "change-me-in-production",
		Issuer:               "metlab.edu",
		TeacherTokenDuration: 24 * time.Hour,
		StudentTokenDuration: 7 * 24 * time.Hour,
	}
}

// Claims represents the JWT claims
type Claims struct {
	UserID    string   `json:"user_id"`
	Role      string   `json:"role"` // "teacher" or "student"
	TeacherID string   `json:"teacher_id,omitempty"`
	ClassIDs  []string `json:"class_ids,omitempty"`
	jwt.RegisteredClaims
}

// TokenManager handles JWT token generation and validation
type TokenManager struct {
	config *Config
}

// NewTokenManager creates a new JWT token manager
func NewTokenManager(cfg *Config) *TokenManager {
	if cfg == nil {
		cfg = DefaultConfig()
	}
	return &TokenManager{
		config: cfg,
	}
}

// GenerateTeacherToken generates a JWT token for a teacher
func (tm *TokenManager) GenerateTeacherToken(userID string, classIDs []string) (string, int64, error) {
	expiresAt := time.Now().Add(tm.config.TeacherTokenDuration)
	
	claims := &Claims{
		UserID:   userID,
		Role:     "teacher",
		ClassIDs: classIDs,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(expiresAt),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
			Issuer:    tm.config.Issuer,
			Subject:   userID,
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	tokenString, err := token.SignedString([]byte(tm.config.SecretKey))
	if err != nil {
		return "", 0, fmt.Errorf("failed to sign token: %w", err)
	}

	return tokenString, expiresAt.Unix(), nil
}

// GenerateStudentToken generates a JWT token for a student
func (tm *TokenManager) GenerateStudentToken(userID, teacherID string, classIDs []string) (string, int64, error) {
	expiresAt := time.Now().Add(tm.config.StudentTokenDuration)
	
	claims := &Claims{
		UserID:    userID,
		Role:      "student",
		TeacherID: teacherID,
		ClassIDs:  classIDs,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(expiresAt),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
			Issuer:    tm.config.Issuer,
			Subject:   userID,
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	tokenString, err := token.SignedString([]byte(tm.config.SecretKey))
	if err != nil {
		return "", 0, fmt.Errorf("failed to sign token: %w", err)
	}

	return tokenString, expiresAt.Unix(), nil
}

// GenerateToken generates a JWT token with custom claims
func (tm *TokenManager) GenerateToken(claims *Claims, duration time.Duration) (string, int64, error) {
	expiresAt := time.Now().Add(duration)
	
	claims.RegisteredClaims = jwt.RegisteredClaims{
		ExpiresAt: jwt.NewNumericDate(expiresAt),
		IssuedAt:  jwt.NewNumericDate(time.Now()),
		Issuer:    tm.config.Issuer,
		Subject:   claims.UserID,
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	tokenString, err := token.SignedString([]byte(tm.config.SecretKey))
	if err != nil {
		return "", 0, fmt.Errorf("failed to sign token: %w", err)
	}

	return tokenString, expiresAt.Unix(), nil
}

// ValidateToken validates a JWT token and returns the claims
func (tm *TokenManager) ValidateToken(tokenString string) (*Claims, error) {
	token, err := jwt.ParseWithClaims(tokenString, &Claims{}, func(token *jwt.Token) (interface{}, error) {
		// Verify signing method
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return []byte(tm.config.SecretKey), nil
	})

	if err != nil {
		if errors.Is(err, jwt.ErrTokenExpired) {
			return nil, ErrExpiredToken
		}
		return nil, fmt.Errorf("%w: %v", ErrInvalidToken, err)
	}

	claims, ok := token.Claims.(*Claims)
	if !ok || !token.Valid {
		return nil, ErrInvalidClaims
	}

	return claims, nil
}

// RefreshToken generates a new token with the same claims but extended expiration
func (tm *TokenManager) RefreshToken(tokenString string) (string, int64, error) {
	claims, err := tm.ValidateToken(tokenString)
	if err != nil {
		// Allow refresh even if token is expired (but not if it's invalid)
		if !errors.Is(err, ErrExpiredToken) {
			return "", 0, err
		}
		
		// Parse the expired token to get claims
		token, parseErr := jwt.ParseWithClaims(tokenString, &Claims{}, func(token *jwt.Token) (interface{}, error) {
			return []byte(tm.config.SecretKey), nil
		})
		if parseErr != nil {
			return "", 0, fmt.Errorf("failed to parse expired token: %w", parseErr)
		}
		
		var ok bool
		claims, ok = token.Claims.(*Claims)
		if !ok {
			return "", 0, ErrInvalidClaims
		}
	}

	// Generate new token with same claims
	var duration time.Duration
	if claims.Role == "teacher" {
		duration = tm.config.TeacherTokenDuration
	} else {
		duration = tm.config.StudentTokenDuration
	}

	return tm.GenerateToken(claims, duration)
}

// ExtractUserID extracts the user ID from a token without full validation
func (tm *TokenManager) ExtractUserID(tokenString string) (string, error) {
	token, _, err := new(jwt.Parser).ParseUnverified(tokenString, &Claims{})
	if err != nil {
		return "", fmt.Errorf("failed to parse token: %w", err)
	}

	claims, ok := token.Claims.(*Claims)
	if !ok {
		return "", ErrInvalidClaims
	}

	return claims.UserID, nil
}

// ExtractRole extracts the role from a token without full validation
func (tm *TokenManager) ExtractRole(tokenString string) (string, error) {
	token, _, err := new(jwt.Parser).ParseUnverified(tokenString, &Claims{})
	if err != nil {
		return "", fmt.Errorf("failed to parse token: %w", err)
	}

	claims, ok := token.Claims.(*Claims)
	if !ok {
		return "", ErrInvalidClaims
	}

	return claims.Role, nil
}
