package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/metlab/analytics/internal/config"
	"github.com/metlab/analytics/internal/db"
	"github.com/metlab/analytics/internal/handler"
	"github.com/metlab/analytics/internal/repository"
	"github.com/metlab/analytics/internal/service"
	pb "metlab/proto-gen/go/analytics"
	"google.golang.org/grpc"
	"google.golang.org/grpc/health"
	"google.golang.org/grpc/health/grpc_health_v1"
	"google.golang.org/grpc/reflection"
)

func main() {
	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	// Create context for initialization
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// Initialize database connection
	database, err := db.New(ctx, cfg.DatabaseURL)
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer database.Close()

	log.Println("Successfully connected to database")

	// Initialize repositories
	loginRepo := repository.NewLoginRepository(database.Pool)
	pdfRepo := repository.NewPDFRepository(database.Pool)
	engagementRepo := repository.NewEngagementRepository(database.Pool)

	// Initialize service
	analyticsService := service.NewAnalyticsService(loginRepo, pdfRepo, engagementRepo)

	// Initialize handler
	analyticsHandler := handler.NewAnalyticsHandler(analyticsService)

	// Create gRPC server
	grpcServer := grpc.NewServer()

	// Register health check service
	healthServer := health.NewServer()
	grpc_health_v1.RegisterHealthServer(grpcServer, healthServer)
	healthServer.SetServingStatus("", grpc_health_v1.HealthCheckResponse_SERVING)

	// Register analytics service
	pb.RegisterAnalyticsServiceServer(grpcServer, analyticsHandler)

	// Register reflection service for debugging
	reflection.Register(grpcServer)

	// Start listening
	lis, err := net.Listen("tcp", fmt.Sprintf(":%s", cfg.Port))
	if err != nil {
		log.Fatalf("Failed to listen: %v", err)
	}

	// Handle graceful shutdown
	go func() {
		sigChan := make(chan os.Signal, 1)
		signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)
		<-sigChan

		log.Println("Shutting down gracefully...")
		healthServer.SetServingStatus("", grpc_health_v1.HealthCheckResponse_NOT_SERVING)
		grpcServer.GracefulStop()
	}()

	log.Printf("Analytics service starting on port %s", cfg.Port)
	if err := grpcServer.Serve(lis); err != nil {
		log.Fatalf("Failed to serve: %v", err)
	}
}