package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/metlab/api-gateway/internal/config"
	"github.com/metlab/api-gateway/internal/grpc"
	"github.com/metlab/api-gateway/internal/handlers"
	"github.com/metlab/api-gateway/internal/router"
	"github.com/metlab/shared/cache"
)

func main() {
	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	log.Println("Starting API Gateway...")
	log.Printf("Configuration loaded: Port=%s", cfg.Port)

	// Create context for graceful shutdown
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Initialize Redis client for rate limiting
	var redisClient *cache.RedisClient
	log.Printf("Connecting to Redis at %s...", cfg.RedisURL)
	redisClient, err = cache.NewRedisClientFromURL(ctx, cfg.RedisURL)
	if err != nil {
		log.Printf("Warning: Failed to connect to Redis: %v", err)
		log.Println("Rate limiting will use in-memory storage only")
	} else {
		log.Println("Redis connection established successfully")
		defer redisClient.Close()
	}

	// Initialize gRPC clients
	log.Println("Initializing gRPC client connections...")
	clients, err := grpc.NewServiceClients(ctx, grpc.ClientConfig{
		AuthServiceAddr:          cfg.AuthServiceAddr,
		VideoServiceAddr:         cfg.VideoServiceAddr,
		HomeworkServiceAddr:      cfg.HomeworkServiceAddr,
		AnalyticsServiceAddr:     cfg.AnalyticsServiceAddr,
		CollaborationServiceAddr: cfg.CollaborationServiceAddr,
		PDFServiceAddr:           cfg.PDFServiceAddr,
	})

	if err != nil {
		log.Printf("Warning: Failed to initialize gRPC clients: %v", err)
		log.Println("API Gateway will start but some endpoints may not work")
		// Continue anyway for development - services might not be running yet
	} else {
		log.Println("All gRPC client connections established successfully")
	}

	// Create handlers
	handler := handlers.NewHandler(clients)

	// Create router with rate limiting
	var redisClientForRouter *cache.RedisClient
	if redisClient != nil {
		redisClientForRouter = redisClient
	}
	r := router.NewRouter(handler, &router.RouterConfig{
		RedisClient:        redisClientForRouter,
		RateLimitPerMinute: cfg.RateLimitPerMinute,
	})

	// Create HTTP server
	addr := fmt.Sprintf(":%s", cfg.Port)
	server := &http.Server{
		Addr:         addr,
		Handler:      r,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Start server in a goroutine
	go func() {
		log.Printf("API Gateway listening on %s", addr)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Failed to start server: %v", err)
		}
	}()

	// Wait for interrupt signal for graceful shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down API Gateway...")

	// Graceful shutdown with timeout
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer shutdownCancel()

	if err := server.Shutdown(shutdownCtx); err != nil {
		log.Fatalf("Server forced to shutdown: %v", err)
	}

	log.Println("API Gateway stopped")
}
