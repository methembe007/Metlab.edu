# Video Viewing UI Dependencies

## Required Dependencies

Add these dependencies to your `package.json`:

```json
{
  "dependencies": {
    "hls.js": "^1.4.12",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/hls.js": "^1.0.0",
    "@testing-library/react": "^14.0.0",
    "@testing-library/jest-dom": "^6.1.0",
    "@testing-library/user-event": "^14.5.0",
    "jest": "^29.7.0",
    "jest-environment-jsdom": "^29.7.0"
  }
}
```

## Installation

```bash
# Install production dependencies
npm install hls.js

# Install development dependencies
npm install --save-dev @types/hls.js @testing-library/react @testing-library/jest-dom
```

## HLS.js

HLS.js is a JavaScript library that implements an HTTP Live Streaming client. It relies on HTML5 video and MediaSource Extensions for playback.

**Why HLS.js?**
- Adaptive bitrate streaming
- Wide browser support
- Efficient bandwidth usage
- Industry standard for video streaming

**Browser Support:**
- Chrome 34+
- Firefox 42+
- Edge 12+
- Safari (native HLS support, hls.js not needed)
- Mobile browsers with MSE support

## Testing Libraries

The testing setup uses React Testing Library for component testing:

- `@testing-library/react`: React component testing utilities
- `@testing-library/jest-dom`: Custom Jest matchers for DOM
- `@testing-library/user-event`: User interaction simulation

## TypeScript Types

If using TypeScript, ensure you have the type definitions:

```bash
npm install --save-dev @types/react @types/react-dom @types/hls.js
```

## Jest Configuration

Add this to your `jest.config.js`:

```javascript
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
  },
  transform: {
    '^.+\\.(ts|tsx)$': 'ts-jest',
  },
};
```

Create `jest.setup.js`:

```javascript
import '@testing-library/jest-dom';
```

## Backend API Requirements

The video viewing UI expects the following backend endpoints:

### GET /api/videos
Returns list of available videos for the student.

**Response:**
```json
[
  {
    "id": "video-1",
    "title": "Introduction to Cloud Computing",
    "description": "Learn the fundamentals...",
    "thumbnailUrl": "https://cdn.example.com/thumb1.jpg",
    "duration": 1200,
    "progress": 0,
    "videoUrl": "https://cdn.example.com/video1.m3u8"
  }
]
```

### POST /api/video-progress
Receives video progress updates.

**Request:**
```json
{
  "videoId": "video-1",
  "currentTime": 120.5,
  "duration": 1200,
  "completed": false,
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

**Response:** `200 OK`

## CDN Configuration

For production deployment, videos should be served from a CDN:

1. **Video Storage**: Store videos in object storage (S3, GCS, Azure Blob)
2. **CDN**: Use CloudFront, Cloudflare, or similar CDN
3. **HLS Encoding**: Encode videos to HLS format with multiple bitrates
4. **Thumbnails**: Generate and store video thumbnails

### Example HLS Encoding (FFmpeg)

```bash
ffmpeg -i input.mp4 \
  -c:v h264 -c:a aac \
  -hls_time 10 \
  -hls_playlist_type vod \
  -hls_segment_filename "segment_%03d.ts" \
  output.m3u8
```

## Security Considerations

1. **Signed URLs**: Use signed URLs for video access
2. **Token Authentication**: Validate user access to videos
3. **CORS**: Configure CORS headers for video CDN
4. **Rate Limiting**: Implement rate limiting on progress API

## Performance Optimization

1. **Lazy Loading**: Load video player only when needed
2. **Preloading**: Preload next video in playlist
3. **Thumbnail Optimization**: Use optimized image formats (WebP)
4. **Progress Batching**: Batch progress updates to reduce API calls
