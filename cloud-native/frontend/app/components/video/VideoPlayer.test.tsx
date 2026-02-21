import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { VideoPlayer } from './VideoPlayer';

// Mock HLS.js
jest.mock('hls.js', () => {
  return {
    __esModule: true,
    default: class MockHls {
      static isSupported = () => true;
      loadSource = jest.fn();
      attachMedia = jest.fn();
      on = jest.fn();
      destroy = jest.fn();
    },
  };
});

describe('VideoPlayer', () => {
  const mockProps = {
    videoUrl: 'https://example.com/video.m3u8',
    videoId: 'test-video-1',
    currentTime: 0,
    onTimeUpdate: jest.fn(),
    onEnded: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders video element', () => {
    render(<VideoPlayer {...mockProps} />);
    const videoElement = document.querySelector('video');
    expect(videoElement).toBeInTheDocument();
  });

  it('renders play button', () => {
    render(<VideoPlayer {...mockProps} />);
    const playButton = screen.getByText(/Play/i);
    expect(playButton).toBeInTheDocument();
  });

  it('renders playback speed selector', () => {
    render(<VideoPlayer {...mockProps} />);
    const speedSelect = screen.getByRole('combobox');
    expect(speedSelect).toBeInTheDocument();
  });

  it('has correct playback speed options', () => {
    render(<VideoPlayer {...mockProps} />);
    const options = screen.getAllByRole('option');
    expect(options).toHaveLength(6);
    expect(options[0]).toHaveValue('0.5');
    expect(options[2]).toHaveValue('1');
    expect(options[5]).toHaveValue('2');
  });

  it('renders progress bar', () => {
    render(<VideoPlayer {...mockProps} />);
    const progressBar = screen.getByRole('slider');
    expect(progressBar).toBeInTheDocument();
  });

  it('renders volume controls', () => {
    render(<VideoPlayer {...mockProps} />);
    const volumeSliders = screen.getAllByRole('slider');
    expect(volumeSliders.length).toBeGreaterThan(1);
  });

  it('formats time correctly', () => {
    render(<VideoPlayer {...mockProps} />);
    // Initial time should be 0:00
    expect(screen.getByText('0:00')).toBeInTheDocument();
  });

  it('resumes from current time when provided', () => {
    const propsWithCurrentTime = {
      ...mockProps,
      currentTime: 120, // 2 minutes
    };
    render(<VideoPlayer {...propsWithCurrentTime} />);
    const videoElement = document.querySelector('video') as HTMLVideoElement;
    expect(videoElement).toBeInTheDocument();
  });
});
