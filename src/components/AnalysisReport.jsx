import React from 'react';
import { Box, Paper, Typography } from '@mui/material';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const AnalysisReport = ({ report }) => {
  return (
    <Paper 
      elevation={3}
      sx={{
        p: 3,
        transition: 'all 0.3s ease-in-out',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: '0 6px 12px rgba(0,0,0,0.1)',
        }
      }}
    >
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        📋 Rapport d'Analyse
      </Typography>

      <Box 
        sx={{ 
          '& table': {
            borderCollapse: 'collapse',
            width: '100%',
            mb: 2,
          },
          '& th, & td': {
            border: '1px solid rgba(224, 224, 224, 1)',
            padding: '8px 16px',
            textAlign: 'left',
          },
          '& th': {
            backgroundColor: 'primary.main',
            color: 'white',
          },
          '& tr:nth-of-type(even)': {
            backgroundColor: 'rgba(0, 0, 0, 0.02)',
          },
          '& tr:hover': {
            backgroundColor: 'rgba(0, 0, 0, 0.04)',
          },
          '& h1': {
            color: 'primary.main',
            fontSize: '1.5rem',
            fontWeight: 600,
            mb: 2,
          },
          '& h2': {
            color: 'primary.dark',
            fontSize: '1.25rem',
            fontWeight: 500,
            mb: 2,
            mt: 3,
          },
          '& p': {
            mb: 2,
            lineHeight: 1.6,
          },
          '& ul, & ol': {
            pl: 3,
            mb: 2,
          },
          '& li': {
            mb: 1,
          },
          '& code': {
            backgroundColor: 'rgba(0, 0, 0, 0.04)',
            padding: '2px 4px',
            borderRadius: 1,
            fontFamily: 'monospace',
          },
          '& blockquote': {
            borderLeft: '4px solid',
            borderColor: 'primary.main',
            pl: 2,
            py: 1,
            my: 2,
            backgroundColor: 'rgba(0, 0, 0, 0.02)',
          }
        }}
      >
        <ReactMarkdown 
          remarkPlugins={[remarkGfm]}
          components={{
            h1: ({ node, ...props }) => (
              <Typography variant="h4" gutterBottom {...props} />
            ),
            h2: ({ node, ...props }) => (
              <Typography variant="h5" gutterBottom {...props} />
            ),
            p: ({ node, ...props }) => (
              <Typography variant="body1" paragraph {...props} />
            ),
            li: ({ node, ...props }) => (
              <Typography component="li" variant="body1" {...props} />
            ),
          }}
        >
          {report}
        </ReactMarkdown>
      </Box>
    </Paper>
  );
};

export default AnalysisReport;
