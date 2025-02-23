import React, { useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import html2pdf from 'html2pdf.js';
import { Paper } from '@mui/material';

const PDFGenerator = ({ markdown, onGenerated }) => {
  const contentRef = useRef(null);

  const generatePDF = async () => {
    const element = contentRef.current;
    if (!element) return;

    const opt = {
      margin: 1,
      filename: 'rapport_analyse.pdf',
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2 },
      jsPDF: { unit: 'cm', format: 'a4', orientation: 'portrait' }
    };

    try {
      const pdf = await html2pdf().set(opt).from(element).save();
      if (onGenerated) {
        onGenerated(pdf);
      }
    } catch (error) {
      console.error('Erreur lors de la génération du PDF:', error);
    }
  };

  return (
    <div style={{ display: 'none' }}>
      <Paper ref={contentRef} sx={{ p: 3 }}>
        <ReactMarkdown 
          remarkPlugins={[remarkGfm]}
          components={{
            h1: ({ children }) => (
              <h1 style={{ color: '#1976d2', fontSize: '24px', marginBottom: '20px' }}>
                {children}
              </h1>
            ),
            h2: ({ children }) => (
              <h2 style={{ color: '#1976d2', fontSize: '20px', marginBottom: '15px' }}>
                {children}
              </h2>
            ),
            table: ({ children }) => (
              <table style={{ 
                width: '100%', 
                borderCollapse: 'collapse', 
                marginBottom: '20px' 
              }}>
                {children}
              </table>
            ),
            th: ({ children }) => (
              <th style={{ 
                backgroundColor: '#1976d2',
                color: 'white',
                padding: '10px',
                border: '1px solid #ddd'
              }}>
                {children}
              </th>
            ),
            td: ({ children }) => (
              <td style={{ 
                padding: '8px',
                border: '1px solid #ddd'
              }}>
                {children}
              </td>
            ),
            p: ({ children }) => (
              <p style={{ 
                marginBottom: '10px',
                lineHeight: '1.6'
              }}>
                {children}
              </p>
            ),
            li: ({ children }) => (
              <li style={{ 
                marginBottom: '5px',
                lineHeight: '1.4'
              }}>
                {children}
              </li>
            )
          }}
        >
          {markdown}
        </ReactMarkdown>
      </Paper>
    </div>
  );
};

export default PDFGenerator;
