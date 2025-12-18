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
import html2pdf from 'html2pdf.js';
import HomeScreen from './HomeScreen';
import ProjectEditor from './ProjectEditor';
import CVAnalyzerForm from './CVAnalyzerForm';
import AnalysisReport from './AnalysisReport';
import AnalysisHistory from './AnalysisHistory';

function App() {
  const [screen, setScreen] = useState('home'); // 'home', 'editor', 'analyzer'
  const [currentProject, setCurrentProject] = useState(null);
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedAnalysis, setSelectedAnalysis] = useState(null);

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
  const handleHistorySelect = (reportContent, analysisId) => {
    if (reportContent) {
      setReport(reportContent);
      setSelectedAnalysis(analysisId);
      setError(null);
    }
  };

  // Gérer le début d'une analyse
  const handleAnalysisStart = () => {
    setLoading(true);
    setError(null);
  };

  // Gérer l'export PDF
  const handleExportPDF = async () => {
    if (!report) return;
    
    try {
      const element = document.querySelector('.report-content');
      if (!element) {
        throw new Error('Élément rapport non trouvé');
      }

      // Générer le nom du fichier avec la date et l'heure actuelles
      const now = new Date();
      const dateStr = now.toISOString()
        .replace(/[-:]/g, '')  // Enlever les tirets et les deux points
        .split('T')[0];        // Garder seulement la date
      const timeStr = now.toISOString()
        .split('T')[1]         // Prendre la partie heure
        .split('.')[0]         // Enlever les millisecondes
        .replace(/:/g, '');    // Enlever les deux points

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
    setScreen('editor');
  };

  const handleBackToHome = () => {
    setScreen('home');
    setCurrentProject(null);
    setReport(null);
  };

  const handleProjectSave = (project) => {
    setCurrentProject(project);
    // Rester sur l'écran editor après save
  };

  return (
    <>
      {screen === 'home' && (
        <HomeScreen onProjectSelect={handleProjectSelect} />
      )}

      {screen === 'editor' && currentProject && (
        <Box sx={{ minHeight: '100vh', background: 'linear-gradient(45deg, #f5f5f5 30%, #e3f2fd 90%)', py: 4 }}>
          <Container maxWidth="lg">
            <ProjectEditor
              project={currentProject}
              onBack={handleBackToHome}
              onSave={handleProjectSave}
            />

            {/* Afficher le formulaire d'analyse sous le ProjectEditor */}
            <Box sx={{ mt: 4 }}>
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
                    <Grow in timeout={500}>
                      <Box sx={{ mt: 4 }}>
                        <Paper
                          elevation={3}
                          sx={{
                            p: 3,
                            borderRadius: 3,
                            boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                          }}
                        >
                          <AnalysisReport
                            report={report}
                            onExportPDF={handleExportPDF}
                          />
                        </Paper>
                      </Box>
                    </Grow>
                  )}
                </Box>
              </Fade>
            </Box>
          </Container>
        </Box>
      )}
    </>
  );
}

export default App;
