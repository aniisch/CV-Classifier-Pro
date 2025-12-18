import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Alert,
  Paper,
  Fade,
  Grow,
  LinearProgress,
  Button
} from '@mui/material';
import { ArrowBack as BackIcon } from '@mui/icons-material';
import html2pdf from 'html2pdf.js';
import HomeScreen from './HomeScreen';
import ProjectEditor from './ProjectEditor';
import CVAnalyzerForm from './CVAnalyzerForm';
import AnalysisReport from './AnalysisReport';
import AnalysisHistory from './AnalysisHistory';

function App() {
  const [screen, setScreen] = useState('home'); // 'home', 'analyzer', 'editor'
  const [currentProject, setCurrentProject] = useState(null);
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedAnalysis, setSelectedAnalysis] = useState(null);

  const handleAnalysisComplete = (data) => {
    setLoading(false);
    if (data && data.report) {
      setReport(data.report);
      setError(null);
    } else {
      setError('Format de réponse invalide');
    }
  };

  const handleHistorySelect = (reportContent, analysisId) => {
    if (reportContent) {
      setReport(reportContent);
      setSelectedAnalysis(analysisId);
      setError(null);
    }
  };

  const handleAnalysisStart = () => {
    setLoading(true);
    setError(null);
  };

  const handleExportPDF = async () => {
    if (!report) return;

    try {
      const element = document.querySelector('.report-content');
      if (!element) {
        throw new Error('Élément rapport non trouvé');
      }

      const now = new Date();
      const dateStr = now.toISOString()
        .replace(/[-:]/g, '')
        .split('T')[0];
      const timeStr = now.toISOString()
        .split('T')[1]
        .split('.')[0]
        .replace(/:/g, '');

      const opt = {
        margin: 1,
        filename: `rapport_analyse_${selectedAnalysis}_${dateStr}_${timeStr}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2 },
        jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
      };

      await html2pdf().set(opt).from(element).save();
    } catch (error) {
      setError('Erreur lors de l\'export en PDF');
      console.error('Erreur:', error);
    }
  };

  const handleProjectSelect = (project) => {
    setCurrentProject(project);
    setScreen('analyzer');
    setReport(null);
  };

  const handleEditProject = (project) => {
    setCurrentProject(project);
    setScreen('editor');
  };

  const handleBackToHome = () => {
    setScreen('home');
    setCurrentProject(null);
    setReport(null);
  };

  const handleBackToAnalyzer = () => {
    setScreen('analyzer');
  };

  const handleProjectSave = (project) => {
    setCurrentProject(project);
    setScreen('analyzer');
  };

  return (
    <>
      {screen === 'home' && (
        <HomeScreen onProjectSelect={handleProjectSelect} />
      )}

      {screen === 'analyzer' && currentProject && (
        <Box sx={{ minHeight: '100vh', background: 'linear-gradient(45deg, #f5f5f5 30%, #e3f2fd 90%)', py: 4 }}>
          <Container maxWidth="lg">
            {/* Header avec bouton éditer */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
              <Box>
                <Button startIcon={<BackIcon />} onClick={handleBackToHome} sx={{ mb: 2 }}>
                  Retour à l'accueil
                </Button>
                <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
                  {currentProject.name}
                </Typography>
              </Box>
              <Button
                variant="outlined"
                onClick={() => handleEditProject(currentProject)}
              >
                Éditer le projet
              </Button>
            </Box>

            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            {loading && <LinearProgress sx={{ mb: 2 }} />}

            {/* Formulaire d'analyse */}
            <CVAnalyzerForm
              project={currentProject}
              onAnalysisComplete={handleAnalysisComplete}
              onAnalysisStart={handleAnalysisStart}
            />

            {/* Historique des analyses */}
            <AnalysisHistory
              projectId={currentProject.id}
              onAnalysisSelect={handleHistorySelect}
            />

            {/* Affichage du rapport */}
            {report && (
              <Paper elevation={3} sx={{ p: 3, mt: 4 }}>
                <AnalysisReport
                  report={report}
                  onExportPDF={handleExportPDF}
                />
              </Paper>
            )}
          </Container>
        </Box>
      )}

      {screen === 'editor' && currentProject && (
        <Box sx={{ minHeight: '100vh', background: 'linear-gradient(45deg, #f5f5f5 30%, #e3f2fd 90%)', py: 4 }}>
          <Container maxWidth="lg">
            <ProjectEditor
              project={currentProject}
              onBack={handleBackToAnalyzer}
              onSave={handleProjectSave}
            />
          </Container>
        </Box>
      )}
    </>
  );
}

export default App;
