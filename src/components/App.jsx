import React, { useState } from 'react';
import { Container, Typography, Paper, Box } from '@mui/material';
import CVAnalyzerForm from './CVAnalyzerForm';
import AnalysisReport from './AnalysisReport';

function App() {
  const [report, setReport] = useState(null);

  const handleAnalysisComplete = (reportData) => {
    setReport(reportData);
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom>
          📊 CV Classifier Pro
        </Typography>
        
        <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
          <CVAnalyzerForm onAnalysisComplete={handleAnalysisComplete} />
        </Paper>

        {report && (
          <Paper elevation={3} sx={{ p: 3 }}>
            <AnalysisReport report={report} />
          </Paper>
        )}
      </Box>
    </Container>
  );
}

export default App;
