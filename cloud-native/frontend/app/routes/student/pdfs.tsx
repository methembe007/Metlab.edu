import { useState, useEffect } from 'react';
import { PDFList, PDF } from '../../components/pdf';
import { fetchPDFs, downloadPDF } from '../../api/pdfApi';

/**
 * Student PDFs Page
 * Displays available PDF materials for the student to download
 */
export default function StudentPDFs() {
  const [pdfs, setPdfs] = useState<PDF[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<string | undefined>();

  // Fetch PDFs on component mount
  useEffect(() => {
    loadPDFs();
  }, []);

  const loadPDFs = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetchPDFs();
      setPdfs(response.pdfs);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load PDFs');
      console.error('Error loading PDFs:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (pdf: PDF) => {
    setDownloading(pdf.id);
    try {
      await downloadPDF(pdf.id, pdf.fileName);
      
      // Update the PDF as downloaded in the local state
      setPdfs(prevPdfs =>
        prevPdfs.map(p =>
          p.id === pdf.id ? { ...p, downloadedByStudent: true } : p
        )
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download PDF');
      console.error('Error downloading PDF:', err);
    } finally {
      setDownloading(undefined);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <p>Loading PDFs...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#dc3545' }}>
        <p>Error: {error}</p>
        <button
          onClick={loadPDFs}
          style={{
            marginTop: '16px',
            padding: '10px 20px',
            backgroundColor: '#007bff',
            color: '#fff',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
          }}
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <PDFList
        pdfs={pdfs}
        onDownload={handleDownload}
        isDownloading={downloading}
      />
    </div>
  );
}
