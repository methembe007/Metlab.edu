# PDF Components

This directory contains React components for displaying and managing PDF documents in the student portal.

## Components

### PDFList

Displays a list of available PDF documents with download functionality.

**Features:**
- Display PDF list with titles and descriptions
- Show file sizes in human-readable format (KB, MB, GB)
- Display upload dates in readable format
- Visual indicator for previously downloaded PDFs
- Download button with loading state
- Empty state when no PDFs are available

**Props:**
- `pdfs`: Array of PDF objects to display
- `onDownload`: Callback function when download button is clicked
- `isDownloading`: Optional PDF ID currently being downloaded (for loading state)

**Usage:**
```tsx
import { PDFList } from './components/pdf';
import { downloadPDF } from './api/pdfApi';

function StudentPDFs() {
  const [pdfs, setPdfs] = useState([]);
  const [downloading, setDownloading] = useState<string | undefined>();

  const handleDownload = async (pdf) => {
    setDownloading(pdf.id);
    try {
      await downloadPDF(pdf.id, pdf.fileName);
      // Update the PDF as downloaded
      setPdfs(pdfs.map(p => 
        p.id === pdf.id ? { ...p, downloadedByStudent: true } : p
      ));
    } catch (error) {
      console.error('Download failed:', error);
    } finally {
      setDownloading(undefined);
    }
  };

  return <PDFList pdfs={pdfs} onDownload={handleDownload} isDownloading={downloading} />;
}
```

## API Integration

The PDF components work with the `pdfApi.ts` module which provides:

- `fetchPDFs(classId?)`: Fetch all PDFs for the student's class
- `downloadPDF(pdfId, fileName)`: Download a PDF and track the download
- `getDownloadURL(pdfId)`: Get a secure download URL
- `formatFileSize(bytes)`: Format file size to human-readable format
- `formatDate(dateString)`: Format date to readable format

## Requirements Satisfied

This implementation satisfies the following requirements:

- **11.1**: Display list of available PDF documents with titles and upload dates
- **11.2**: Generate secure download URL and initiate download when button clicked
- **11.3**: Display PDF file size before download
- **11.4**: Allow unlimited downloads (no restrictions in UI)
- **11.5**: Indicate which PDFs the student has previously downloaded
