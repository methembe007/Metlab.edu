import { renderHook, act } from '@testing-library/react';
import { useVideoProgress } from './useVideoProgress';

// Mock fetch
global.fetch = jest.fn();

describe('useVideoProgress', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({}),
    });
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('initializes with correct default values', () => {
    const { result } = renderHook(() =>
      useVideoProgress({
        videoId: 'test-video',
      })
    );

    expect(result.current.accumulatedTime).toBe(0);
    expect(typeof result.current.trackProgress).toBe('function');
    expect(typeof result.current.handleVideoEnd).toBe('function');
    expect(typeof result.current.resetProgress).toBe('function');
  });

  it('tracks progress at specified intervals', async () => {
    const onProgressUpdate = jest.fn();
    const { result } = renderHook(() =>
      useVideoProgress({
        videoId: 'test-video',
        onProgressUpdate,
        updateInterval: 5000,
      })
    );

    act(() => {
      result.current.trackProgress(10, 100);
    });

    // Fast-forward time
    act(() => {
      jest.advanceTimersByTime(5000);
    });

    act(() => {
      result.current.trackProgress(15, 100);
    });

    expect(onProgressUpdate).toHaveBeenCalled();
  });

  it('sends progress to backend', async () => {
    const { result } = renderHook(() =>
      useVideoProgress({
        videoId: 'test-video',
        updateInterval: 5000,
        apiEndpoint: '/api/test-progress',
      })
    );

    act(() => {
      result.current.trackProgress(10, 100);
    });

    act(() => {
      jest.advanceTimersByTime(5000);
    });

    act(() => {
      result.current.trackProgress(15, 100);
    });

    await act(async () => {
      await Promise.resolve();
    });

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/test-progress',
      expect.objectContaining({
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })
    );
  });

  it('marks video as completed when >= 95% watched', async () => {
    const onProgressUpdate = jest.fn();
    const { result } = renderHook(() =>
      useVideoProgress({
        videoId: 'test-video',
        onProgressUpdate,
        updateInterval: 5000,
      })
    );

    act(() => {
      result.current.trackProgress(96, 100);
    });

    act(() => {
      jest.advanceTimersByTime(5000);
    });

    act(() => {
      result.current.trackProgress(97, 100);
    });

    expect(onProgressUpdate).toHaveBeenCalledWith(
      expect.objectContaining({
        completed: true,
      })
    );
  });

  it('handles video end correctly', async () => {
    const onProgressUpdate = jest.fn();
    const { result } = renderHook(() =>
      useVideoProgress({
        videoId: 'test-video',
        onProgressUpdate,
      })
    );

    await act(async () => {
      result.current.handleVideoEnd(100, 100);
    });

    expect(onProgressUpdate).toHaveBeenCalledWith(
      expect.objectContaining({
        videoId: 'test-video',
        currentTime: 100,
        duration: 100,
        completed: true,
      })
    );
  });

  it('resets progress correctly', () => {
    const { result } = renderHook(() =>
      useVideoProgress({
        videoId: 'test-video',
      })
    );

    act(() => {
      result.current.trackProgress(50, 100);
    });

    act(() => {
      result.current.resetProgress();
    });

    expect(result.current.accumulatedTime).toBe(0);
  });

  it('does not send updates more frequently than interval', async () => {
    const onProgressUpdate = jest.fn();
    const { result } = renderHook(() =>
      useVideoProgress({
        videoId: 'test-video',
        onProgressUpdate,
        updateInterval: 10000,
      })
    );

    act(() => {
      result.current.trackProgress(10, 100);
    });

    act(() => {
      jest.advanceTimersByTime(5000);
    });

    act(() => {
      result.current.trackProgress(15, 100);
    });

    expect(onProgressUpdate).not.toHaveBeenCalled();

    act(() => {
      jest.advanceTimersByTime(5000);
    });

    act(() => {
      result.current.trackProgress(20, 100);
    });

    expect(onProgressUpdate).toHaveBeenCalledTimes(1);
  });

  it('handles fetch errors gracefully', async () => {
    const consoleError = jest.spyOn(console, 'error').mockImplementation();
    (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() =>
      useVideoProgress({
        videoId: 'test-video',
        updateInterval: 5000,
      })
    );

    act(() => {
      result.current.trackProgress(10, 100);
    });

    act(() => {
      jest.advanceTimersByTime(5000);
    });

    act(() => {
      result.current.trackProgress(15, 100);
    });

    await act(async () => {
      await Promise.resolve();
    });

    expect(consoleError).toHaveBeenCalled();
    consoleError.mockRestore();
  });
});
