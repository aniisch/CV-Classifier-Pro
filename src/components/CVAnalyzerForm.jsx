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
import PsychologyIcon from '@mui/icons-material/Psychology';

const CVAnalyzerForm = ({ project, jobOffers = [], onAnalysisComplete, onAnalysisStart }) => {
  const [folderPath, setFolderPath] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [analysisMode, setAnalysisMode] = useState('keywords'); // 'keywords', 'joboffer' ou 'llm'
  const [selectedJobOfferId, setSelectedJobOfferId] = useState('');
  const [llmConfigured, setLlmConfigured] = useState(false);

  // Verifier si LLM est configure
  useEffect(() => {
    const checkLLMConfig = async () => {
      try {
        const response = await fetch(apiUrl('/api/llm-settings'));
        if (response.ok) {
          const data = await response.json();
          // LLM configure si provider est set et (ollama OU api_key present)
          setLlmConfigured(data.provider && (data.provider === 'ollama' || data.api_key));
        }
      } catch (err) {
        console.error('Erreur verification LLM:', err);
      }
    };
    checkLLMConfig();
  }, []);

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

    if (analysisMode === 'llm' && !selectedJobOfferId) {
      setError('Veuillez selectionner une offre d\'emploi pour l\'analyse IA');
      return;
    }

    try {
      setLoading(true);
      onAnalysisStart?.();

      let url;
      let body;

      if (analysisMode === 'keywords') {
        url = apiUrl(`/api/projects/${project.id}/analyze`);
        body = { folder_path: folderPath };
      } else if (analysisMode === 'joboffer') {
        url = apiUrl(`/api/projects/${project.id}/analyze-offer/${selectedJobOfferId}`);
        body = { folder_path: folderPath };
      } else if (analysisMode === 'llm') {
        url = apiUrl(`/api/projects/${project.id}/analyze-llm`);
        body = { folder_path: folderPath, job_offer_id: selectedJobOfferId };
      }

      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
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
            <FormControlLabel
              value="llm"
              control={<Radio />}
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <PsychologyIcon fontSize="small" />
                  Analyse IA
                  <Chip label="LLM" size="small" color="success" />
                </Box>
              }
              disabled={!hasJobOffers || !llmConfigured}
            />
          </RadioGroup>
        </FormControl>

        {/* Info si LLM non configure */}
        {analysisMode === 'llm' && !llmConfigured && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            LLM non configure. Allez dans les parametres (engrenage) pour configurer.
          </Alert>
        )}

        {/* Selection de l'offre si mode joboffer ou llm */}
        {(analysisMode === 'joboffer' || analysisMode === 'llm') && (
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

        {/* Affichage des mots-cles utilises (pas pour mode LLM) */}
        {hasCurrentKeywords && analysisMode !== 'llm' && (
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

        {/* Info mode LLM */}
        {analysisMode === 'llm' && selectedJobOfferId && (
          <Alert severity="info" sx={{ mb: 2 }}>
            L'IA va analyser chaque CV en detail par rapport a l'offre d'emploi.
            Cette analyse peut prendre quelques minutes selon le nombre de CVs.
          </Alert>
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
          color={analysisMode === 'llm' ? 'success' : 'primary'}
          endIcon={analysisMode === 'llm' ? <PsychologyIcon /> : <SendIcon />}
          disabled={
            !folderPath ||
            loading ||
            (analysisMode === 'keywords' && !hasCurrentKeywords) ||
            (analysisMode === 'joboffer' && !selectedJobOfferId) ||
            (analysisMode === 'llm' && (!selectedJobOfferId || !llmConfigured))
          }
        >
          {loading
            ? (analysisMode === 'llm' ? 'Analyse IA en cours...' : 'Analyse en cours...')
            : (analysisMode === 'llm' ? 'Lancer l\'analyse IA' : 'Analyser les CVs')
          }
        </Button>
      </Box>
    </Paper>
  );
};

export default CVAnalyzerForm;
