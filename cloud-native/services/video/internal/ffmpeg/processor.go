package ffmpeg

import (
	"context"
	"fmt"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
)

// Processor handles video processing using FFmpeg
type Processor struct {
	ffmpegPath string
	ffprobePath string
}

// NewProcessor creates a new FFmpeg processor
func NewProcessor() *Processor {
	return &Processor{
		ffmpegPath:  "ffmpeg",
		ffprobePath: "ffprobe",
	}
}

// VideoMetadata contains metadata extracted from a video
type VideoMetadata struct {
	DurationSeconds int32
	Width           int32
	Height          int32
	Bitrate         int32
	Codec           string
	Format          string
}

// GetMetadata extracts metadata from a video file
func (p *Processor) GetMetadata(ctx context.Context, inputPath string) (*VideoMetadata, error) {
	// Get duration
	durationCmd := exec.CommandContext(ctx, p.ffprobePath,
		"-v", "error",
		"-show_entries", "format=duration",
		"-of", "default=noprint_wrappers=1:nokey=1",
		inputPath,
	)
	durationOutput, err := durationCmd.Output()
	if err != nil {
		return nil, fmt.Errorf("failed to get duration: %w", err)
	}
	durationStr := strings.TrimSpace(string(durationOutput))
	durationFloat, err := strconv.ParseFloat(durationStr, 64)
	if err != nil {
		return nil, fmt.Errorf("failed to parse duration: %w", err)
	}

	// Get video stream info
	videoInfoCmd := exec.CommandContext(ctx, p.ffprobePath,
		"-v", "error",
		"-select_streams", "v:0",
		"-show_entries", "stream=width,height,bit_rate,codec_name",
		"-of", "csv=p=0",
		inputPath,
	)
	videoInfoOutput, err := videoInfoCmd.Output()
	if err != nil {
		return nil, fmt.Errorf("failed to get video info: %w", err)
	}

	// Parse video info (format: width,height,bit_rate,codec_name)
	parts := strings.Split(strings.TrimSpace(string(videoInfoOutput)), ",")
	if len(parts) < 4 {
		return nil, fmt.Errorf("unexpected video info format")
	}

	width, _ := strconv.ParseInt(parts[0], 10, 32)
	height, _ := strconv.ParseInt(parts[1], 10, 32)
	bitrate, _ := strconv.ParseInt(parts[2], 10, 32)
	codec := parts[3]

	// Get format
	formatCmd := exec.CommandContext(ctx, p.ffprobePath,
		"-v", "error",
		"-show_entries", "format=format_name",
		"-of", "default=noprint_wrappers=1:nokey=1",
		inputPath,
	)
	formatOutput, err := formatCmd.Output()
	if err != nil {
		return nil, fmt.Errorf("failed to get format: %w", err)
	}

	return &VideoMetadata{
		DurationSeconds: int32(durationFloat),
		Width:           int32(width),
		Height:          int32(height),
		Bitrate:         int32(bitrate / 1000), // Convert to kbps
		Codec:           codec,
		Format:          strings.TrimSpace(string(formatOutput)),
	}, nil
}

// TranscodeOptions contains options for video transcoding
type TranscodeOptions struct {
	Resolution string // 1080p, 720p, 480p, 360p
	BitrateKbps int32
	OutputPath string
}

// Transcode transcodes a video to a different resolution and bitrate
func (p *Processor) Transcode(ctx context.Context, inputPath string, opts *TranscodeOptions) error {
	// Determine output dimensions based on resolution
	var scale string
	switch opts.Resolution {
	case "1080p":
		scale = "1920:1080"
	case "720p":
		scale = "1280:720"
	case "480p":
		scale = "854:480"
	case "360p":
		scale = "640:360"
	default:
		return fmt.Errorf("unsupported resolution: %s", opts.Resolution)
	}

	// Build FFmpeg command
	args := []string{
		"-i", inputPath,
		"-vf", fmt.Sprintf("scale=%s:force_original_aspect_ratio=decrease,pad=%s:(ow-iw)/2:(oh-ih)/2", scale, scale),
		"-c:v", "libx264",
		"-preset", "medium",
		"-b:v", fmt.Sprintf("%dk", opts.BitrateKbps),
		"-c:a", "aac",
		"-b:a", "128k",
		"-movflags", "+faststart",
		"-y", // Overwrite output file
		opts.OutputPath,
	}

	cmd := exec.CommandContext(ctx, p.ffmpegPath, args...)
	output, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("transcoding failed: %w, output: %s", err, string(output))
	}

	return nil
}

