package utils

import (
	"crypto/rand"
	"math/big"
)

const (
	// Characters to use for signin code generation (alphanumeric, excluding ambiguous characters)
	codeCharset = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
	codeLength  = 8
)

// GenerateSigninCode generates a random 8-character alphanumeric signin code
func GenerateSigninCode() (string, error) {
	code := make([]byte, codeLength)
	charsetLen := big.NewInt(int64(len(codeCharset)))
	
	for i := 0; i < codeLength; i++ {
		num, err := rand.Int(rand.Reader, charsetLen)
		if err != nil {
			return "", err
		}
		code[i] = codeCharset[num.Int64()]
	}
	
	return string(code), nil
}
