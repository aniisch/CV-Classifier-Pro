import React from 'react';
import { Box, Typography } from '@mui/material';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

function AnalysisReport({ report }) {
  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Résultats de l'analyse
      </Typography>
      <Box sx={{ 
        '& table': {
          borderCollapse: 'collapse',
          width: '100%',
          mb: 2
        },
        '& th, & td': {
          border: '1px solid #ddd',
          padding: '8px',
          textAlign: 'left'
        },
        '& th': {
          backgroundColor: '#f5f5f5'
        }
      }}>
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {report}
        </ReactMarkdown>
      </Box>
    </Box>
  );
}

export default AnalysisReport;
