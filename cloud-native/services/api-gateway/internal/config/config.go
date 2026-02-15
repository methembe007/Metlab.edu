package config

import (
	"fmt"
	"os"
	"strconv"
)

// Config holds all configuration for the API Gateway
type Config struct {
	Port                     string
	AuthServiceAddr          string
	VideoServiceAddr         string
	HomeworkServiceAddr      string
	AnalyticsServiceAddr     string
	CollaborationServiceAddr string
	PDFServiceAddr           string
	AllowedOrigins           string
	RedisURL                 string
	RateLimitPerMinute       int
}

// Load loads configuration from environment variables
func Load() (*Config, error) {
	rateLimitPerMinute := 100 // default
	if val := os.Getenv("RATE_LIMIT_PER_MINUTE"); val != "" {
		if parsed, err := strconv.Atoi(val); err == nil {
			rateLimitPerMinute = parsed
		}
	}

	config := &Config{
		Port:                     getEnv("PORT", "8080"),
		AuthServiceAddr:          getEnv("AUTH_SERVICE_ADDR", "localhost:50051"),
		VideoServiceAddr:         getEnv("VIDEO_SERVICE_ADDR", "localhost:50052"),
		HomeworkServiceAddr:      getEnv("HOMEWORK_SERVICE_ADDR", "localhost:50053"),
		AnalyticsServiceAddr:     getEnv("ANALYTICS_SERVICE_ADDR", "localhost:50054"),
		CollaborationServiceAddr: getEnv("COLLABORATION_SERVICE_ADDR", "localhost:50055"),
		PDFServiceAddr:           getEnv("PDF_SERVICE_ADDR", "localhost:50056"),
		AllowedOrigins:           getEnv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173"),
		RedisURL:                 getEnv("REDIS_URL", "redis://localhost:6379/0"),
		RateLimitPerMinute:       rateLimitPerMinute,
	}

	// Validate required configuration
	if err := config.Validate(); err != nil {
		return nil, err
	}

	return config, nil
}

// Validate checks if the configuration is valid
func (c *Config) Validate() error {
	if c.Port == "" {
		return fmt.Errorf("PORT is required")
	}

	// Validate service addresses
	services := map[string]string{
		"AUTH_SERVICE_ADDR":          c.AuthServiceAddr,
		"VIDEO_SERVICE_ADDR":         c.VideoServiceAddr,
		"HOMEWORK_SERVICE_ADDR":      c.HomeworkServiceAddr,
		"ANALYTICS_SERVICE_ADDR":     c.AnalyticsServiceAddr,
		"COLLABORATION_SERVICE_ADDR": c.CollaborationServiceAddr,
		"PDF_SERVICE_ADDR":           c.PDFServiceAddr,
	}

	for name, addr := range services {
		if addr == "" {
			return fmt.Errorf("%s is required", name)
		}
	}

	return nil
}

// getEnv gets an environment variable or returns a default value
func getEnv(key, defaultValue string) string {
	value := os.Getenv(key)
	if value == "" {
		return defaultValue
	}
	return value
}
