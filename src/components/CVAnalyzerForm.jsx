import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Button,
  Paper,
  Typography,
  Alert
} from '@mui/material';
import FolderOpenIcon from '@mui/icons-material/FolderOpen';
import SendIcon from '@mui/icons-material/Send';

const CVAnalyzerForm = ({ project, onAnalysisComplete, onAnalysisStart }) => {
  const [folderPath, setFolderPath] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Debug logging dans useEffect pour éviter la boucle infinie
  useEffect(() => {
    console.log('CVAnalyzerForm - project reçu:', project);
    console.log('CVAnalyzerForm - project exists?', !!project);
    if (project) {
      console.log('CVAnalyzerForm - project.id:', project.id);
      console.log('CVAnalyzerForm - project.name:', project.name);
      console.log('CVAnalyzerForm - project.keywords:', project.keywords);
    }
  }, [project]);

  // Si pas de projet, ne rien afficher
  if (!project) {
    return null;
  }

  const keywords = project.keywords || {};
  const hasKeywords = Object.keys(keywords).length > 0;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!folderPath) {
      setError('Veuillez spécifier le dossier des CVs');
      return;
    }

    if (!hasKeywords) {
      setError('Veuillez configurer des mots-clés dans le projet');
      return;
    }

    try {
      setLoading(true);
      onAnalysisStart?.();

      const response = await fetch(`/api/projects/${project.id}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folder_path: folderPath }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erreur lors de l\'analyse');
      }

      const data = await response.json();
      onAnalysisComplete(data);
    } catch (error) {
      setError(error.message);
      onAnalysisComplete(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        Analyse - {project.name}
      </Typography>

      <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
        <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
          <TextField
            fullWidth
            label="Dossier des CVs"
            value={folderPath}
            onChange={(e) => setFolderPath(e.target.value)}
            placeholder="C:\Users\username\CVs"
            InputProps={{
              startAdornment: <FolderOpenIcon color="action" sx={{ mr: 1 }} />,
            }}
            disabled={loading}
          />
          <Button
            variant="outlined"
            onClick={() => {
              const path = window.prompt('Entrez le chemin du dossier:');
              if (path) setFolderPath(path);
            }}
            disabled={loading}
            sx={{ whiteSpace: 'nowrap' }}
          >
            Parcourir
          </Button>
        </Box>

        <Typography variant="body2" sx={{ mt: 2, mb: 2 }}>
          Mots-clés configurés: {Object.entries(keywords).map(([k, v]) => `${k} (${v}%)`).join(', ')}
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Button
          type="submit"
          variant="contained"
          fullWidth
          endIcon={<SendIcon />}
          disabled={!folderPath || loading}
        >
          {loading ? 'Analyse en cours...' : 'Analyser les CVs'}
        </Button>
      </Box>
    </Paper>
  );
};

export default CVAnalyzerForm;
