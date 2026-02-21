# Video Viewing UI - Quick Start Guide

## Getting Started

### 1. Install Dependencies

```bash
npm install hls.js
npm install --save-dev @types/hls.js @testing-library/react @testing-library/jest-dom
```

### 2. Import Components

```tsx
import { VideoPlayer, VideoList } from './app/components/video';
import { useVideoProgress } from './app/hooks/useVideoProgress';
```

### 3. Basic Usage

#### Simple Video Player

```tsx
import { VideoPlayer } from './app/components/video';

function MyVideoPage() {
  return (
    <VideoPlayer
      videoUrl="https://example.com/video.m3u8"
      videoId="video-123"
      currentTime={0}
      onTimeUpdate={(time) => console.log('Current time:', time)}
      onEnded={() => console.log('Video ended')}
    />
  );
}
```

#### Video List with Player

```tsx
import { useState } from 'react';
import { VideoPlayer, VideoList, Video } from './app/components/video';

function VideosPage() {
  const [videos] = useState<Video[]>([
    {
      id: 'video-1',
      title: 'Introduction',
      description: 'Getting started',
      thumbnailUrl: 'https://example.com/thumb.jpg',
      duration: 600,
      videoUrl: 'https://example.com/video.m3u8',
      progress: 0,
    },
  ]);
  
  const [selectedVideo, setSelectedVideo] = useState(videos[0]);

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 400px', gap: '20px' }}>
      <VideoPlayer
        videoUrl={selectedVideo.videoUrl}
        videoId={selectedVideo.id}
        currentTime={selectedVideo.progress || 0}
      />
      <VideoList
        videos={videos}
        onVideoSelect={setSelectedVideo}
        currentVideoId={selectedVideo.id}
      />
    </div>
  );
}
```

#### With Progress Tracking

```tsx
import { VideoPlayer } from './app/components/video';
import { useVideoProgress } from './app/hooks/useVideoProgress';

function VideoWithTracking() {
  const { trackProgress, handleVideoEnd } = useVideoProgress({
    videoId: 'video-123',
    onProgressUpdate: (data) => {
      console.log('Progress:', data);
    },
    updateInterval: 10000, // Update every 10 seconds
  });

  return (
    <VideoPlayer
      videoUrl="https://example.com/video.m3u8"
      videoId="video-123"
      onTimeUpdate={(time) => trackProgress(time, 600)}
      onEnded={() => handleVideoEnd(600, 600)}
    />
  );
}
```

### 4. Backend Integration

#### Fetch Videos from API

```tsx
import { fetchVideos } from './app/api/videoApi';

async function loadVideos() {
  try {
    const { videos } = await fetchVideos();
    console.log('Loaded videos:', videos);
  } catch (error) {
    console.error('Failed to load videos:', error);
  }
}
```

#### Update Progress

```tsx
import { updateVideoProgress } from './app/api/videoApi';

async function saveProgress() {
  await updateVideoProgress({
    videoId: 'video-123',
    currentTime: 120,
    duration: 600,
    completed: false,
    timestamp: new Date().toISOString(),
  });
}
```

### 5. Run Tests

```bash
# Run all tests
npm test

# Run specific test file
npm test VideoPlayer.test.tsx

# Run with coverage
npm test -- --coverage
```

### 6. Styling

Import the CSS file in your component:

```tsx
import './app/components/video/VideoPlayer.css';
```

Or customize with your own styles:

```tsx
<VideoPlayer
  videoUrl="..."
  videoId="..."
  // Add custom className or inline styles
/>
```

## Common Use Cases

### Auto-play Next Video

```tsx
const handleVideoEnded = () => {
  const currentIndex = videos.findIndex(v => v.id === selectedVideo.id);
  if (currentIndex < videos.length - 1) {
    setSelectedVideo(videos[currentIndex + 1]);
  }
};

<VideoPlayer onEnded={handleVideoEnded} />
```

### Resume from Last Position

```tsx
const [progress, setProgress] = useState(0);

// Load progress from API
useEffect(() => {
  async function loadProgress() {
    const time = await getVideoProgress(videoId);
    setProgress(time);
  }
  loadProgress();
}, [videoId]);

<VideoPlayer currentTime={progress} />
```

### Track Completion

```tsx
const { trackProgress } = useVideoProgress({
  videoId: 'video-123',
  onProgressUpdate: (data) => {
    if (data.completed) {
      console.log('Video completed!');
      // Show next lesson, update UI, etc.
    }
  },
});
```

## Troubleshooting

### Video Not Playing

1. Check video URL is accessible
2. Verify HLS format (.m3u8)
3. Check CORS headers on video CDN
4. Open browser console for errors

### Progress Not Saving

1. Verify API endpoint is correct
2. Check network tab for failed requests
3. Ensure authentication is working
4. Check backend logs

### Tests Failing

1. Ensure all dependencies are installed
2. Check Jest configuration
3. Mock fetch in tests
4. Clear Jest cache: `npm test -- --clearCache`

## Production Checklist

- [ ] Install hls.js dependency
- [ ] Configure backend API endpoints
- [ ] Set up video CDN
- [ ] Encode videos to HLS format
- [ ] Generate video thumbnails
- [ ] Configure CORS headers
- [ ] Implement authentication
- [ ] Set up monitoring
- [ ] Test on multiple browsers
- [ ] Test on mobile devices
- [ ] Run all tests
- [ ] Enable analytics

## Support

For more details, see:
- [README.md](./app/components/video/README.md) - Full documentation
- [DEPENDENCIES.md](./DEPENDENCIES.md) - Dependency details
- [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) - Implementation details

## Example: Complete Page

See `app/routes/student/videos.tsx` for a complete working example with:
- Video player
- Video list
- Progress tracking
- Auto-play next
- Error handling
- Loading states
