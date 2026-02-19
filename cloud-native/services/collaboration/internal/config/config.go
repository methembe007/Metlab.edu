package config

import (
	"fmt"
	"os"
	"strconv"
)

// Config holds all configuration for the collaboration service
type Config struct {
	Port        string
	DatabaseURL string
	RedisURL    string
	S3Endpoint  string
	S3Bucket    string
	S3AccessKey string
	S3SecretKey string
	MaxGroupMembers int
	MaxGroupsPerStudent int
	MessageRetentionDays int
	MaxMessageLength int
	MaxImageSize int64
}

// Load reads configuration from environment variables
func Load() (*Config, error) {
	port := getEnv("PORT", "50055")
	
	// Database configuration
	dbHost := getEnv("DATABASE_HOST", "localhost")
	dbPort := getEnv("DATABASE_PORT", "5432")
	dbUser := getEnv("DATABASE_USER", "postgres")
	dbPassword := getEnv("DATABASE_PASSWORD", "postgres")
	dbName := getEnv("DATABASE_NAME", "metlab")
	
	databaseURL := fmt.Sprintf(
		"postgres://%s:%s@%s:%s/%s?sslmode=disable",
		dbUser, dbPassword, dbHost, dbPort, dbName,
	)
	
	// Redis configuration
	redisHost := getEnv("REDIS_HOST", "localhost")
	redisPort := getEnv("REDIS_PORT", "6379")
	redisPassword := getEnv("REDIS_PASSWORD", "")
	redisDB := getEnv("REDIS_DB", "0")
	
	redisURL := fmt.Sprintf("redis://:%s@%s:%s/%s", redisPassword, redisHost, redisPort, redisDB)
	if redisPassword == "" {
		redisURL = fmt.Sprintf("redis://%s:%s/%s", redisHost, redisPort, redisDB)
	}
	
	// S3 configuration
	s3Endpoint := getEnv("S3_ENDPOINT", "localhost:9000")
	s3Bucket := getEnv("S3_BUCKET", "metlab-chat-images")
	s3AccessKey := getEnv("S3_ACCESS_KEY", "minioadmin")
	s3SecretKey := getEnv("S3_SECRET_KEY", "minioadmin")
	
	// Business rules configuration
	maxGroupMembers, _ := strconv.Atoi(getEnv("MAX_GROUP_MEMBERS", "10"))
	maxGroupsPerStudent, _ := strconv.Atoi(getEnv("MAX_GROUPS_PER_STUDENT", "5"))
	messageRetentionDays, _ := strconv.Atoi(getEnv("MESSAGE_RETENTION_DAYS", "7"))
	maxMessageLength, _ := strconv.Atoi(getEnv("MAX_MESSAGE_LENGTH", "1000"))
	maxImageSizeMB, _ := strconv.Atoi(getEnv("MAX_IMAGE_SIZE_MB", "5"))
	
	return &Config{
		Port:                 port,
		DatabaseURL:          databaseURL,
		RedisURL:             redisURL,
		S3Endpoint:           s3Endpoint,
		S3Bucket:             s3Bucket,
		S3AccessKey:          s3AccessKey,
		S3SecretKey:          s3SecretKey,
		MaxGroupMembers:      maxGroupMembers,
		MaxGroupsPerStudent:  maxGroupsPerStudent,
		MessageRetentionDays: messageRetentionDays,
		MaxMessageLength:     maxMessageLength,
		MaxImageSize:         int64(maxImageSizeMB) * 1024 * 1024,
	}, nil
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
