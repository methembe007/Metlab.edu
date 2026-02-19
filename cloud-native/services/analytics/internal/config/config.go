package config

import (
	"fmt"
	"os"
)

// Config holds all configuration for the analytics service
type Config struct {
	Port        string
	DatabaseURL string
}

// Load reads configuration from environment variables
func Load() (*Config, error) {
	port := getEnv("PORT", "50054")

	dbHost := getEnv("DATABASE_HOST", "localhost")
	dbPort := getEnv("DATABASE_PORT", "5432")
	dbUser := getEnv("DATABASE_USER", "postgres")
	dbPassword := getEnv("DATABASE_PASSWORD", "postgres")
	dbName := getEnv("DATABASE_NAME", "metlab")

	databaseURL := fmt.Sprintf(
		"postgres://%s:%s@%s:%s/%s?sslmode=disable",
		dbUser, dbPassword, dbHost, dbPort, dbName,
	)

	return &Config{
		Port:        port,
		DatabaseURL: databaseURL,
	}, nil
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
