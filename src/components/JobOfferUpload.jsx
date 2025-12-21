import React, { useState } from 'react';
import { apiUrl } from '../config';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Chip,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Tooltip
} from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import FolderOpenIcon from '@mui/icons-material/FolderOpen';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import DeleteIcon from '@mui/icons-material/Delete';

const JobOfferUpload = ({ projectId, onUploadComplete, onBack }) => {
  const [filePath, setFilePath] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [uploadedOffer, setUploadedOffer] = useState(null);

  const handleBrowse = async () => {
    // En mode Electron, utiliser le dialog natif
    if (window.electronAPI?.selectFile) {
      try {
        const selectedPath = await window.electronAPI.selectFile({
          filters: [
            { name: 'Documents', extensions: ['pdf', 'txt'] }
          ]
        });
        if (selectedPath) setFilePath(selectedPath);
      } catch (err) {
        console.error('Erreur selection fichier:', err);
      }
    } else {
      setError('Tapez le chemin du fichier manuellement');
    }
  };

  const handleUpload = async () => {
    if (!filePath) {
      setError('Veuillez specifier le chemin du fichier');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch(apiUrl(`/api/projects/${projectId}/job-offers`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_path: filePath })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erreur lors de l\'upload');
      }

      const data = await response.json();
      setUploadedOffer(data);
      setSuccess(`Offre "${data.filename}" uploadee avec succes! ${Object.keys(data.requirements).length} requirements detectes.`);

      if (onUploadComplete) {
        onUploadComplete(data);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getTotalWeight = () => {
    if (!uploadedOffer?.requirements) return 0;
    return Object.values(uploadedOffer.requirements).reduce((sum, w) => sum + w, 0);
  };

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <UploadFileIcon color="primary" />
        Importer une Offre d'Emploi
      </Typography>

      <Box sx={{ mt: 2 }}>
        <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
          <TextField
            fullWidth
            label="Chemin du fichier (PDF ou TXT)"
            value={filePath}
            onChange={(e) => setFilePath(e.target.value)}
            placeholder="C:\Users\...\offre.pdf"
            InputProps={{
              startAdornment: <FolderOpenIcon color="action" sx={{ mr: 1 }} />
            }}
            disabled={loading}
          />
          <Button
            variant="outlined"
            onClick={handleBrowse}
            disabled={loading}
            sx={{ whiteSpace: 'nowrap' }}
          >
            Parcourir
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mb: 2 }} icon={<CheckCircleIcon />}>
            {success}
          </Alert>
        )}

        <Button
          variant="contained"
          onClick={handleUpload}
          disabled={!filePath || loading}
          startIcon={loading ? <CircularProgress size={20} /> : <UploadFileIcon />}
          fullWidth
          sx={{ mb: 3 }}
        >
          {loading ? 'Analyse en cours...' : 'Uploader et Analyser'}
        </Button>

        {uploadedOffer && uploadedOffer.requirements && Object.keys(uploadedOffer.requirements).length > 0 && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
              Requirements detectes ({Object.keys(uploadedOffer.requirements).length})
            </Typography>

            <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Competence</TableCell>
                    <TableCell align="right">Ponderation</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {Object.entries(uploadedOffer.requirements)
                    .sort((a, b) => b[1] - a[1])
                    .map(([keyword, weight]) => (
                      <TableRow key={keyword}>
                        <TableCell>
                          <Chip label={keyword} size="small" color="primary" variant="outlined" />
                        </TableCell>
                        <TableCell align="right">{weight}%</TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="body2" color="text.secondary">
              Total: {getTotalWeight().toFixed(1)}%
            </Typography>
          </Box>
        )}

        {uploadedOffer && (!uploadedOffer.requirements || Object.keys(uploadedOffer.requirements).length === 0) && (
          <Alert severity="warning" sx={{ mt: 2 }}>
            Aucun requirement technique detecte dans ce fichier. Verifiez le contenu du document.
          </Alert>
        )}

        <Box sx={{ display: 'flex', gap: 2, mt: 3 }}>
          <Button variant="outlined" onClick={onBack}>
            Retour
          </Button>
        </Box>
      </Box>
    </Paper>
  );
};

export default JobOfferUpload;
