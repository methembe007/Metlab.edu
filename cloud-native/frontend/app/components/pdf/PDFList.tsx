import React, { useState } from 'react';
import { formatFileSize, formatDate } from '../../api/pdfApi';

export interface PDF {
  id: string;
  title: string;
  description: string;
  fileName: string;
  fileSizeBytes: number;
  createdAt: string;
  downloadedByStudent: boolean;
}

interface PDFListProps {
  pdfs: PDF[];
  onDownload: (pdf: PDF) => void;
  isDownloading?: string; // PDF ID currently being downloaded
}

export const PDFList: React.FC<PDFListProps> = ({
  pdfs,
  onDownload,
  isDownloading,
}) => {
  return (
    <div className="pdf-list">
      <h2 className="pdf-list-title" style={{ fontSize: '24px', marginBottom: '20px' }}>
        Course Materials
      </h2>
      
      {pdfs.length === 0 ? (
        <div className="no-pdfs" style={{ padding: '40px', textAlign: 'center', color: '#666' }}>
          <p>No PDF materials available yet.</p>
        </div>
      ) : (
        <div className="pdf-items">
          {pdfs.map((pdf) => {
            const isCurrentlyDownloading = isDownloading === pdf.id;

            return (
              <div
                key={pdf.id}
                className="pdf-item"
                style={{
                  padding: '16px',
                  marginBottom: '12px',
                  border: '1px solid #ddd',
                  borderRadius: '8px',
                  backgroundColor: '#fff',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '16px',
                }}
              >
                {/* PDF Icon */}
                <div
                  className="pdf-icon"
                  style={{
                    width: '48px',
                    height: '48px',
                    backgroundColor: '#dc3545',
                    borderRadius: '8px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#fff',
                    fontSize: '20px',
                    fontWeight: 'bold',
                    flexShrink: 0,
                  }}
                >
                  PDF
                </div>

                {/* PDF Info */}
                <div className="pdf-info" style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <h3
                      className="pdf-title"
                      style={{
                        margin: 0,
                        fontSize: '16px',
                        fontWeight: '600',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {pdf.title}
                    </h3>
                    {pdf.downloadedByStudent && (
                      <span
                        className="downloaded-badge"
                        style={{
                          backgroundColor: '#28a745',
                          color: '#fff',
                          padding: '2px 8px',
                          borderRadius: '12px',
                          fontSize: '11px',
                          fontWeight: '600',
                          flexShrink: 0,
                        }}
                      >
                        ✓ Downloaded
                      </span>
                    )}
                  </div>

                  {pdf.description && (
                    <p
                      className="pdf-description"
                      style={{
                        margin: '4px 0',
                        fontSize: '14px',
                        color: '#666',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {pdf.description}
                    </p>
                  )}

                  <div
                    className="pdf-metadata"
                    style={{
                      display: 'flex',
                      gap: '16px',
                      fontSize: '12px',
                      color: '#999',
                      marginTop: '4px',
                    }}
                  >
                    <span className="file-size">
                      📄 {formatFileSize(pdf.fileSizeBytes)}
                    </span>
                    <span className="upload-date">
                      📅 {formatDate(pdf.createdAt)}
                    </span>
                  </div>
                </div>

                {/* Download Button */}
                <button
                  className="download-button"
                  onClick={() => onDownload(pdf)}
                  disabled={isCurrentlyDownloading}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: isCurrentlyDownloading ? '#6c757d' : '#007bff',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '6px',
                    fontSize: '14px',
                    fontWeight: '600',
                    cursor: isCurrentlyDownloading ? 'not-allowed' : 'pointer',
                    flexShrink: 0,
                    minWidth: '100px',
                    transition: 'background-color 0.2s',
                  }}
                  onMouseEnter={(e) => {
                    if (!isCurrentlyDownloading) {
                      e.currentTarget.style.backgroundColor = '#0056b3';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isCurrentlyDownloading) {
                      e.currentTarget.style.backgroundColor = '#007bff';
                    }
                  }}
                >
                  {isCurrentlyDownloading ? 'Downloading...' : 'Download'}
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
