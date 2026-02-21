# Video Viewing UI Components

This directory contains the video viewing functionality for students in the cloud-native learning platform.

## Components

### VideoPlayer
A full-featured video player component with HLS streaming support.

**Features:**
- HLS (HTTP Live Streaming) support for adaptive bitrate streaming
- Playback controls: play, pause, seek
- Playback speed adjustment (0.5x to 2x)
- Volume control with mute toggle
- Progress bar with time display
- Resume functionality from last watched position
- Automatic progress tracking

**Props:**
- `videoUrl` (string): URL of the video (supports HLS .m3u8 files)
- `videoId` (string): Unique identifier for the video
- `currentTime` (number, optional): Starting position in seconds
- `onTimeUpdate` (function, optional): Callback fired during playback with current time
- `onEnded` (function, optional): Callback fired when video ends

**Example:**
```tsx
<VideoPlayer
  videoUrl="https://example.com/video.m3u8"
  videoId="video-123"
  currentTime={120}
  onTimeUpdate={(time) => console.log('Current time:', time)}
  onEnded={() => console.log('Video ended')}
/>
```

### VideoList
Displays a list of videos with thumbnails, progress indicators, and metadata.

**Features:**
- Video thumbnails with duration badges
- Progress bars showing watch percentage
- Completion status indicators
- Active video highlighting
- Click to select video

**Props:**
- `videos` (Video[]): Array of video objects
- `onVideoSelect` (function): Callback when a video is selected
- `currentVideoId` (string, optional): ID of currently playing video

**Video Object:**
```typescript
interface Video {
  id: string;
  title: string;
  description: string;
  thumbnailUrl: string;
  duration: number; // in seconds
  progress?: number; // in seconds
  videoUrl: string;
}
```

**Example:**
```tsx
<VideoList
  videos={videos}
  onVideoSelect={(video) => setSelectedVideo(video)}
  currentVideoId={selectedVideo?.id}
/>
```

## Hooks

### useVideoProgress
Custom hook for tracking video viewing progress and sending updates to the backend.

**Features:**
- Automatic progress tracking at configurable intervals
- Backend API integration
- Completion detection (95% threshold)
- Accumulated viewing time calculation
- Cleanup on unmount

**Parameters:**
- `videoId` (string): Video identifier
- `onProgressUpdate` (function, optional): Callback for progress updates
- `updateInterval` (number, optional): Update frequency in milliseconds (default: 10000)
- `apiEndpoint` (string, optional): Backend API endpoint (default: '/api/video-progress')

**Returns:**
- `trackProgress(currentTime, duration)`: Function to track progress
- `handleVideoEnd(currentTime, duration)`: Function to handle video completion
- `resetProgress()`: Function to reset tracking state
- `accumulatedTime`: Total viewing time in seconds

**Example:**
```tsx
const { trackProgress, handleVideoEnd } = useVideoProgress({
  videoId: 'video-123',
  onProgressUpdate: (data) => console.log('Progress:', data),
  updateInterval: 10000,
});

<VideoPlayer
  onTimeUpdate={(time) => trackProgress(time, duration)}
  onEnded={() => handleVideoEnd(duration, duration)}
/>
```

## Routes

### /student/videos
Main video viewing page that integrates all components.

**Features:**
- Video player with selected video
- Video list sidebar
- Auto-play next video on completion
- Progress persistence
- Responsive layout

## Backend Integration

The video viewing UI sends progress updates to the backend API:

**Endpoint:** `POST /api/video-progress`

**Request Body:**
```json
{
  "videoId": "video-123",
  "currentTime": 120.5,
  "duration": 600,
  "completed": false,
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

**Response:** `200 OK`

## Requirements Mapping

This implementation satisfies the following requirements:

- **10.1**: Video player with HLS support ✓
- **10.2**: Playback controls (play, pause, seek, speed) ✓
- **10.3**: Video progress and resume functionality ✓
- **10.4**: Video list with thumbnails and progress ✓
- **10.5**: Track viewing time and send to backend ✓

## Testing

Unit tests are provided for all components and hooks:
- `VideoPlayer.test.tsx`: Tests for video player functionality
- `VideoList.test.tsx`: Tests for video list rendering and interaction
- `useVideoProgress.test.ts`: Tests for progress tracking logic

Run tests with:
```bash
npm test
```

## Dependencies

- **hls.js**: HLS streaming support
- **React**: UI framework
- **@testing-library/react**: Testing utilities

Install dependencies:
```bash
npm install hls.js
npm install --save-dev @types/hls.js
```

## Browser Support

- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Native HLS support (no hls.js needed)
- Mobile browsers: Full support with native HLS

## Future Enhancements

- Closed captions/subtitles support
- Quality selector for manual bitrate control
- Picture-in-picture mode
- Keyboard shortcuts
- Playlist management
- Download for offline viewing
- Video bookmarks/notes
