import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { PDFList, PDF } from './PDFList';

describe('PDFList', () => {
  const mockPDFs: PDF[] = [
    {
      id: '1',
      title: 'Introduction to React',
      description: 'Learn the basics of React',
      fileName: 'react-intro.pdf',
      fileSizeBytes: 2097152, // 2 MB
      createdAt: '2024-01-15T10:00:00Z',
      downloadedByStudent: false,
    },
    {
      id: '2',
      title: 'Advanced TypeScript',
      description: 'Deep dive into TypeScript features',
      fileName: 'typescript-advanced.pdf',
      fileSizeBytes: 5242880, // 5 MB
      createdAt: '2024-01-20T14:30:00Z',
      downloadedByStudent: true,
    },
  ];

  it('should render PDF list with title', () => {
    const onDownload = vi.fn();
    render(<PDFList pdfs={mockPDFs} onDownload={onDownload} />);

    expect(screen.getByText('Course Materials')).toBeDefined();
  });

  it('should render all PDFs', () => {
    const onDownload = vi.fn();
    render(<PDFList pdfs={mockPDFs} onDownload={onDownload} />);

    expect(screen.getByText('Introduction to React')).toBeDefined();
    expect(screen.getByText('Advanced TypeScript')).toBeDefined();
  });

  it('should display PDF descriptions', () => {
    const onDownload = vi.fn();
    render(<PDFList pdfs={mockPDFs} onDownload={onDownload} />);

    expect(screen.getByText('Learn the basics of React')).toBeDefined();
    expect(screen.getByText('Deep dive into TypeScript features')).toBeDefined();
  });

  it('should display file sizes', () => {
    const onDownload = vi.fn();
    render(<PDFList pdfs={mockPDFs} onDownload={onDownload} />);

    expect(screen.getByText(/2 MB/)).toBeDefined();
    expect(screen.getByText(/5 MB/)).toBeDefined();
  });

  it('should display upload dates', () => {
    const onDownload = vi.fn();
    render(<PDFList pdfs={mockPDFs} onDownload={onDownload} />);

    expect(screen.getByText(/Jan 15, 2024/)).toBeDefined();
    expect(screen.getByText(/Jan 20, 2024/)).toBeDefined();
  });

  it('should show downloaded badge for previously downloaded PDFs', () => {
    const onDownload = vi.fn();
    render(<PDFList pdfs={mockPDFs} onDownload={onDownload} />);

    const badges = screen.getAllByText('✓ Downloaded');
    expect(badges).toHaveLength(1);
  });

  it('should render download buttons', () => {
    const onDownload = vi.fn();
    render(<PDFList pdfs={mockPDFs} onDownload={onDownload} />);

    const buttons = screen.getAllByText('Download');
    expect(buttons).toHaveLength(2);
  });

  it('should call onDownload when download button is clicked', () => {
    const onDownload = vi.fn();
    render(<PDFList pdfs={mockPDFs} onDownload={onDownload} />);

    const buttons = screen.getAllByText('Download');
    fireEvent.click(buttons[0]);

    expect(onDownload).toHaveBeenCalledWith(mockPDFs[0]);
  });

  it('should show downloading state for specific PDF', () => {
    const onDownload = vi.fn();
    render(<PDFList pdfs={mockPDFs} onDownload={onDownload} isDownloading="1" />);

    expect(screen.getByText('Downloading...')).toBeDefined();
  });

  it('should disable button when downloading', () => {
    const onDownload = vi.fn();
    render(<PDFList pdfs={mockPDFs} onDownload={onDownload} isDownloading="1" />);

    const downloadingButton = screen.getByText('Downloading...').closest('button');
    expect(downloadingButton?.disabled).toBe(true);
  });

  it('should show empty state when no PDFs', () => {
    const onDownload = vi.fn();
    render(<PDFList pdfs={[]} onDownload={onDownload} />);

    expect(screen.getByText('No PDF materials available yet.')).toBeDefined();
  });

  it('should render PDF without description', () => {
    const pdfWithoutDescription: PDF = {
      id: '3',
      title: 'Quick Reference',
      description: '',
      fileName: 'reference.pdf',
      fileSizeBytes: 1024,
      createdAt: '2024-01-25T10:00:00Z',
      downloadedByStudent: false,
    };

    const onDownload = vi.fn();
    render(<PDFList pdfs={[pdfWithoutDescription]} onDownload={onDownload} />);

    expect(screen.getByText('Quick Reference')).toBeDefined();
  });

  it('should handle multiple downloads correctly', () => {
    const onDownload = vi.fn();
    render(<PDFList pdfs={mockPDFs} onDownload={onDownload} />);

    const buttons = screen.getAllByText('Download');
    fireEvent.click(buttons[0]);
    fireEvent.click(buttons[1]);

    expect(onDownload).toHaveBeenCalledTimes(2);
    expect(onDownload).toHaveBeenNthCalledWith(1, mockPDFs[0]);
    expect(onDownload).toHaveBeenNthCalledWith(2, mockPDFs[1]);
  });
});
