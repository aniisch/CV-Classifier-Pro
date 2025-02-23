import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Paper,
  Typography,
  IconButton,
  Tooltip,
  Collapse,
  Alert,
  Stack,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import HistoryIcon from '@mui/icons-material/History';
import RefreshIcon from '@mui/icons-material/Refresh';
import ErrorIcon from '@mui/icons-material/Error';
import KeyIcon from '@mui/icons-material/Key';
import DeleteIcon from '@mui/icons-material/Delete';
import ExportButton from './ExportButton';

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
      if (!response.ok) {
        throw new Error('Erreur lors du chargement de l\'historique');
      }
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
    } else {
      onAnalysisSelect(null);
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

  const handleExportPDF = async (event, analysis) => {
    event.stopPropagation();
    try {
      const response = await fetch(`/api/export/pdf/${analysis.id}`);
      if (!response.ok) {
        throw new Error('Erreur lors de l\'export PDF');
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `rapport_analyse_${analysis.id}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      setError('Erreur lors de l\'export PDF');
      console.error('Erreur:', error);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return format(date, "d MMMM yyyy 'à' HH:mm", { locale: fr });
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
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <ExportButton
                    onClick={(e) => handleExportPDF(e, analysis)}
                    disabled={loading}
                  />
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
                    label={`${keyword} (${weight.toFixed(1)}%)`}
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
  );
};

export default AnalysisHistory;
