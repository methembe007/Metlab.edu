import {
  fetchVideos,
  fetchVideoById,
  updateVideoProgress,
  getVideoProgress,
  markVideoCompleted,
} from './videoApi';

// Mock fetch
global.fetch = jest.fn();

describe('videoApi', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('fetchVideos', () => {
    it('fetches all videos successfully', async () => {
      const mockResponse = {
        videos: [
          {
            id: 'video-1',
            title: 'Test Video',
            description: 'Test Description',
            thumbnailUrl: 'https://example.com/thumb.jpg',
            duration: 600,
            videoUrl: 'https://example.com/video.m3u8',
          },
        ],
        totalCount: 1,
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await fetchVideos();

      expect(global.fetch).toHaveBeenCalledWith('/api/videos', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });
      expect(result).toEqual(mockResponse);
    });

    it('fetches videos for specific course', async () => {
      const mockResponse = {
        videos: [],
        totalCount: 0,
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      });

      await fetchVideos('course-123');

      expect(global.fetch).toHaveBeenCalledWith('/api/videos?courseId=course-123', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });
    });

    it('throws error on failed request', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        statusText: 'Not Found',
      });

      await expect(fetchVideos()).rejects.toThrow('Failed to fetch videos: Not Found');
    });
  });

  describe('fetchVideoById', () => {
    it('fetches single video successfully', async () => {
      const mockVideo = {
        id: 'video-1',
        title: 'Test Video',
        description: 'Test Description',
        thumbnailUrl: 'https://example.com/thumb.jpg',
        duration: 600,
        videoUrl: 'https://example.com/video.m3u8',
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockVideo,
      });

      const result = await fetchVideoById('video-1');

      expect(global.fetch).toHaveBeenCalledWith('/api/videos/video-1', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });
      expect(result).toEqual(mockVideo);
    });

    it('throws error when video not found', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        statusText: 'Not Found',
      });

      await expect(fetchVideoById('invalid-id')).rejects.toThrow(
        'Failed to fetch video: Not Found'
      );
    });
  });

  describe('updateVideoProgress', () => {
    it('updates video progress successfully', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
      });

      const payload = {
        videoId: 'video-1',
        currentTime: 120,
        duration: 600,
        completed: false,
        timestamp: '2024-01-15T10:30:00.000Z',
      };

      await updateVideoProgress(payload);

      expect(global.fetch).toHaveBeenCalledWith('/api/video-progress', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(payload),
      });
    });

    it('throws error on failed update', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        statusText: 'Internal Server Error',
      });

      const payload = {
        videoId: 'video-1',
        currentTime: 120,
        duration: 600,
        completed: false,
        timestamp: '2024-01-15T10:30:00.000Z',
      };

      await expect(updateVideoProgress(payload)).rejects.toThrow(
        'Failed to update video progress: Internal Server Error'
      );
    });
  });

  describe('getVideoProgress', () => {
    it('gets video progress successfully', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ currentTime: 120 }),
      });

      const result = await getVideoProgress('video-1');

      expect(global.fetch).toHaveBeenCalledWith('/api/video-progress/video-1', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });
      expect(result).toBe(120);
    });

    it('returns 0 when no progress exists', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({}),
      });

      const result = await getVideoProgress('video-1');

      expect(result).toBe(0);
    });

    it('throws error on failed request', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        statusText: 'Not Found',
      });

      await expect(getVideoProgress('video-1')).rejects.toThrow(
        'Failed to get video progress: Not Found'
      );
    });
  });

  describe('markVideoCompleted', () => {
    it('marks video as completed successfully', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
      });

      await markVideoCompleted('video-1');

      expect(global.fetch).toHaveBeenCalledWith('/api/videos/video-1/complete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });
    });

    it('throws error on failed request', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        statusText: 'Unauthorized',
      });

      await expect(markVideoCompleted('video-1')).rejects.toThrow(
        'Failed to mark video as completed: Unauthorized'
      );
    });
  });
});
