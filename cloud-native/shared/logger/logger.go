package logger

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"runtime"
	"time"
)

// Level represents the log level
type Level int

const (
	// DebugLevel is for debug messages
	DebugLevel Level = iota
	// InfoLevel is for informational messages
	InfoLevel
	// WarnLevel is for warning messages
	WarnLevel
	// ErrorLevel is for error messages
	ErrorLevel
	// FatalLevel is for fatal messages (will exit the program)
	FatalLevel
)

// String returns the string representation of the log level
func (l Level) String() string {
	switch l {
	case DebugLevel:
		return "DEBUG"
	case InfoLevel:
		return "INFO"
	case WarnLevel:
		return "WARN"
	case ErrorLevel:
		return "ERROR"
	case FatalLevel:
		return "FATAL"
	default:
		return "UNKNOWN"
	}
}

// Config holds logger configuration
type Config struct {
	Level       Level             // Minimum log level to output
	ServiceName string            // Name of the service
	Output      io.Writer         // Output writer (default: os.Stdout)
	AddCaller   bool              // Add caller information (file and line)
	Fields      map[string]string // Default fields to include in all logs
}

// DefaultConfig returns a configuration with sensible defaults
func DefaultConfig() *Config {
	return &Config{
		Level:       InfoLevel,
		ServiceName: "metlab-service",
		Output:      os.Stdout,
		AddCaller:   true,
		Fields:      make(map[string]string),
	}
}

// Logger provides structured logging
type Logger struct {
	config *Config
}

// New creates a new logger with the given configuration
func New(cfg *Config) *Logger {
	if cfg == nil {
		cfg = DefaultConfig()
	}
	if cfg.Output == nil {
		cfg.Output = os.Stdout
	}
	if cfg.Fields == nil {
		cfg.Fields = make(map[string]string)
	}
	return &Logger{
		config: cfg,
	}
}

// LogEntry represents a single log entry
type LogEntry struct {
	Timestamp   string                 `json:"timestamp"`
	Level       string                 `json:"level"`
	Service     string                 `json:"service"`
	Message     string                 `json:"message"`
	Fields      map[string]interface{} `json:"fields,omitempty"`
	Caller      string                 `json:"caller,omitempty"`
	TraceID     string                 `json:"trace_id,omitempty"`
	UserID      string                 `json:"user_id,omitempty"`
	Error       string                 `json:"error,omitempty"`
	StackTrace  string                 `json:"stack_trace,omitempty"`
}

// log writes a log entry
func (l *Logger) log(level Level, msg string, fields map[string]interface{}) {
	if level < l.config.Level {
		return
	}

	entry := LogEntry{
		Timestamp: time.Now().UTC().Format(time.RFC3339Nano),
		Level:     level.String(),
		Service:   l.config.ServiceName,
		Message:   msg,
		Fields:    make(map[string]interface{}),
	}

	// Add default fields
	for k, v := range l.config.Fields {
		entry.Fields[k] = v
	}

	// Add custom fields
	for k, v := range fields {
		entry.Fields[k] = v
	}

	// Add caller information if enabled
	if l.config.AddCaller {
		if _, file, line, ok := runtime.Caller(2); ok {
			entry.Caller = fmt.Sprintf("%s:%d", file, line)
		}
	}

	// Marshal to JSON
	data, err := json.Marshal(entry)
	if err != nil {
		fmt.Fprintf(os.Stderr, "failed to marshal log entry: %v\n", err)
		return
	}

	// Write to output
	fmt.Fprintln(l.config.Output, string(data))

	// Exit if fatal
	if level == FatalLevel {
		os.Exit(1)
	}
}

// Debug logs a debug message
func (l *Logger) Debug(msg string, fields ...map[string]interface{}) {
	f := mergeFields(fields...)
	l.log(DebugLevel, msg, f)
}

// Info logs an info message
func (l *Logger) Info(msg string, fields ...map[string]interface{}) {
	f := mergeFields(fields...)
	l.log(InfoLevel, msg, f)
}

