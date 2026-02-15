package grpc

import (
	"context"
	"fmt"
	"log"
	"time"

	authpb "github.com/metlab/shared/proto-gen/go/auth"
	videopb "github.com/metlab/shared/proto-gen/go/video"
	homeworkpb "github.com/metlab/shared/proto-gen/go/homework"
	analyticspb "github.com/metlab/shared/proto-gen/go/analytics"
	collaborationpb "github.com/metlab/shared/proto-gen/go/collaboration"
	pdfpb "github.com/metlab/shared/proto-gen/go/pdf"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

// ServiceClients holds all gRPC client connections
type ServiceClients struct {
	Auth          authpb.AuthServiceClient
	Video         videopb.VideoServiceClient
	Homework      homeworkpb.HomeworkServiceClient
	Analytics     analyticspb.AnalyticsServiceClient
	Collaboration collaborationpb.CollaborationServiceClient
	PDF           pdfpb.PDFServiceClient
}

// ClientConfig holds configuration for gRPC clients
type ClientConfig struct {
	AuthServiceAddr          string
	VideoServiceAddr         string
	HomeworkServiceAddr      string
	AnalyticsServiceAddr     string
	CollaborationServiceAddr string
	PDFServiceAddr           string
}

// NewServiceClients creates and initializes all gRPC client connections
func NewServiceClients(ctx context.Context, config ClientConfig) (*ServiceClients, error) {
	clients := &ServiceClients{}

	// Connect to Auth Service
	authConn, err := createConnection(ctx, config.AuthServiceAddr, "Auth")
	if err != nil {
		return nil, err
	}
	clients.Auth = authpb.NewAuthServiceClient(authConn)

	// Connect to Video Service
	videoConn, err := createConnection(ctx, config.VideoServiceAddr, "Video")
	if err != nil {
		return nil, err
	}
	clients.Video = videopb.NewVideoServiceClient(videoConn)

	// Connect to Homework Service
	homeworkConn, err := createConnection(ctx, config.HomeworkServiceAddr, "Homework")
	if err != nil {
		return nil, err
	}
	clients.Homework = homeworkpb.NewHomeworkServiceClient(homeworkConn)

	// Connect to Analytics Service
	analyticsConn, err := createConnection(ctx, config.AnalyticsServiceAddr, "Analytics")
	if err != nil {
		return nil, err
	}
	clients.Analytics = analyticspb.NewAnalyticsServiceClient(analyticsConn)

	// Connect to Collaboration Service
	collaborationConn, err := createConnection(ctx, config.CollaborationServiceAddr, "Collaboration")
	if err != nil {
		return nil, err
	}
	clients.Collaboration = collaborationpb.NewCollaborationServiceClient(collaborationConn)

	// Connect to PDF Service
	pdfConn, err := createConnection(ctx, config.PDFServiceAddr, "PDF")
	if err != nil {
		return nil, err
	}
	clients.PDF = pdfpb.NewPDFServiceClient(pdfConn)

	log.Println("All gRPC client connections established successfully")
	return clients, nil
}

// createConnection creates a gRPC connection with retry logic
func createConnection(ctx context.Context, addr, serviceName string) (*grpc.ClientConn, error) {
	log.Printf("Connecting to %s service at %s", serviceName, addr)

	// Create connection with timeout
	ctx, cancel := context.WithTimeout(ctx, 10*time.Second)
	defer cancel()

	conn, err := grpc.DialContext(
		ctx,
		addr,
		grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithBlock(),
		grpc.WithDefaultCallOptions(
			grpc.MaxCallRecvMsgSize(50*1024*1024), // 50MB for large file transfers
			grpc.MaxCallSendMsgSize(50*1024*1024),
		),
	)

	if err != nil {
		return nil, fmt.Errorf("failed to connect to %s service: %w", serviceName, err)
	}

	log.Printf("Successfully connected to %s service", serviceName)
	return conn, nil
}