// GenerateThumbnail generates a thumbnail at a specific timestamp percentage
func (p *Processor) GenerateThumbnail(ctx context.Context, inputPath string, timestampPercent int32, outputPath string) error {
	// Get video duration first
	metadata, err := p.GetMetadata(ctx, inputPath)
	if err != nil {
		return fmt.Errorf("failed to get metadata: %w", err)
	}

	// Calculate timestamp in seconds
	timestamp := float64(metadata.DurationSeconds) * float64(timestampPercent) / 100.0

	// Build FFmpeg command
	args := []string{
		"-ss", fmt.Sprintf("%.2f", timestamp),
		"-i", inputPath,
		"-vframes", "1",
		"-vf", "scale=320:-1",
		"-y", // Overwrite output file
		outputPath,
	}

	cmd := exec.CommandContext(ctx, p.ffmpegPath, args...)
	output, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("thumbnail generation failed: %w, output: %s", err, string(output))
	}

	return nil
}

// GenerateHLSManifest generates an HLS manifest for adaptive streaming
func (p *Processor) GenerateHLSManifest(ctx context.Context, inputPath, outputDir string) error {
	// Create output directory if it doesn't exist
	manifestPath := filepath.Join(outputDir, "playlist.m3u8")
	segmentPattern := filepath.Join(outputDir, "segment_%03d.ts")

	// Build FFmpeg command for HLS
	args := []string{
		"-i", inputPath,
		"-c:v", "libx264",
		"-c:a", "aac",
		"-hls_time", "10", // 10 second segments
		"-hls_playlist_type", "vod",
		"-hls_segment_filename", segmentPattern,
		"-y",
		manifestPath,
	}

	cmd := exec.CommandContext(ctx, p.ffmpegPath, args...)
	output, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("HLS generation failed: %w, output: %s", err, string(output))
	}

	return nil
}

// ValidateVideoFile checks if a file is a valid video with supported format
func (p *Processor) ValidateVideoFile(ctx context.Context, filePath string) error {
	cmd := exec.CommandContext(ctx, p.ffprobePath,
		"-v", "error",
		"-show_entries", "format=format_name",
		"-of", "default=noprint_wrappers=1:nokey=1",
		filePath,
	)

	output, err := cmd.Output()
	if err != nil {
		return fmt.Errorf("invalid video file: %w", err)
	}

	format := strings.TrimSpace(string(output))
	if format == "" {
		return fmt.Errorf("unable to detect video format")
	}

	// Check if format is one of the supported formats
	// FFprobe returns format names like "mov,mp4,m4a,3gp,3g2,mj2" for MP4/MOV
	// and "matroska,webm" for WebM
	supportedFormats := []string{"mov", "mp4", "webm", "matroska"}
	isSupported := false
	
	formatParts := strings.Split(format, ",")
	for _, part := range formatParts {
		for _, supported := range supportedFormats {
			if strings.Contains(strings.ToLower(part), supported) {
				isSupported = true
				break
			}
		}
		if isSupported {
			break
		}
	}

	if !isSupported {
		return fmt.Errorf("unsupported video format: %s (supported formats: MP4, WebM, MOV)", format)
	}

	return nil
}

// GetRecommendedBitrate returns recommended bitrate for a resolution
func GetRecommendedBitrate(resolution string) int32 {
	switch resolution {
	case "1080p":
		return 5000 // 5 Mbps
	case "720p":
		return 2500 // 2.5 Mbps
	case "480p":
		return 1000 // 1 Mbps
	case "360p":
		return 500 // 500 kbps
	default:
		return 2500
	}
}
