package errors

import (
	"errors"
	"fmt"

	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

// Common error types
var (
	// ErrNotFound indicates a resource was not found
	ErrNotFound = errors.New("resource not found")
	// ErrAlreadyExists indicates a resource already exists
	ErrAlreadyExists = errors.New("resource already exists")
	// ErrInvalidArgument indicates an invalid argument was provided
	ErrInvalidArgument = errors.New("invalid argument")
	// ErrUnauthenticated indicates the request lacks valid authentication
	ErrUnauthenticated = errors.New("unauthenticated")
	// ErrPermissionDenied indicates the caller doesn't have permission
	ErrPermissionDenied = errors.New("permission denied")
	// ErrInternal indicates an internal server error
	ErrInternal = errors.New("internal server error")
	// ErrUnavailable indicates the service is unavailable
	ErrUnavailable = errors.New("service unavailable")
	// ErrDeadlineExceeded indicates the deadline was exceeded
	ErrDeadlineExceeded = errors.New("deadline exceeded")
	// ErrResourceExhausted indicates a resource has been exhausted
	ErrResourceExhausted = errors.New("resource exhausted")
	// ErrAborted indicates the operation was aborted
	ErrAborted = errors.New("operation aborted")
	// ErrOutOfRange indicates an operation was attempted past the valid range
	ErrOutOfRange = errors.New("out of range")
	// ErrUnimplemented indicates the operation is not implemented
	ErrUnimplemented = errors.New("unimplemented")
	// ErrDataLoss indicates unrecoverable data loss or corruption
	ErrDataLoss = errors.New("data loss")
)

// AppError represents an application error with additional context
type AppError struct {
	Code    codes.Code         // gRPC status code
	Message string             // Error message
	Details map[string]string  // Additional error details
	Err     error              // Underlying error
}

// Error implements the error interface
func (e *AppError) Error() string {
	if e.Err != nil {
		return fmt.Sprintf("%s: %v", e.Message, e.Err)
	}
	return e.Message
}

// Unwrap returns the underlying error
func (e *AppError) Unwrap() error {
	return e.Err
}

// ToGRPCStatus converts the AppError to a gRPC status
func (e *AppError) ToGRPCStatus() *status.Status {
	return status.New(e.Code, e.Error())
}

// New creates a new AppError
func New(code codes.Code, message string) *AppError {
	return &AppError{
		Code:    code,
		Message: message,
		Details: make(map[string]string),
	}
}

// Wrap wraps an existing error with additional context
func Wrap(err error, code codes.Code, message string) *AppError {
	return &AppError{
		Code:    code,
		Message: message,
		Details: make(map[string]string),
		Err:     err,
	}
}

// WithDetails adds details to an AppError
func (e *AppError) WithDetails(details map[string]string) *AppError {
	for k, v := range details {
		e.Details[k] = v
	}
	return e
}

// WithDetail adds a single detail to an AppError
func (e *AppError) WithDetail(key, value string) *AppError {
	e.Details[key] = value
	return e
}

// NotFound creates a NOT_FOUND error
func NotFound(message string) *AppError {
	return New(codes.NotFound, message)
}

// NotFoundf creates a NOT_FOUND error with formatting
func NotFoundf(format string, args ...interface{}) *AppError {
	return New(codes.NotFound, fmt.Sprintf(format, args...))
}

// AlreadyExists creates an ALREADY_EXISTS error
func AlreadyExists(message string) *AppError {
	return New(codes.AlreadyExists, message)
}

// AlreadyExistsf creates an ALREADY_EXISTS error with formatting
func AlreadyExistsf(format string, args ...interface{}) *AppError {
	return New(codes.AlreadyExists, fmt.Sprintf(format, args...))
}

// InvalidArgument creates an INVALID_ARGUMENT error
func InvalidArgument(message string) *AppError {
	return New(codes.InvalidArgument, message)
}

// InvalidArgumentf creates an INVALID_ARGUMENT error with formatting
func InvalidArgumentf(format string, args ...interface{}) *AppError {
	return New(codes.InvalidArgument, fmt.Sprintf(format, args...))
}

// Unauthenticated creates an UNAUTHENTICATED error
func Unauthenticated(message string) *AppError {
	return New(codes.Unauthenticated, message)
}

// Unauthenticatedf creates an UNAUTHENTICATED error with formatting
func Unauthenticatedf(format string, args ...interface{}) *AppError {
	return New(codes.Unauthenticated, fmt.Sprintf(format, args...))
}

// PermissionDenied creates a PERMISSION_DENIED error
func PermissionDenied(message string) *AppError {
	return New(codes.PermissionDenied, message)
}

// PermissionDeniedf creates a PERMISSION_DENIED error with formatting
func PermissionDeniedf(format string, args ...interface{}) *AppError {
	return New(codes.PermissionDenied, fmt.Sprintf(format, args...))
}

// Internal creates an INTERNAL error
func Internal(message string) *AppError {
	return New(codes.Internal, message)
}

// Internalf creates an INTERNAL error with formatting
func Internalf(format string, args ...interface{}) *AppError {
	return New(codes.Internal, fmt.Sprintf(format, args...))
}

// Unavailable creates an UNAVAILABLE error
func Unavailable(message string) *AppError {
	return New(codes.Unavailable, message)
}

// Unavailablef creates an UNAVAILABLE error with formatting
func Unavailablef(format string, args ...interface{}) *AppError {
	return New(codes.Unavailable, fmt.Sprintf(format, args...))
}

// DeadlineExceeded creates a DEADLINE_EXCEEDED error
func DeadlineExceeded(message string) *AppError {
	return New(codes.DeadlineExceeded, message)
}

// DeadlineExceededf creates a DEADLINE_EXCEEDED error with formatting
func DeadlineExceededf(format string, args ...interface{}) *AppError {
	return New(codes.DeadlineExceeded, fmt.Sprintf(format, args...))
}

// ResourceExhausted creates a RESOURCE_EXHAUSTED error
func ResourceExhausted(message string) *AppError {
	return New(codes.ResourceExhausted, message)
}

// ResourceExhaustedf creates a RESOURCE_EXHAUSTED error with formatting
func ResourceExhaustedf(format string, args ...interface{}) *AppError {
	return New(codes.ResourceExhausted, fmt.Sprintf(format, args...))
}

// Aborted creates an ABORTED error
func Aborted(message string) *AppError {
	return New(codes.Aborted, message)
}

// Abortedf creates an ABORTED error with formatting
func Abortedf(format string, args ...interface{}) *AppError {
	return New(codes.Aborted, fmt.Sprintf(format, args...))
}

// OutOfRange creates an OUT_OF_RANGE error
func OutOfRange(message string) *AppError {
	return New(codes.OutOfRange, message)
}

// OutOfRangef creates an OUT_OF_RANGE error with formatting
func OutOfRangef(format string, args ...interface{}) *AppError {
	return New(codes.OutOfRange, fmt.Sprintf(format, args...))
}

// Unimplemented creates an UNIMPLEMENTED error
func Unimplemented(message string) *AppError {
	return New(codes.Unimplemented, message)
}

// Unimplementedf creates an UNIMPLEMENTED error with formatting
func Unimplementedf(format string, args ...interface{}) *AppError {
	return New(codes.Unimplemented, fmt.Sprintf(format, args...))
}

// DataLoss creates a DATA_LOSS error
func DataLoss(message string) *AppError {
	return New(codes.DataLoss, message)
}

// DataLossf creates a DATA_LOSS error with formatting
func DataLossf(format string, args ...interface{}) *AppError {
	return New(codes.DataLoss, fmt.Sprintf(format, args...))
}

// FromGRPCStatus converts a gRPC status to an AppError
func FromGRPCStatus(st *status.Status) *AppError {
	return &AppError{
		Code:    st.Code(),
		Message: st.Message(),
		Details: make(map[string]string),
	}
}

// ToGRPCError converts an error to a gRPC error
func ToGRPCError(err error) error {
	if err == nil {
		return nil
	}

	// If it's already an AppError, convert it
	var appErr *AppError
	if errors.As(err, &appErr) {
		return appErr.ToGRPCStatus().Err()
	}

	// Check for common error types
	switch {
	case errors.Is(err, ErrNotFound):
		return status.Error(codes.NotFound, err.Error())
	case errors.Is(err, ErrAlreadyExists):
		return status.Error(codes.AlreadyExists, err.Error())
	case errors.Is(err, ErrInvalidArgument):
		return status.Error(codes.InvalidArgument, err.Error())
	case errors.Is(err, ErrUnauthenticated):
		return status.Error(codes.Unauthenticated, err.Error())
	case errors.Is(err, ErrPermissionDenied):
		return status.Error(codes.PermissionDenied, err.Error())
	case errors.Is(err, ErrUnavailable):
		return status.Error(codes.Unavailable, err.Error())
	case errors.Is(err, ErrDeadlineExceeded):
		return status.Error(codes.DeadlineExceeded, err.Error())
	case errors.Is(err, ErrResourceExhausted):
		return status.Error(codes.ResourceExhausted, err.Error())
	case errors.Is(err, ErrAborted):
		return status.Error(codes.Aborted, err.Error())
	case errors.Is(err, ErrOutOfRange):
		return status.Error(codes.OutOfRange, err.Error())
	case errors.Is(err, ErrUnimplemented):
		return status.Error(codes.Unimplemented, err.Error())
	case errors.Is(err, ErrDataLoss):
		return status.Error(codes.DataLoss, err.Error())
	default:
		// Default to internal error
		return status.Error(codes.Internal, err.Error())
	}
}

// FromGRPCError converts a gRPC error to an AppError
func FromGRPCError(err error) *AppError {
	if err == nil {
		return nil
	}

	st, ok := status.FromError(err)
	if !ok {
		return Internal(err.Error())
	}

	return FromGRPCStatus(st)
}

// IsNotFound checks if an error is a NOT_FOUND error
func IsNotFound(err error) bool {
	if err == nil {
		return false
	}
	var appErr *AppError
	if errors.As(err, &appErr) {
		return appErr.Code == codes.NotFound
	}
	return errors.Is(err, ErrNotFound)
}

// IsAlreadyExists checks if an error is an ALREADY_EXISTS error
func IsAlreadyExists(err error) bool {
	if err == nil {
		return false
	}
	var appErr *AppError
	if errors.As(err, &appErr) {
		return appErr.Code == codes.AlreadyExists
	}
	return errors.Is(err, ErrAlreadyExists)
}

// IsInvalidArgument checks if an error is an INVALID_ARGUMENT error
func IsInvalidArgument(err error) bool {
	if err == nil {
		return false
	}
	var appErr *AppError
	if errors.As(err, &appErr) {
		return appErr.Code == codes.InvalidArgument
	}
	return errors.Is(err, ErrInvalidArgument)
}

// IsUnauthenticated checks if an error is an UNAUTHENTICATED error
func IsUnauthenticated(err error) bool {
	if err == nil {
		return false
	}
	var appErr *AppError
	if errors.As(err, &appErr) {
		return appErr.Code == codes.Unauthenticated
	}
	return errors.Is(err, ErrUnauthenticated)
}

// IsPermissionDenied checks if an error is a PERMISSION_DENIED error
func IsPermissionDenied(err error) bool {
	if err == nil {
		return false
	}
	var appErr *AppError
	if errors.As(err, &appErr) {
		return appErr.Code == codes.PermissionDenied
	}
	return errors.Is(err, ErrPermissionDenied)
}

// IsInternal checks if an error is an INTERNAL error
func IsInternal(err error) bool {
	if err == nil {
		return false
	}
	var appErr *AppError
	if errors.As(err, &appErr) {
		return appErr.Code == codes.Internal
	}
	return errors.Is(err, ErrInternal)
}
