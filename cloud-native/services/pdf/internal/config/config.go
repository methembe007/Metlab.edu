package config

import (
	"fmt"
	"os"
	"strconv"
)

// Config holds the configuration for the PDF service
type Config struct {
	Port           string
	DatabaseURL    string
	S3Endpoint     string
	S3AccessKey    string
	S3SecretKey    string
	S3Bucket       string
	S3Region       string
	S3UseSSL       bool
	MaxUploadSize  int64
	JWTSecret      string
	Environment    string
}

// LoadConfig loads configuration from environment variables
func LoadConfig() (*Config, error) {
	port := getEnv("PORT", "50056")
	
	// Database configuration
	dbHost := getEnv("DATABASE_HOST", "localhost")
	dbPort := getEnv("DATABASE_PORT", "5432")
	dbUser := getEnv("DATABASE_USER", "postgres")
	dbPassword := getEnv("DATABASE_PASSWORD", "postgres")
	dbName := getEnv("DATABASE_NAME", "metlab")
	dbSSLMode := getEnv("DATABASE_SSL_MODE", "disable")
	
	databaseURL := fmt.Sprintf(
		"postgres://%s:%s@%s:%s/%s?sslmode=%s",
		dbUser, dbPassword, dbHost, dbPort, dbName, dbSSLMode,
	)
	
	// S3 configuration
	s3Endpoint := getEnv("S3_ENDPOINT", "localhost:9000")
	s3AccessKey := getEnv("S3_ACCESS_KEY", "minioadmin")
	s3SecretKey := getEnv("S3_SECRET_KEY", "minioadmin")
	s3Bucket := getEnv("S3_BUCKET", "metlab-pdfs")
	s3Region := getEnv("S3_REGION", "us-east-1")
	s3UseSSL := getEnv("S3_USE_SSL", "false") == "true"
	
	// Upload configuration - 50MB max for PDFs
	maxUploadSizeStr := getEnv("MAX_UPLOAD_SIZE", "52428800") // 50MB default
	maxUploadSize, err := strconv.ParseInt(maxUploadSizeStr, 10, 64)
	if err != nil {
		maxUploadSize = 52428800
	}
	
	// JWT configuration
	jwtSecret := getEnv("JWT_SECRET", "dev-secret-key-change-in-production")
	
	// Environment
	environment := getEnv("ENVIRONMENT", "development")
	
	return &Config{
		Port:          port,
		DatabaseURL:   databaseURL,
		S3Endpoint:    s3Endpoint,
		S3AccessKey:   s3AccessKey,
		S3SecretKey:   s3SecretKey,
		S3Bucket:      s3Bucket,
		S3Region:      s3Region,
		S3UseSSL:      s3UseSSL,
		MaxUploadSize: maxUploadSize,
		JWTSecret:     jwtSecret,
		Environment:   environment,
	}, nil
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
