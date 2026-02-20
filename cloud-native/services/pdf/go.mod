module github.com/metlab/pdf

go 1.24.0

replace github.com/metlab/shared => ../../shared

replace metlab/proto-gen => ../../shared/proto-gen

require (
	github.com/google/uuid v1.6.0
	github.com/jackc/pgx/v5 v5.5.1
	github.com/metlab/shared v0.0.0
	google.golang.org/grpc v1.79.1
	metlab/proto-gen v0.0.0
)

require (
	github.com/aws/aws-sdk-go v1.49.21 // indirect
	github.com/jackc/pgpassfile v1.0.0 // indirect
	github.com/jackc/pgservicefile v0.0.0-20231201235250-de7065d80cb9 // indirect
	github.com/jackc/puddle/v2 v2.2.1 // indirect
	github.com/jmespath/go-jmespath v0.4.0 // indirect
	golang.org/x/crypto v0.48.0 // indirect
	golang.org/x/net v0.50.0 // indirect
	golang.org/x/sync v0.19.0 // indirect
	golang.org/x/sys v0.41.0 // indirect
	golang.org/x/text v0.34.0 // indirect
	google.golang.org/genproto/googleapis/rpc v0.0.0-20260209200024-4cfbd4190f57 // indirect
	google.golang.org/protobuf v1.36.11 // indirect
)
