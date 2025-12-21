import React, { useState, useEffect } from 'react';
import { apiUrl } from '../config';
import {
  Box,
  TextField,
  Button,
  Paper,
  Typography,
  Alert,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  Select,
  MenuItem,
  InputLabel,
  Chip,
  Stack,
  Divider
} from '@mui/material';
import FolderOpenIcon from '@mui/icons-material/FolderOpen';
import SendIcon from '@mui/icons-material/Send';
import WorkIcon from '@mui/icons-material/Work';
import KeyIcon from '@mui/icons-material/Key';

const CVAnalyzerForm = ({ project, jobOffers = [], onAnalysisComplete, onAnalysisStart }) => {
  const [folderPath, setFolderPath] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [analysisMode, setAnalysisMode] = useState('keywords'); // 'keywords' ou 'joboffer'
  const [selectedJobOfferId, setSelectedJobOfferId] = useState('');

  useEffect(() => {
    console.log('CVAnalyzerForm - project:', project?.name);
    console.log('CVAnalyzerForm - jobOffers:', jobOffers?.length);
  }, [project, jobOffers]);

  if (!project) {
    return null;
  }

  const keywords = project.keywords || {};
  const hasKeywords = Object.keys(keywords).length > 0;
  const hasJobOffers = jobOffers && jobOffers.length > 0;

  const selectedJobOffer = jobOffers?.find(jo => jo.id === selectedJobOfferId);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!folderPath) {
      setError('Veuillez specifier le dossier des CVs');
      return;
    }

    if (analysisMode === 'keywords' && !hasKeywords) {
      setError('Veuillez configurer des mots-cles dans le projet');
      return;
    }

    if (analysisMode === 'joboffer' && !selectedJobOfferId) {
      setError('Veuillez selectionner une offre d\'emploi');
      return;
    }

    try {
      setLoading(true);
      onAnalysisStart?.();

      let url;
      if (analysisMode === 'keywords') {
        url = apiUrl(`/api/projects/${project.id}/analyze`);
      } else {
        url = apiUrl(`/api/projects/${project.id}/analyze-offer/${selectedJobOfferId}`);
      }

      const response = await fetch(url, {
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

  const handleBrowseFolder = async () => {
    if (window.electronAPI?.selectFolder) {
      try {
        const selectedPath = await window.electronAPI.selectFolder();
        if (selectedPath) setFolderPath(selectedPath);
      } catch (err) {
        console.error('Erreur selection dossier:', err);
        setError('Erreur lors de la selection du dossier');
      }
    } else {
      setError('Tapez le chemin du dossier manuellement');
    }
  };

  const getCurrentKeywords = () => {
    if (analysisMode === 'keywords') {
      return keywords;
    } else if (selectedJobOffer) {
      return selectedJobOffer.requirements || {};
    }
    return {};
  };

  const currentKeywords = getCurrentKeywords();
  const hasCurrentKeywords = Object.keys(currentKeywords).length > 0;

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        Analyse - {project.name}
      </Typography>

      <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
        {/* Selection du dossier */}
        <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
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
            onClick={handleBrowseFolder}
            disabled={loading}
            sx={{ whiteSpace: 'nowrap' }}
          >
            Parcourir
          </Button>
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Mode d'analyse */}
        <FormControl component="fieldset" sx={{ mb: 2, width: '100%' }}>
          <FormLabel component="legend" sx={{ mb: 1 }}>
            Mode d'analyse
          </FormLabel>
          <RadioGroup
            row
            value={analysisMode}
            onChange={(e) => {
              setAnalysisMode(e.target.value);
              setError('');
            }}
          >
            <FormControlLabel
              value="keywords"
              control={<Radio />}
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <KeyIcon fontSize="small" />
                  Mots-cles du projet
                  {hasKeywords && (
                    <Chip label={Object.keys(keywords).length} size="small" color="primary" />
                  )}
                </Box>
              }
              disabled={!hasKeywords}
            />
            <FormControlLabel
              value="joboffer"
              control={<Radio />}
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <WorkIcon fontSize="small" />
                  Offre d'emploi
                  {hasJobOffers && (
                    <Chip label={jobOffers.length} size="small" color="secondary" />
                  )}
                </Box>
              }
              disabled={!hasJobOffers}
            />
          </RadioGroup>
        </FormControl>

        {/* Selection de l'offre si mode joboffer */}
        {analysisMode === 'joboffer' && (
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel id="job-offer-select-label">Selectionner une offre</InputLabel>
            <Select
              labelId="job-offer-select-label"
              value={selectedJobOfferId}
              onChange={(e) => setSelectedJobOfferId(e.target.value)}
              label="Selectionner une offre"
              disabled={loading}
            >
              {jobOffers.map((offer) => (
                <MenuItem key={offer.id} value={offer.id}>
                  <Box>
                    <Typography variant="body2">{offer.filename}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {Object.keys(offer.requirements || {}).length} requirements
                    </Typography>
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        )}

        {/* Affichage des mots-cles utilises */}
        {hasCurrentKeywords && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Criteres d'evaluation ({Object.keys(currentKeywords).length}):
            </Typography>
            <Stack direction="row" spacing={0.5} flexWrap="wrap" sx={{ gap: 0.5 }}>
              {Object.entries(currentKeywords).slice(0, 8).map(([k, v]) => (
                <Chip
                  key={k}
                  label={`${k} (${v}%)`}
                  size="small"
                  variant="outlined"
                  color={analysisMode === 'keywords' ? 'primary' : 'secondary'}
                />
              ))}
              {Object.keys(currentKeywords).length > 8 && (
                <Chip
                  label={`+${Object.keys(currentKeywords).length - 8}`}
                  size="small"
                  color="default"
                />
              )}
            </Stack>
          </Box>
        )}

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
          disabled={!folderPath || loading || !hasCurrentKeywords}
        >
          {loading ? 'Analyse en cours...' : 'Analyser les CVs'}
        </Button>
      </Box>
    </Paper>
  );
};

export default CVAnalyzerForm;
