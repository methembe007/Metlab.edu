/**
 * PDF API Client
 * Handles all PDF-related API calls to the backend
 */

export interface PDFData {
  id: string;
  title: string;
  description: string;
  fileName: string;
  fileSizeBytes: number;
  createdAt: string;
  downloadedByStudent: boolean;
}

export interface PDFListResponse {
  pdfs: PDFData[];
  totalCount: number;
}

/**
 * Fetch all PDFs for the current student's class
 */
export async function fetchPDFs(classId?: string): Promise<PDFListResponse> {
  const url = classId ? `/api/pdfs?classId=${classId}` : '/api/pdfs';

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include', // Include cookies for authentication
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch PDFs: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get a secure download URL for a PDF
 * This will also track the download
 */
export async function getDownloadURL(pdfId: string): Promise<string> {
  const response = await fetch(`/api/pdfs/${pdfId}/download`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error(`Failed to get download URL: ${response.statusText}`);
  }

  const data = await response.json();
  return data.url;
}

/**
 * Download a PDF file
 * This function handles the download process and tracking
 */
export async function downloadPDF(pdfId: string, fileName: string): Promise<void> {
  try {
    // Get the secure download URL
    const downloadUrl = await getDownloadURL(pdfId);

    // Create a temporary anchor element to trigger download
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = fileName;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } catch (error) {
    throw new Error(`Failed to download PDF: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Format file size in bytes to human-readable format
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

/**
 * Format date string to readable format
 */
export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}
