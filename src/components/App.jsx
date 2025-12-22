import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Alert,
  Paper,
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
import JobOfferUpload from './JobOfferUpload';
import JobOfferList from './JobOfferList';
import JobOfferEdit from './JobOfferEdit';
import { apiUrl } from '../config';

function App() {
  const [screen, setScreen] = useState('home'); // 'home', 'analyzer', 'editor', 'jobofferupload', 'jobofferedit'
  const [currentProject, setCurrentProject] = useState(null);
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedAnalysis, setSelectedAnalysis] = useState(null);
  const [jobOffers, setJobOffers] = useState([]);
  const [editingJobOffer, setEditingJobOffer] = useState(null);

  // Charger les offres d'emploi quand on entre dans l'analyzer
  useEffect(() => {
    if (screen === 'analyzer' && currentProject) {
      fetchJobOffers();
    }
  }, [screen, currentProject?.id]);

  const fetchJobOffers = async () => {
    if (!currentProject) return;
    try {
      const response = await fetch(apiUrl(`/api/projects/${currentProject.id}/job-offers`));
      if (response.ok) {
        const data = await response.json();
        setJobOffers(data);
      }
    } catch (err) {
      console.error('Erreur chargement offres:', err);
    }
  };

  const handleAnalysisComplete = (data) => {
    setLoading(false);
    if (data && data.report) {
      setReport(data.report);
      setError(null);
    } else {
      setError('Format de reponse invalide');
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
        throw new Error('Element rapport non trouve');
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
    setJobOffers([]);
  };

  const handleEditProject = (project) => {
    setCurrentProject(project);
    setScreen('editor');
  };

  const handleBackToHome = () => {
    setScreen('home');
    setCurrentProject(null);
    setReport(null);
    setJobOffers([]);
  };

  const handleBackToAnalyzer = () => {
    setScreen('analyzer');
  };

  const handleProjectSave = (project) => {
    setCurrentProject(project);
    setScreen('analyzer');
  };

  const handleAddJobOffer = () => {
    setScreen('jobofferupload');
  };

  const handleJobOfferUploadComplete = (jobOffer) => {
    setJobOffers(prev => [jobOffer, ...prev]);
    setScreen('analyzer');
  };

  const handleEditJobOffer = (offer) => {
    setEditingJobOffer(offer);
    setScreen('jobofferedit');
  };

  const handleJobOfferSave = (updatedOffer) => {
    setJobOffers(prev => prev.map(o => o.id === updatedOffer.id ? updatedOffer : o));
    setScreen('analyzer');
    setEditingJobOffer(null);
  };

  return (
    <>
      {screen === 'home' && (
        <HomeScreen onProjectSelect={handleProjectSelect} />
      )}

      {screen === 'analyzer' && currentProject && (
        <Box sx={{ minHeight: '100vh', background: 'linear-gradient(45deg, #f5f5f5 30%, #e3f2fd 90%)', py: 4 }}>
          <Container maxWidth="lg">
            {/* Header avec bouton editer */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
              <Box>
                <Button startIcon={<BackIcon />} onClick={handleBackToHome} sx={{ mb: 2 }}>
                  Retour a l'accueil
                </Button>
                <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
                  {currentProject.name}
                </Typography>
              </Box>
              <Button
                variant="outlined"
                onClick={() => handleEditProject(currentProject)}
              >
                Editer le projet
              </Button>
            </Box>

            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            {loading && <LinearProgress sx={{ mb: 2 }} />}

            {/* Liste des offres d'emploi */}
            <JobOfferList
              projectId={currentProject.id}
              onAddClick={handleAddJobOffer}
              onEditClick={handleEditJobOffer}
              onOfferSelect={(offer) => console.log('Offre selectionnee:', offer)}
            />

            {/* Formulaire d'analyse */}
            <CVAnalyzerForm
              project={currentProject}
              jobOffers={jobOffers}
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

      {screen === 'jobofferupload' && currentProject && (
        <Box sx={{ minHeight: '100vh', background: 'linear-gradient(45deg, #f5f5f5 30%, #e3f2fd 90%)', py: 4 }}>
          <Container maxWidth="lg">
            <Button startIcon={<BackIcon />} onClick={handleBackToAnalyzer} sx={{ mb: 2 }}>
              Retour
            </Button>
            <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 3 }}>
              {currentProject.name} - Importer une offre
            </Typography>
            <JobOfferUpload
              projectId={currentProject.id}
              onUploadComplete={handleJobOfferUploadComplete}
              onBack={handleBackToAnalyzer}
            />
          </Container>
        </Box>
      )}

      {screen === 'jobofferedit' && currentProject && editingJobOffer && (
        <Box sx={{ minHeight: '100vh', background: 'linear-gradient(45deg, #f5f5f5 30%, #e3f2fd 90%)', py: 4 }}>
          <Container maxWidth="lg">
            <Button startIcon={<BackIcon />} onClick={handleBackToAnalyzer} sx={{ mb: 2 }}>
              Retour
            </Button>
            <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 3 }}>
              {currentProject.name} - Modifier l'offre
            </Typography>
            <JobOfferEdit
              jobOffer={editingJobOffer}
              onSave={handleJobOfferSave}
              onBack={handleBackToAnalyzer}
            />
          </Container>
        </Box>
      )}
    </>
  );
}

export default App;
