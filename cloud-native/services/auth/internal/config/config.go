package config

import (
	"fmt"
	"os"
	"strconv"
	"time"
)

// Config holds all configuration for the auth service
type Config struct {
	Port           string
	DatabaseURL    string
	JWTSecret      string
	JWTExpiry      time.Duration
	StudentExpiry  time.Duration
	MaxLoginAttempts int
	LockoutDuration time.Duration
}

// Load reads configuration from environment variables
func Load() (*Config, error) {
	port := getEnv("PORT", "50051")
	
	dbHost := getEnv("DATABASE_HOST", "localhost")
	dbPort := getEnv("DATABASE_PORT", "5432")
	dbUser := getEnv("DATABASE_USER", "postgres")
	dbPassword := getEnv("DATABASE_PASSWORD", "postgres")
	dbName := getEnv("DATABASE_NAME", "metlab")
	
	databaseURL := fmt.Sprintf(
		"postgres://%s:%s@%s:%s/%s?sslmode=disable",
		dbUser, dbPassword, dbHost, dbPort, dbName,
	)
	
	jwtSecret := getEnv("JWT_SECRET", "dev-secret-change-in-production")
	if jwtSecret == "dev-secret-change-in-production" && getEnv("ENV", "development") == "production" {
		return nil, fmt.Errorf("JWT_SECRET must be set in production")
	}
	
	jwtExpiryHours, _ := strconv.Atoi(getEnv("JWT_EXPIRY_HOURS", "24"))
	studentExpiryDays, _ := strconv.Atoi(getEnv("STUDENT_EXPIRY_DAYS", "7"))
	maxLoginAttempts, _ := strconv.Atoi(getEnv("MAX_LOGIN_ATTEMPTS", "5"))
	lockoutMinutes, _ := strconv.Atoi(getEnv("LOCKOUT_MINUTES", "30"))
	
	return &Config{
		Port:             port,
		DatabaseURL:      databaseURL,
		JWTSecret:        jwtSecret,
		JWTExpiry:        time.Duration(jwtExpiryHours) * time.Hour,
		StudentExpiry:    time.Duration(studentExpiryDays) * 24 * time.Hour,
		MaxLoginAttempts: maxLoginAttempts,
		LockoutDuration:  time.Duration(lockoutMinutes) * time.Minute,
	}, nil
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
