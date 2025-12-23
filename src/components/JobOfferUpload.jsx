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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Tooltip,
  InputAdornment
} from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import FolderOpenIcon from '@mui/icons-material/FolderOpen';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import SaveIcon from '@mui/icons-material/Save';
import CancelIcon from '@mui/icons-material/Cancel';

const JobOfferUpload = ({ projectId, onUploadComplete, onBack }) => {
  const [filePath, setFilePath] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [uploadedOffer, setUploadedOffer] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editedRequirements, setEditedRequirements] = useState({});

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
      setEditedRequirements(data.requirements || {});
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

  const handleStartEdit = () => {
    setEditedRequirements({ ...uploadedOffer.requirements });
    setIsEditing(true);
    setError('');
  };

  const handleCancelEdit = () => {
    setEditedRequirements({ ...uploadedOffer.requirements });
    setIsEditing(false);
  };

  const handleWeightChange = (keyword, value) => {
    const numValue = parseFloat(value) || 0;
    setEditedRequirements(prev => ({
      ...prev,
      [keyword]: Math.max(0, Math.min(100, numValue))
    }));
  };

  const handleDeleteKeyword = (keyword) => {
    setEditedRequirements(prev => {
      const newReqs = { ...prev };
      delete newReqs[keyword];
      return newReqs;
    });
  };

  const handleSaveRequirements = async () => {
    // Verifier que le total fait 100%
    const total = Object.values(editedRequirements).reduce((sum, w) => sum + w, 0);
    if (Math.abs(total - 100) > 0.5) {
      setError(`Le total des ponderations doit faire 100% (actuellement ${total.toFixed(1)}%)`);
      return;
    }

    setSaving(true);
    setError('');

    try {
      const response = await fetch(apiUrl(`/api/job-offers/${uploadedOffer.id}`), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requirements: editedRequirements })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erreur lors de la sauvegarde');
      }

      const data = await response.json();
      setUploadedOffer(data);
      setIsEditing(false);
      setSuccess('Ponderations mises a jour avec succes!');

      if (onUploadComplete) {
        onUploadComplete(data);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const getTotalWeight = (requirements) => {
    if (!requirements) return 0;
    return Object.values(requirements).reduce((sum, w) => sum + w, 0);
  };

  const currentRequirements = isEditing ? editedRequirements : (uploadedOffer?.requirements || {});
  const totalWeight = getTotalWeight(currentRequirements);
  const isTotalValid = Math.abs(totalWeight - 100) <= 0.5;

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

        {uploadedOffer && Object.keys(currentRequirements).length > 0 && (
          <Box sx={{ mt: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                Requirements detectes ({Object.keys(currentRequirements).length})
              </Typography>

              {!isEditing ? (
                <Tooltip title="Modifier les ponderations">
                  <Button
                    size="small"
                    startIcon={<EditIcon />}
                    onClick={handleStartEdit}
                  >
                    Modifier
                  </Button>
                </Tooltip>
              ) : (
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button
                    size="small"
                    color="error"
                    startIcon={<CancelIcon />}
                    onClick={handleCancelEdit}
                    disabled={saving}
                  >
                    Annuler
                  </Button>
                  <Button
                    size="small"
                    variant="contained"
                    color="success"
                    startIcon={saving ? <CircularProgress size={16} /> : <SaveIcon />}
                    onClick={handleSaveRequirements}
                    disabled={saving || !isTotalValid}
                  >
                    Sauvegarder
                  </Button>
                </Box>
              )}
            </Box>

            <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Competence</TableCell>
                    <TableCell align="right" sx={{ width: 150 }}>Ponderation</TableCell>
                    {isEditing && <TableCell align="center" sx={{ width: 60 }}>Action</TableCell>}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {Object.entries(currentRequirements)
                    .sort((a, b) => b[1] - a[1])
                    .map(([keyword, weight]) => (
                      <TableRow key={keyword}>
                        <TableCell>
                          <Chip label={keyword} size="small" color="primary" variant="outlined" />
                        </TableCell>
                        <TableCell align="right">
                          {isEditing ? (
                            <TextField
                              size="small"
                              type="number"
                              value={weight}
                              onChange={(e) => handleWeightChange(keyword, e.target.value)}
                              InputProps={{
                                endAdornment: <InputAdornment position="end">%</InputAdornment>,
                                inputProps: { min: 0, max: 100, step: 0.1 }
                              }}
                              sx={{ width: 100 }}
                            />
                          ) : (
                            `${weight}%`
                          )}
                        </TableCell>
                        {isEditing && (
                          <TableCell align="center">
                            <Tooltip title="Supprimer">
                              <IconButton
                                size="small"
                                color="error"
                                onClick={() => handleDeleteKeyword(keyword)}
                              >
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </TableCell>
                        )}
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            </TableContainer>

            <Typography
              variant="body2"
              color={isTotalValid ? 'text.secondary' : 'error'}
              sx={{ fontWeight: isTotalValid ? 'normal' : 'bold' }}
            >
              Total: {totalWeight.toFixed(1)}%
              {!isTotalValid && isEditing && ' (doit faire 100%)'}
            </Typography>
          </Box>
        )}

        {uploadedOffer && Object.keys(currentRequirements).length === 0 && (
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
