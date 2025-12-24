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
  Divider,
  Slider,
  Checkbox,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Collapse
} from '@mui/material';
import FolderOpenIcon from '@mui/icons-material/FolderOpen';
import SendIcon from '@mui/icons-material/Send';
import WorkIcon from '@mui/icons-material/Work';
import KeyIcon from '@mui/icons-material/Key';
import PsychologyIcon from '@mui/icons-material/Psychology';
import FilterListIcon from '@mui/icons-material/FilterList';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';

const CVAnalyzerForm = ({ project, jobOffers = [], onAnalysisComplete, onAnalysisStart }) => {
  const [folderPath, setFolderPath] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [analysisMode, setAnalysisMode] = useState('keywords'); // 'keywords', 'joboffer' ou 'llm'
  const [selectedJobOfferId, setSelectedJobOfferId] = useState('');
  const [llmConfigured, setLlmConfigured] = useState(false);

  // Etats pour la selection de CVs (mode LLM)
  const [cvSelectionMode, setCvSelectionMode] = useState('all'); // 'all', 'topN', 'manual'
  const [previousAnalyses, setPreviousAnalyses] = useState([]);
  const [selectedAnalysisId, setSelectedAnalysisId] = useState('');
  const [analysisResults, setAnalysisResults] = useState([]); // CVs de l'analyse selectionnee
  const [topNCount, setTopNCount] = useState(3);
  const [selectedCvs, setSelectedCvs] = useState([]); // Pour selection manuelle
  const [showCvList, setShowCvList] = useState(false);

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

  // Charger les analyses precedentes du projet
  useEffect(() => {
    const loadPreviousAnalyses = async () => {
      if (!project?.id) return;
      try {
        const response = await fetch(apiUrl(`/api/projects/${project.id}/analyses`));
        if (response.ok) {
          const data = await response.json();
          // Filtrer pour garder uniquement les analyses non-LLM (mots-cles ou offre)
          const nonLlmAnalyses = data.filter(a => {
            const kw = a.keywords || {};
            return kw.mode !== 'llm';
          });
          setPreviousAnalyses(nonLlmAnalyses);
        }
      } catch (err) {
        console.error('Erreur chargement analyses:', err);
      }
    };
    loadPreviousAnalyses();
  }, [project?.id]);

  // Parser les resultats quand une analyse est selectionnee
  useEffect(() => {
    if (!selectedAnalysisId) {
      setAnalysisResults([]);
      setSelectedCvs([]);
      return;
    }

    const analysis = previousAnalyses.find(a => a.id === parseInt(selectedAnalysisId));
    if (!analysis) return;

    // Extraire les CVs du rapport markdown
    // Le format est: | 1 | filename.pdf | XX% | ...
    const report = analysis.report || '';
    const cvRegex = /\|\s*\d+\s*\|\s*([^|]+\.pdf)\s*\|\s*([\d.]+)%?\s*\|/gi;
    const cvs = [];
    let match;

    while ((match = cvRegex.exec(report)) !== null) {
      cvs.push({
        filename: match[1].trim(),
        score: parseFloat(match[2])
      });
    }

    // Trier par score decroissant
    cvs.sort((a, b) => b.score - a.score);
    setAnalysisResults(cvs);

    // Pre-selectionner le top N
    if (cvSelectionMode === 'topN') {
      setSelectedCvs(cvs.slice(0, topNCount).map(c => c.filename));
    } else if (cvSelectionMode === 'manual') {
      setSelectedCvs([]);
    }

    // Mettre a jour le folder_path depuis l'analyse
    if (analysis.folder_path && !folderPath) {
      setFolderPath(analysis.folder_path);
    }
  }, [selectedAnalysisId, previousAnalyses, cvSelectionMode, topNCount]);

  // Mettre a jour la selection quand topN change
  useEffect(() => {
    if (cvSelectionMode === 'topN' && analysisResults.length > 0) {
      setSelectedCvs(analysisResults.slice(0, topNCount).map(c => c.filename));
    }
  }, [topNCount, cvSelectionMode, analysisResults]);

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
        body = {
          folder_path: folderPath,
          job_offer_id: selectedJobOfferId,
          // Ajouter cv_files si mode selection (pas 'all')
          ...(cvSelectionMode !== 'all' && selectedCvs.length > 0 && {
            cv_files: selectedCvs,
            source_analysis_id: selectedAnalysisId ? parseInt(selectedAnalysisId) : null
          })
        };
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

        {/* Selection des CVs pour mode LLM */}
        {analysisMode === 'llm' && selectedJobOfferId && (
          <Box sx={{ mb: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
            <Typography variant="subtitle2" sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
              <FilterListIcon fontSize="small" />
              Source des CVs
            </Typography>

            <RadioGroup
              value={cvSelectionMode}
              onChange={(e) => {
                setCvSelectionMode(e.target.value);
                if (e.target.value === 'all') {
                  setSelectedCvs([]);
                  setSelectedAnalysisId('');
                }
              }}
              sx={{ mb: 1 }}
            >
              <FormControlLabel
                value="all"
                control={<Radio size="small" />}
                label="Tous les CVs du dossier"
              />
              <FormControlLabel
                value="topN"
                control={<Radio size="small" />}
                label="Top N d'une analyse précédente"
                disabled={previousAnalyses.length === 0}
              />
              <FormControlLabel
                value="manual"
                control={<Radio size="small" />}
                label="Sélection manuelle"
                disabled={previousAnalyses.length === 0}
              />
            </RadioGroup>

            {/* Selection de l'analyse precedente */}
            {(cvSelectionMode === 'topN' || cvSelectionMode === 'manual') && (
              <Box sx={{ ml: 3 }}>
                <FormControl fullWidth size="small" sx={{ mb: 1 }}>
                  <InputLabel>Analyse source</InputLabel>
                  <Select
                    value={selectedAnalysisId}
                    onChange={(e) => setSelectedAnalysisId(e.target.value)}
                    label="Analyse source"
                  >
                    {previousAnalyses.map((analysis) => (
                      <MenuItem key={analysis.id} value={analysis.id}>
                        {new Date(analysis.date).toLocaleDateString('fr-FR')} - {Object.keys(analysis.keywords || {}).length} critères
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                {/* Slider pour Top N */}
                {cvSelectionMode === 'topN' && selectedAnalysisId && analysisResults.length > 0 && (
                  <Box sx={{ px: 1 }}>
                    <Typography variant="body2" gutterBottom>
                      Nombre de CVs: <strong>{topNCount}</strong> sur {analysisResults.length}
                    </Typography>
                    <Slider
                      value={topNCount}
                      onChange={(e, val) => setTopNCount(val)}
                      min={1}
                      max={Math.min(10, analysisResults.length)}
                      marks
                      valueLabelDisplay="auto"
                      size="small"
                    />
                    <Typography variant="caption" color="text.secondary">
                      CVs sélectionnés: {selectedCvs.join(', ')}
                    </Typography>
                  </Box>
                )}

                {/* Liste avec checkboxes pour selection manuelle */}
                {cvSelectionMode === 'manual' && selectedAnalysisId && analysisResults.length > 0 && (
                  <Box>
                    <Button
                      size="small"
                      onClick={() => setShowCvList(!showCvList)}
                      endIcon={showCvList ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                      sx={{ mb: 1 }}
                    >
                      {selectedCvs.length} CV(s) sélectionné(s)
                    </Button>
                    <Collapse in={showCvList}>
                      <List dense sx={{ maxHeight: 200, overflow: 'auto', bgcolor: 'white', borderRadius: 1 }}>
                        {analysisResults.map((cv) => (
                          <ListItem key={cv.filename} disablePadding>
                            <ListItemButton
                              onClick={() => {
                                setSelectedCvs(prev =>
                                  prev.includes(cv.filename)
                                    ? prev.filter(f => f !== cv.filename)
                                    : [...prev, cv.filename]
                                );
                              }}
                              dense
                            >
                              <ListItemIcon sx={{ minWidth: 36 }}>
                                <Checkbox
                                  edge="start"
                                  checked={selectedCvs.includes(cv.filename)}
                                  size="small"
                                />
                              </ListItemIcon>
                              <ListItemText
                                primary={cv.filename}
                                secondary={`Score: ${cv.score.toFixed(1)}%`}
                              />
                            </ListItemButton>
                          </ListItem>
                        ))}
                      </List>
                    </Collapse>
                  </Box>
                )}

                {/* Message si pas d'analyse selectionnee */}
                {!selectedAnalysisId && (
                  <Typography variant="caption" color="text.secondary">
                    Sélectionnez une analyse précédente pour voir les CVs disponibles
                  </Typography>
                )}
              </Box>
            )}

            {/* Message si pas d'analyses precedentes */}
            {previousAnalyses.length === 0 && cvSelectionMode !== 'all' && (
              <Alert severity="info" sx={{ mt: 1 }}>
                Aucune analyse précédente. Lancez d'abord une analyse par mots-clés ou offre.
              </Alert>
            )}
          </Box>
        )}

        {/* Info mode LLM */}
        {analysisMode === 'llm' && selectedJobOfferId && (
          <Alert severity="info" sx={{ mb: 2 }}>
            {cvSelectionMode === 'all'
              ? "L'IA va analyser tous les CVs du dossier."
              : `L'IA va analyser ${selectedCvs.length} CV(s) sélectionné(s).`
            }
            {' '}Cette analyse peut prendre quelques minutes.
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
            (analysisMode === 'llm' && (
              !selectedJobOfferId ||
              !llmConfigured ||
              (cvSelectionMode !== 'all' && selectedCvs.length === 0)
            ))
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
