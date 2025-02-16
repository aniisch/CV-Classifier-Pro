import React, { useState } from 'react';
import { Container, Typography, Box, Alert } from '@mui/material';
import CVAnalyzerForm from './CVAnalyzerForm';
import AnalysisReport from './AnalysisReport';
import AnalysisHistory from './AnalysisHistory';

function App() {
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  // Gérer la réception d'un nouveau rapport d'analyse
  const handleAnalysisComplete = (data) => {
    if (data && data.report) {
      setReport(data.report);
      setError(null);
    } else {
      setError('Format de réponse invalide');
    }
  };

  // Gérer la sélection d'une analyse depuis l'historique
  const handleHistorySelect = (reportContent) => {
    if (reportContent) {
      setReport(reportContent);
      setError(null);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom align="center">
        📊 CV Classifier Pro
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Historique des analyses */}
      <AnalysisHistory onAnalysisSelect={handleHistorySelect} />

      {/* Formulaire d'analyse */}
      <CVAnalyzerForm onAnalysisComplete={handleAnalysisComplete} />

      {/* Affichage du rapport */}
      <Box mt={4}>
        {report && <AnalysisReport report={report} />}
      </Box>
    </Container>
  );
}

export default App;
