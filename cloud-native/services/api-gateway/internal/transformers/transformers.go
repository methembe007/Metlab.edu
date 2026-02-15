package transformers

import (
	"encoding/json"
	"io"
	"net/http"

	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

// ErrorResponse represents a standard error response
type ErrorResponse struct {
	Error ErrorDetail `json:"error"`
}

// ErrorDetail contains error information
type ErrorDetail struct {
	Code    string                 `json:"code"`
	Message string                 `json:"message"`
	Details map[string]interface{} `json:"details,omitempty"`
}

// DecodeJSONRequest decodes a JSON request body into the provided struct
func DecodeJSONRequest(r *http.Request, v interface{}) error {
	defer r.Body.Close()
	
	body, err := io.ReadAll(r.Body)
	if err != nil {
		return err
	}

	if len(body) == 0 {
		return nil
	}

	return json.Unmarshal(body, v)
}

// EncodeJSONResponse encodes a response as JSON and writes it to the response writer
func EncodeJSONResponse(w http.ResponseWriter, statusCode int, v interface{}) error {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)
	
	if v == nil {
		return nil
	}

	return json.NewEncoder(w).Encode(v)
}

// HandleGRPCError converts a gRPC error to an HTTP error response
func HandleGRPCError(w http.ResponseWriter, err error) {
	st, ok := status.FromError(err)
	if !ok {
		// Not a gRPC error, treat as internal server error
		EncodeJSONResponse(w, http.StatusInternalServerError, ErrorResponse{
			Error: ErrorDetail{
				Code:    "INTERNAL_ERROR",
				Message: "An internal error occurred",
			},
		})
		return
	}

	// Map gRPC status codes to HTTP status codes
	httpStatus := grpcCodeToHTTPStatus(st.Code())
	
	EncodeJSONResponse(w, httpStatus, ErrorResponse{
		Error: ErrorDetail{
			Code:    st.Code().String(),
			Message: st.Message(),
		},
	})
}

// grpcCodeToHTTPStatus maps gRPC status codes to HTTP status codes
func grpcCodeToHTTPStatus(code codes.Code) int {
	switch code {
	case codes.OK:
		return http.StatusOK
	case codes.Canceled:
		return http.StatusRequestTimeout
	case codes.Unknown:
		return http.StatusInternalServerError
	case codes.InvalidArgument:
		return http.StatusBadRequest
	case codes.DeadlineExceeded:
		return http.StatusGatewayTimeout
	case codes.NotFound:
		return http.StatusNotFound
	case codes.AlreadyExists:
		return http.StatusConflict
	case codes.PermissionDenied:
		return http.StatusForbidden
	case codes.ResourceExhausted:
		return http.StatusTooManyRequests
	case codes.FailedPrecondition:
		return http.StatusPreconditionFailed
	case codes.Aborted:
		return http.StatusConflict
	case codes.OutOfRange:
		return http.StatusBadRequest
	case codes.Unimplemented:
		return http.StatusNotImplemented
	case codes.Internal:
		return http.StatusInternalServerError
	case codes.Unavailable:
		return http.StatusServiceUnavailable
	case codes.DataLoss:
		return http.StatusInternalServerError
	case codes.Unauthenticated:
		return http.StatusUnauthorized
	default:
		return http.StatusInternalServerError
	}
}

// WriteError writes a standard error response
func WriteError(w http.ResponseWriter, statusCode int, code, message string) {
	EncodeJSONResponse(w, statusCode, ErrorResponse{
		Error: ErrorDetail{
			Code:    code,
			Message: message,
		},
	})
}
