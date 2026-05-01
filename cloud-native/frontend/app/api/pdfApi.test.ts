import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  fetchPDFs,
  getDownloadURL,
  downloadPDF,
  formatFileSize,
  formatDate,
} from './pdfApi';

describe('pdfApi', () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('fetchPDFs', () => {
    it('should fetch PDFs without classId', async () => {
      const mockResponse = {
        pdfs: [
          {
            id: '1',
            title: 'Test PDF',
            description: 'Test description',
            fileName: 'test.pdf',
            fileSizeBytes: 1024,
            createdAt: '2024-01-01T00:00:00Z',
            downloadedByStudent: false,
          },
        ],
        totalCount: 1,
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await fetchPDFs();

      expect(global.fetch).toHaveBeenCalledWith('/api/pdfs', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });
      expect(result).toEqual(mockResponse);
    });

    it('should fetch PDFs with classId', async () => {
      const mockResponse = {
        pdfs: [],
        totalCount: 0,
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      await fetchPDFs('class-123');

      expect(global.fetch).toHaveBeenCalledWith('/api/pdfs?classId=class-123', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });
    });

    it('should throw error when fetch fails', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        statusText: 'Not Found',
      });

      await expect(fetchPDFs()).rejects.toThrow('Failed to fetch PDFs: Not Found');
    });
  });

  describe('getDownloadURL', () => {
    it('should get download URL for a PDF', async () => {
      const mockUrl = 'https://example.com/download/test.pdf?token=abc123';
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ url: mockUrl }),
      });

      const result = await getDownloadURL('pdf-123');

      expect(global.fetch).toHaveBeenCalledWith('/api/pdfs/pdf-123/download', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });
      expect(result).toBe(mockUrl);
    });

    it('should throw error when getting download URL fails', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        statusText: 'Unauthorized',
      });

      await expect(getDownloadURL('pdf-123')).rejects.toThrow(
        'Failed to get download URL: Unauthorized'
      );
    });
  });

  describe('downloadPDF', () => {
    it('should download PDF successfully', async () => {
      const mockUrl = 'https://example.com/download/test.pdf';
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ url: mockUrl }),
      });

      // Mock DOM methods
      const mockLink = {
        href: '',
        download: '',
        style: { display: '' },
        click: vi.fn(),
      };
      const appendChildSpy = vi.spyOn(document.body, 'appendChild').mockImplementation(() => mockLink as any);
      const removeChildSpy = vi.spyOn(document.body, 'removeChild').mockImplementation(() => mockLink as any);
      vi.spyOn(document, 'createElement').mockReturnValue(mockLink as any);

      await downloadPDF('pdf-123', 'test.pdf');

      expect(mockLink.href).toBe(mockUrl);
      expect(mockLink.download).toBe('test.pdf');
      expect(mockLink.click).toHaveBeenCalled();
      expect(appendChildSpy).toHaveBeenCalled();
      expect(removeChildSpy).toHaveBeenCalled();
    });

    it('should throw error when download fails', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        statusText: 'Not Found',
      });

      await expect(downloadPDF('pdf-123', 'test.pdf')).rejects.toThrow(
        'Failed to download PDF'
      );
    });
  });

  describe('formatFileSize', () => {
    it('should format 0 bytes', () => {
      expect(formatFileSize(0)).toBe('0 Bytes');
    });

    it('should format bytes', () => {
      expect(formatFileSize(500)).toBe('500 Bytes');
    });

    it('should format kilobytes', () => {
      expect(formatFileSize(1024)).toBe('1 KB');
      expect(formatFileSize(2048)).toBe('2 KB');
    });

    it('should format megabytes', () => {
      expect(formatFileSize(1048576)).toBe('1 MB');
      expect(formatFileSize(5242880)).toBe('5 MB');
    });

    it('should format gigabytes', () => {
      expect(formatFileSize(1073741824)).toBe('1 GB');
    });

    it('should format with decimals', () => {
      expect(formatFileSize(1536)).toBe('1.5 KB');
      expect(formatFileSize(2621440)).toBe('2.5 MB');
    });
  });

  describe('formatDate', () => {
    it('should format date string', () => {
      const result = formatDate('2024-01-15T10:30:00Z');
      expect(result).toMatch(/Jan 15, 2024/);
    });

    it('should handle different date formats', () => {
      const result = formatDate('2024-12-25T00:00:00Z');
      expect(result).toMatch(/Dec 25, 2024/);
    });
  });
});
