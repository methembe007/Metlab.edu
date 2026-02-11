package utils

import (
	"testing"
)

func TestValidateEmail(t *testing.T) {
	tests := []struct {
		name    string
		email   string
		wantErr bool
		errMsg  string
	}{
		{
			name:    "valid email",
			email:   "teacher@example.com",
			wantErr: false,
		},
		{
			name:    "valid email with subdomain",
			email:   "teacher@mail.example.com",
			wantErr: false,
		},
		{
			name:    "valid email with plus",
			email:   "teacher+test@example.com",
			wantErr: false,
		},
		{
			name:    "valid email with numbers",
			email:   "teacher123@example.com",
			wantErr: false,
		},
		{
			name:    "empty email",
			email:   "",
			wantErr: true,
			errMsg:  "required",
		},
		{
			name:    "no @ symbol",
			email:   "teacherexample.com",
			wantErr: true,
			errMsg:  "invalid email format",
		},
		{
			name:    "no domain",
			email:   "teacher@",
			wantErr: true,
			errMsg:  "invalid email format",
		},
		{
			name:    "no local part",
			email:   "@example.com",
			wantErr: true,
			errMsg:  "invalid email format",
		},
		{
			name:    "no TLD",
			email:   "teacher@example",
			wantErr: true,
			errMsg:  "invalid email format",
		},
		{
			name:    "spaces in email",
			email:   "teacher @example.com",
			wantErr: true,
			errMsg:  "invalid email format",
		},
		{
			name:    "email with whitespace trimmed",
			email:   "  teacher@example.com  ",
			wantErr: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := ValidateEmail(tt.email)
			if (err != nil) != tt.wantErr {
				t.Errorf("ValidateEmail() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if tt.wantErr && err != nil && tt.errMsg != "" {
				if !containsStr(err.Error(), tt.errMsg) {
					t.Errorf("ValidateEmail() error = %v, want error containing %v", err, tt.errMsg)
				}
			}
		})
	}
}

func containsStr(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}
