import React, { useState } from 'react';
import { 
  Container, 
  Typography, 
  Box, 
  Alert, 
  Paper,
  Fade,
  Grow,
  LinearProgress
} from '@mui/material';
import CVAnalyzerForm from './CVAnalyzerForm';
import AnalysisReport from './AnalysisReport';
import AnalysisHistory from './AnalysisHistory';

function App() {
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  // Gérer la réception d'un nouveau rapport d'analyse
  const handleAnalysisComplete = (data) => {
    setLoading(false);
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

  // Gérer le début d'une analyse
  const handleAnalysisStart = () => {
    setLoading(true);
    setError(null);
  };

  return (
    <Box sx={{ 
      minHeight: '100vh',
      background: 'linear-gradient(45deg, #f5f5f5 30%, #e3f2fd 90%)',
      py: 4 
    }}>
      <Container maxWidth="lg">
        <Fade in timeout={1000}>
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <Typography 
              variant="h4" 
              component="h1" 
              gutterBottom
              sx={{
                fontWeight: 'bold',
                textShadow: '2px 2px 4px rgba(0,0,0,0.1)',
                mb: 2
              }}
            >
              📊 CV Classifier Pro
            </Typography>
            <Typography 
              variant="subtitle1" 
              color="text.secondary"
              sx={{ mb: 4 }}
            >
              Analysez vos CV en quelques clics
            </Typography>
          </Box>
        </Fade>

        {error && (
          <Grow in timeout={500}>
            <Alert 
              severity="error" 
              sx={{ 
                mb: 2,
                borderRadius: 2,
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
              }}
            >
              {error}
            </Alert>
          </Grow>
        )}

        {loading && (
          <Box sx={{ width: '100%', mb: 2 }}>
            <LinearProgress />
          </Box>
        )}

        <Fade in timeout={800}>
          <Box>
            {/* Historique des analyses */}
            <AnalysisHistory onAnalysisSelect={handleHistorySelect} />

            {/* Formulaire d'analyse */}
            <CVAnalyzerForm 
              onAnalysisComplete={handleAnalysisComplete}
              onAnalysisStart={handleAnalysisStart}
            />

            {/* Affichage du rapport */}
            {report && (
              <Grow in timeout={500}>
                <Paper 
                  elevation={3} 
                  sx={{ 
                    mt: 4,
                    p: 3,
                    borderRadius: 3,
                    boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                  }}
                >
                  <AnalysisReport report={report} />
                </Paper>
              </Grow>
            )}
          </Box>
        </Fade>
      </Container>
    </Box>
  );
}

export default App;
