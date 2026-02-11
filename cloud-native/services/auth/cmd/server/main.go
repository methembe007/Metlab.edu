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

	"github.com/metlab/auth/internal/config"
	"github.com/metlab/auth/internal/db"
	"github.com/metlab/auth/internal/repository"
	"github.com/metlab/auth/internal/service"
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

	// Initialize database connection
	ctx := context.Background()
	database, err := db.New(ctx, cfg.DatabaseURL)
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer database.Close()

	log.Println("Successfully connected to database")

	// Initialize repositories
	userRepo := repository.NewUserRepository(database.Pool)
	teacherRepo := repository.NewTeacherRepository(database.Pool)
	studentRepo := repository.NewStudentRepository(database.Pool)
	signinCodeRepo := repository.NewSigninCodeRepository(database.Pool)
	loginAttemptRepo := repository.NewLoginAttemptRepository(database.Pool)

	// Initialize service
	authService := service.NewAuthService(
		cfg,
		userRepo,
		teacherRepo,
		studentRepo,
		signinCodeRepo,
		loginAttemptRepo,
	)

	// Create gRPC server
	grpcServer := grpc.NewServer(
		grpc.UnaryInterceptor(loggingInterceptor),
	)

	// Register health check service
	healthServer := health.NewServer()
	grpc_health_v1.RegisterHealthServer(grpcServer, healthServer)
	
	// Set initial health status
	healthServer.SetServingStatus("", grpc_health_v1.HealthCheckResponse_SERVING)
	healthServer.SetServingStatus("auth.AuthService", grpc_health_v1.HealthCheckResponse_SERVING)

	// TODO: Register AuthService gRPC handler when proto is generated
	// pb.RegisterAuthServiceServer(grpcServer, handler.NewAuthHandler(authService))

	// Enable reflection for development
	reflection.Register(grpcServer)

	// Start listening
	lis, err := net.Listen("tcp", fmt.Sprintf(":%s", cfg.Port))
	if err != nil {
		log.Fatalf("Failed to listen: %v", err)
	}

	// Start server in a goroutine
	go func() {
		log.Printf("Auth service starting on port %s", cfg.Port)
		if err := grpcServer.Serve(lis); err != nil {
			log.Fatalf("Failed to serve: %v", err)
		}
	}()

	// Wait for interrupt signal to gracefully shutdown the server
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down server...")

	// Set health status to not serving
	healthServer.SetServingStatus("", grpc_health_v1.HealthCheckResponse_NOT_SERVING)
	healthServer.SetServingStatus("auth.AuthService", grpc_health_v1.HealthCheckResponse_NOT_SERVING)

	// Graceful shutdown
	grpcServer.GracefulStop()
	log.Println("Server stopped")
}

// loggingInterceptor logs all gRPC requests
func loggingInterceptor(
	ctx context.Context,
	req interface{},
	info *grpc.UnaryServerInfo,
	handler grpc.UnaryHandler,
) (interface{}, error) {
	start := time.Now()
	
	// Call the handler
	resp, err := handler(ctx, req)
	
	// Log the request
	duration := time.Since(start)
	if err != nil {
		log.Printf("[ERROR] %s - %v (took %v)", info.FullMethod, err, duration)
	} else {
		log.Printf("[INFO] %s - success (took %v)", info.FullMethod, duration)
	}
	
	return resp, err
}