// Warn logs a warning message
func (l *Logger) Warn(msg string, fields ...map[string]interface{}) {
	f := mergeFields(fields...)
	l.log(WarnLevel, msg, f)
}

// Error logs an error message
func (l *Logger) Error(msg string, err error, fields ...map[string]interface{}) {
	f := mergeFields(fields...)
	if err != nil {
		f["error"] = err.Error()
	}
	l.log(ErrorLevel, msg, f)
}

// Fatal logs a fatal message and exits the program
func (l *Logger) Fatal(msg string, err error, fields ...map[string]interface{}) {
	f := mergeFields(fields...)
	if err != nil {
		f["error"] = err.Error()
	}
	l.log(FatalLevel, msg, f)
}

// WithFields returns a new logger with additional default fields
func (l *Logger) WithFields(fields map[string]string) *Logger {
	newFields := make(map[string]string)
	for k, v := range l.config.Fields {
		newFields[k] = v
	}
	for k, v := range fields {
		newFields[k] = v
	}

	newConfig := *l.config
	newConfig.Fields = newFields

	return &Logger{
		config: &newConfig,
	}
}

// WithTraceID returns a new logger with a trace ID
func (l *Logger) WithTraceID(traceID string) *Logger {
	return l.WithFields(map[string]string{"trace_id": traceID})
}

// WithUserID returns a new logger with a user ID
func (l *Logger) WithUserID(userID string) *Logger {
	return l.WithFields(map[string]string{"user_id": userID})
}

// WithContext returns a new logger with context values
func (l *Logger) WithContext(ctx context.Context) *Logger {
	fields := make(map[string]string)
	
	// Extract trace ID from context if available
	if traceID := ctx.Value("trace_id"); traceID != nil {
		if tid, ok := traceID.(string); ok {
			fields["trace_id"] = tid
		}
	}
	
	// Extract user ID from context if available
	if userID := ctx.Value("user_id"); userID != nil {
		if uid, ok := userID.(string); ok {
			fields["user_id"] = uid
		}
	}
	
	if len(fields) == 0 {
		return l
	}
	
	return l.WithFields(fields)
}

// mergeFields merges multiple field maps into one
func mergeFields(fields ...map[string]interface{}) map[string]interface{} {
	result := make(map[string]interface{})
	for _, f := range fields {
		for k, v := range f {
			result[k] = v
		}
	}
	return result
}

// Global logger instance
var defaultLogger = New(DefaultConfig())

// SetDefault sets the default global logger
func SetDefault(logger *Logger) {
	defaultLogger = logger
}

// Debug logs a debug message using the default logger
func Debug(msg string, fields ...map[string]interface{}) {
	defaultLogger.Debug(msg, fields...)
}

// Info logs an info message using the default logger
func Info(msg string, fields ...map[string]interface{}) {
	defaultLogger.Info(msg, fields...)
}

// Warn logs a warning message using the default logger
func Warn(msg string, fields ...map[string]interface{}) {
	defaultLogger.Warn(msg, fields...)
}

// Error logs an error message using the default logger
func Error(msg string, err error, fields ...map[string]interface{}) {
	defaultLogger.Error(msg, err, fields...)
}

// Fatal logs a fatal message using the default logger and exits
func Fatal(msg string, err error, fields ...map[string]interface{}) {
	defaultLogger.Fatal(msg, err, fields...)
}

// WithFields returns a new logger with additional default fields
func WithFields(fields map[string]string) *Logger {
	return defaultLogger.WithFields(fields)
}

// WithTraceID returns a new logger with a trace ID
func WithTraceID(traceID string) *Logger {
	return defaultLogger.WithTraceID(traceID)
}

// WithUserID returns a new logger with a user ID
func WithUserID(userID string) *Logger {
	return defaultLogger.WithUserID(userID)
}

// WithContext returns a new logger with context values
func WithContext(ctx context.Context) *Logger {
	return defaultLogger.WithContext(ctx)
}
