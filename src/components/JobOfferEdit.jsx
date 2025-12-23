import React, { useState, useEffect } from 'react';
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
import EditIcon from '@mui/icons-material/Edit';
import SaveIcon from '@mui/icons-material/Save';
import DeleteIcon from '@mui/icons-material/Delete';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

const JobOfferEdit = ({ jobOffer, onSave, onBack }) => {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [requirements, setRequirements] = useState({});

  useEffect(() => {
    if (jobOffer?.requirements) {
      setRequirements({ ...jobOffer.requirements });
    }
  }, [jobOffer]);

  const handleWeightChange = (keyword, value) => {
    const numValue = parseFloat(value) || 0;
    setRequirements(prev => ({
      ...prev,
      [keyword]: Math.max(0, Math.min(100, numValue))
    }));
  };

  const handleDeleteKeyword = (keyword) => {
    setRequirements(prev => {
      const newReqs = { ...prev };
      delete newReqs[keyword];
      return newReqs;
    });
  };

  const handleSave = async () => {
    const total = Object.values(requirements).reduce((sum, w) => sum + w, 0);
    if (Math.abs(total - 100) > 0.5) {
      setError(`Le total des ponderations doit faire 100% (actuellement ${total.toFixed(1)}%)`);
      return;
    }

    setSaving(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch(apiUrl(`/api/job-offers/${jobOffer.id}`), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requirements })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erreur lors de la sauvegarde');
      }

      const data = await response.json();
      setSuccess('Ponderations mises a jour avec succes!');

      if (onSave) {
        onSave(data);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const getTotalWeight = () => {
    return Object.values(requirements).reduce((sum, w) => sum + w, 0);
  };

  const totalWeight = getTotalWeight();
  const isTotalValid = Math.abs(totalWeight - 100) <= 0.5;

  if (!jobOffer) {
    return null;
  }

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <EditIcon color="primary" />
        Modifier les ponderations - {jobOffer.filename}
      </Typography>

      <Box sx={{ mt: 2 }}>
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

        {Object.keys(requirements).length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
              Requirements ({Object.keys(requirements).length})
            </Typography>

            <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Competence</TableCell>
                    <TableCell align="right" sx={{ width: 150 }}>Ponderation</TableCell>
                    <TableCell align="center" sx={{ width: 60 }}>Action</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {Object.entries(requirements)
                    .sort((a, b) => b[1] - a[1])
                    .map(([keyword, weight]) => (
                      <TableRow key={keyword}>
                        <TableCell>
                          <Chip label={keyword} size="small" color="primary" variant="outlined" />
                        </TableCell>
                        <TableCell align="right">
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
                        </TableCell>
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
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            </TableContainer>

            <Typography
              variant="body2"
              color={isTotalValid ? 'text.secondary' : 'error'}
              sx={{ fontWeight: isTotalValid ? 'normal' : 'bold', mb: 2 }}
            >
              Total: {totalWeight.toFixed(1)}%
              {!isTotalValid && ' (doit faire 100%)'}
            </Typography>
          </Box>
        )}

        <Box sx={{ display: 'flex', gap: 2, mt: 3 }}>
          <Button variant="outlined" onClick={onBack}>
            Retour
          </Button>
          <Button
            variant="contained"
            color="success"
            startIcon={saving ? <CircularProgress size={16} /> : <SaveIcon />}
            onClick={handleSave}
            disabled={saving || !isTotalValid}
          >
            Sauvegarder
          </Button>
        </Box>
      </Box>
    </Paper>
  );
};

export default JobOfferEdit;
