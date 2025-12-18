import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Paper,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Collapse,
  IconButton,
  Chip,
  Stack,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  Tooltip
} from '@mui/material';
import HistoryIcon from '@mui/icons-material/History';
import RefreshIcon from '@mui/icons-material/Refresh';
import ErrorIcon from '@mui/icons-material/Error';
import KeyIcon from '@mui/icons-material/Key';
import DeleteIcon from '@mui/icons-material/Delete';

const AnalysisHistory = ({ projectId, onAnalysisSelect }) => {
  const [analyses, setAnalyses] = useState([]);
  const [selectedAnalysis, setSelectedAnalysis] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [analysisToDelete, setAnalysisToDelete] = useState(null);

  const fetchAnalyses = async () => {
    if (!projectId) return;

    setLoading(true);
    try {
      const response = await fetch(`/api/projects/${projectId}/analyses`);
      if (!response.ok) {
        // Phase 1.3 n'est pas encore implémenté, on ignore silencieusement
        setAnalyses([]);
        return;
      }
      const data = await response.json();
      setAnalyses(data || []);
      setError('');
    } catch (error) {
      // Phase 1.3 pas encore implémenté
      setAnalyses([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalyses();
  }, [projectId]);

  const formatDate = (dateString) => {
    const options = { 
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    };
    return new Date(dateString).toLocaleDateString('fr-FR', options);
  };

  const handleAnalysisChange = (event) => {
    const analysisId = event.target.value;
    setSelectedAnalysis(analysisId);
    const analysis = analyses.find(a => a.id === analysisId);
    if (analysis && onAnalysisSelect) {
      onAnalysisSelect(analysis.report, analysisId);
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
        method: 'DELETE'
      });
      
      if (!response.ok) {
        throw new Error('Erreur lors de la suppression');
      }
      
      await fetchAnalyses();
      if (selectedAnalysis === analysisToDelete.id) {
        setSelectedAnalysis('');
        if (onAnalysisSelect) {
          onAnalysisSelect(null);
        }
      }
    } catch (error) {
      setError('Erreur lors de la suppression');
      console.error('Erreur:', error);
    } finally {
      setDeleteDialogOpen(false);
      setAnalysisToDelete(null);
    }
  };

  return (
    <>
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

        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel id="analysis-history-label">
            Sélectionner une analyse précédente
          </InputLabel>
          <Select
            labelId="analysis-history-label"
            value={selectedAnalysis}
            onChange={handleAnalysisChange}
            label="Sélectionner une analyse précédente"
            disabled={loading}
            renderValue={(selected) => {
              const analysis = analyses.find(a => a.id === selected);
              if (!analysis) return <em>Choisir une analyse</em>;
              return (
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>
                    Analyse du {formatDate(analysis.date)}
                  </Typography>
                  <Stack 
                    direction="row" 
                    spacing={1} 
                    flexWrap="wrap"
                    sx={{ gap: 0.5 }}
                  >
                    <KeyIcon fontSize="small" sx={{ opacity: 0.7 }} />
                    {Object.entries(analysis.keywords).map(([keyword, weight]) => (
                      <Chip
                        key={keyword}
                        label={`${keyword} (${weight}%)`}
                        size="small"
                        variant="outlined"
                        color="primary"
                      />
                    ))}
                  </Stack>
                </Box>
              );
            }}
          >
            <MenuItem value="">
              <em>Choisir une analyse</em>
            </MenuItem>
            {analyses.map((analysis) => (
              <MenuItem 
                key={analysis.id} 
                value={analysis.id}
                sx={{ display: 'block', py: 1 }}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>
                    Analyse du {formatDate(analysis.date)}
                  </Typography>
                  <Tooltip title="Supprimer cette analyse">
                    <IconButton
                      size="small"
                      color="error"
                      onClick={(e) => handleDeleteClick(e, analysis)}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
                <Stack 
                  direction="row" 
                  spacing={1} 
                  flexWrap="wrap"
                  sx={{ gap: 0.5 }}
                >
                  <KeyIcon fontSize="small" sx={{ opacity: 0.7 }} />
                  {Object.entries(analysis.keywords).map(([keyword, weight]) => (
                    <Chip
                      key={keyword}
                      label={`${keyword} (${weight}%)`}
                      size="small"
                      variant="outlined"
                      color="primary"
                    />
                  ))}
                </Stack>
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
              Êtes-vous sûr de vouloir supprimer cette analyse ?
              Cette action est irréversible.
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
    </>
  );
};

export default AnalysisHistory;
