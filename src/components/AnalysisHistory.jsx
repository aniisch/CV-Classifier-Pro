import React, { useState, useEffect } from 'react';
import { 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  Box, 
  Typography,
  Paper,
  Chip,
  Tooltip,
  IconButton,
  Collapse,
  Alert,
  Stack,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button
} from '@mui/material';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import HistoryIcon from '@mui/icons-material/History';
import RefreshIcon from '@mui/icons-material/Refresh';
import ErrorIcon from '@mui/icons-material/Error';
import KeyIcon from '@mui/icons-material/Key';
import DeleteIcon from '@mui/icons-material/Delete';

const AnalysisHistory = ({ onAnalysisSelect }) => {
  const [analyses, setAnalyses] = useState([]);
  const [selectedAnalysis, setSelectedAnalysis] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [analysisToDelete, setAnalysisToDelete] = useState(null);

  const fetchAnalyses = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/analyses');
      const data = await response.json();
      setAnalyses(data);
      setError('');
    } catch (error) {
      setError('Erreur lors du chargement de l\'historique');
      console.error('Erreur:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalyses();
  }, []);

  const handleAnalysisChange = async (event) => {
    const analysisId = event.target.value;
    setSelectedAnalysis(analysisId);

    if (analysisId) {
      try {
        const response = await fetch(`/api/analyses/${analysisId}`);
        if (!response.ok) {
          throw new Error('Erreur lors du chargement de l\'analyse');
        }
        const data = await response.json();
        onAnalysisSelect(data.report);
        setError('');
      } catch (error) {
        setError('Erreur lors du chargement de l\'analyse');
        console.error('Erreur:', error);
      }
    }
  };

  const handleDeleteClick = (event, analysis) => {
    event.stopPropagation();
    setAnalysisToDelete(analysis);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!analysisToDelete) return;

    try {
      const response = await fetch(`/api/analyses/${analysisToDelete.id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Erreur lors de la suppression');
      }

      setError('');
      if (selectedAnalysis === analysisToDelete.id) {
        setSelectedAnalysis('');
        onAnalysisSelect(null);
      }
      await fetchAnalyses();
    } catch (error) {
      setError('Erreur lors de la suppression de l\'analyse');
      console.error('Erreur:', error);
    } finally {
      setDeleteDialogOpen(false);
      setAnalysisToDelete(null);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return format(date, "d MMMM yyyy 'à' HH:mm", { locale: fr });
  };

  const formatKeywords = (keywords) => {
    if (!keywords) return [];
    return Object.entries(keywords).map(([keyword, weight]) => ({
      keyword,
      weight: Math.round(weight)
    }));
  };

  return (
    <Paper 
      elevation={3} 
      sx={{ 
        p: 3, 
        mb: 3,
        transition: 'all 0.3s ease-in-out',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: '0 6px 12px rgba(0,0,0,0.1)',
        }
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Typography 
          variant="h6" 
          sx={{ 
            display: 'flex', 
            alignItems: 'center',
            gap: 1
          }}
        >
          <HistoryIcon color="primary" />
          Historique des Analyses
          <Chip 
            label={`${analyses.length} analyse${analyses.length > 1 ? 's' : ''}`}
            size="small"
            color="primary"
            sx={{ ml: 1 }}
          />
        </Typography>

        <Tooltip title="Rafraîchir l'historique">
          <IconButton 
            onClick={fetchAnalyses}
            disabled={loading}
            size="small"
            color="primary"
          >
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>

      <Collapse in={!!error}>
        <Alert 
          severity="error" 
          sx={{ mb: 2 }}
          icon={<ErrorIcon />}
        >
          {error}
        </Alert>
      </Collapse>

      <FormControl fullWidth>
        <InputLabel id="analysis-history-label">
          Sélectionner une analyse précédente
        </InputLabel>
        <Select
          labelId="analysis-history-label"
          value={selectedAnalysis}
          onChange={handleAnalysisChange}
          label="Sélectionner une analyse précédente"
          disabled={loading}
        >
          <MenuItem value="">
            <em>Choisir une analyse</em>
          </MenuItem>
          {analyses.map((analysis) => (
            <MenuItem 
              key={analysis.id} 
              value={analysis.id}
              sx={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: 1,
                py: 1
              }}
            >
              <Box sx={{ 
                display: 'flex', 
                flexDirection: 'column',
                flex: 1
              }}>
                <Box sx={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'center'
                }}>
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>
                    Analyse du {formatDate(analysis.date)}
                  </Typography>
                  <Tooltip title="Supprimer cette analyse">
                    <IconButton
                      size="small"
                      color="error"
                      onClick={(e) => handleDeleteClick(e, analysis)}
                      sx={{ 
                        opacity: 0.7,
                        '&:hover': { opacity: 1 }
                      }}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
                <Stack 
                  direction="row" 
                  spacing={1} 
                  sx={{ 
                    mt: 1,
                    flexWrap: 'wrap',
                    gap: '4px'
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <KeyIcon fontSize="small" color="action" />
                    <Typography variant="caption" color="text.secondary">
                      Mots-clés :
                    </Typography>
                  </Box>
                  {formatKeywords(analysis.keywords).map(({ keyword, weight }, index) => (
                    <Chip
                      key={index}
                      label={`${keyword} (${weight}%)`}
                      size="small"
                      variant="outlined"
                      color="primary"
                    />
                  ))}
                </Stack>
              </Box>
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>Confirmer la suppression</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Êtes-vous sûr de vouloir supprimer cette analyse ? Cette action est irréversible.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>
            Annuler
          </Button>
          <Button 
            onClick={handleDeleteConfirm} 
            color="error" 
            variant="contained"
          >
            Supprimer
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
};

export default AnalysisHistory;
