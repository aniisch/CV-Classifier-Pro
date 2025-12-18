import React, { useState, useEffect } from 'react';
import {
  Container,
  Box,
  Typography,
  Button,
  TextField,
  Card,
  Paper,
  Alert,
  CircularProgress,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid
} from '@mui/material';
import { Delete as DeleteIcon, ArrowBack as BackIcon, Add as AddIcon } from '@mui/icons-material';

function ProjectEditor({ project, onBack, onSave }) {
  const [formData, setFormData] = useState(project || {});
  const [keywords, setKeywords] = useState(project?.keywords || {});
  const [newKeyword, setNewKeyword] = useState('');
  const [newWeight, setNewWeight] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [openDeleteKeywordDialog, setOpenDeleteKeywordDialog] = useState(false);
  const [keywordToDelete, setKeywordToDelete] = useState(null);

  useEffect(() => {
    setFormData(project || {});
    setKeywords(project?.keywords || {});
  }, [project]);

  const totalWeight = Object.values(keywords).reduce((sum, w) => sum + (Number(w) || 0), 0);

  const handleProjectChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleAddKeyword = () => {
    if (!newKeyword.trim()) {
      setError('Le mot-clé ne peut pas être vide');
      return;
    }

    if (!newWeight || Number(newWeight) <= 0) {
      setError('La pondération doit être supérieure à 0');
      return;
    }

    if (keywords[newKeyword.trim()]) {
      setError('Ce mot-clé existe déjà');
      return;
    }

    setKeywords({
      ...keywords,
      [newKeyword.trim()]: Number(newWeight)
    });
    setNewKeyword('');
    setNewWeight('');
    setError(null);
  };

  const handleDeleteKeywordClick = (keyword) => {
    setKeywordToDelete(keyword);
    setOpenDeleteKeywordDialog(true);
  };

  const handleConfirmDeleteKeyword = () => {
    if (keywordToDelete) {
      const newKeywords = { ...keywords };
      delete newKeywords[keywordToDelete];
      setKeywords(newKeywords);
      setOpenDeleteKeywordDialog(false);
      setKeywordToDelete(null);
    }
  };

  const handleSaveProject = async () => {
    if (!formData.name?.trim()) {
      setError('Le nom du projet est requis');
      return;
    }

    if (totalWeight !== 100) {
      setError(`La somme des pondérations doit égaler 100% (actuellement ${totalWeight}%)`);
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(`/api/projects/${project.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: formData.name,
          description: formData.description || '',
          keywords
        })
      });

      if (!response.ok) {
        throw new Error('Erreur lors de la sauvegarde du projet');
      }

      const updatedProject = await response.json();
      setSuccess(true);
      setTimeout(() => {
        setSuccess(false);
        onSave?.(updatedProject);
      }, 1500);
    } catch (err) {
      setError(err.message);
      console.error('Erreur:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!project) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Typography>Sélectionnez un projet</Typography>
      </Container>
    );
  }

  return (
    <Box sx={{ minHeight: '100vh', background: 'linear-gradient(45deg, #f5f5f5 30%, #e3f2fd 90%)', py: 4 }}>
      <Container maxWidth="lg">
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 4 }}>
          <IconButton onClick={onBack} sx={{ mr: 2 }}>
            <BackIcon />
          </IconButton>
          <Typography variant="h4" component="h1" sx={{ fontWeight: 'bold' }}>
            Éditer le projet: {project.name}
          </Typography>
        </Box>

        {error && <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2, borderRadius: 2 }}>Projet sauvegardé avec succès</Alert>}

        <Grid container spacing={3}>
          {/* Project Information */}
          <Grid item xs={12} md={6}>
            <Paper elevation={3} sx={{ p: 3, borderRadius: 2 }}>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold', mb: 2 }}>
                Informations du projet
              </Typography>

              <TextField
                fullWidth
                label="Nom du projet"
                name="name"
                value={formData.name || ''}
                onChange={handleProjectChange}
                variant="outlined"
                margin="normal"
              />

              <TextField
                fullWidth
                label="Description"
                name="description"
                value={formData.description || ''}
                onChange={handleProjectChange}
                variant="outlined"
                multiline
                rows={4}
                margin="normal"
              />

              <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
                <Button
                  variant="contained"
                  onClick={handleSaveProject}
                  disabled={loading}
                  fullWidth
                >
                  {loading ? <CircularProgress size={24} /> : 'Sauvegarder'}
                </Button>
                <Button
                  variant="outlined"
                  onClick={onBack}
                  disabled={loading}
                  fullWidth
                >
                  Annuler
                </Button>
              </Box>
            </Paper>
          </Grid>

          {/* Keywords Management */}
          <Grid item xs={12} md={6}>
            <Paper elevation={3} sx={{ p: 3, borderRadius: 2 }}>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold', mb: 2 }}>
                Mots-clés (Total: {totalWeight}%)
              </Typography>

              {/* Add Keyword */}
              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <TextField
                  label="Mot-clé"
                  value={newKeyword}
                  onChange={(e) => setNewKeyword(e.target.value)}
                  size="small"
                  fullWidth
                  placeholder="Ex: Python"
                />
                <TextField
                  label="Poids %"
                  type="number"
                  value={newWeight}
                  onChange={(e) => setNewWeight(e.target.value)}
                  size="small"
                  inputProps={{ min: 0, max: 100 }}
                  sx={{ width: 100 }}
                />
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={handleAddKeyword}
                  sx={{ whiteSpace: 'nowrap' }}
                >
                  Ajouter
                </Button>
              </Box>

              {/* Keywords Table */}
              {Object.keys(keywords).length === 0 ? (
                <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
                  Aucun mot-clé ajouté
                </Typography>
              ) : (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow sx={{ bgcolor: 'rgba(0,0,0,0.05)' }}>
                        <TableCell>Mot-clé</TableCell>
                        <TableCell align="right">Poids</TableCell>
                        <TableCell align="right">Action</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {Object.entries(keywords).map(([keyword, weight]) => (
                        <TableRow key={keyword}>
                          <TableCell>{keyword}</TableCell>
                          <TableCell align="right">{weight}%</TableCell>
                          <TableCell align="right">
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => handleDeleteKeywordClick(keyword)}
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}

              {totalWeight !== 100 && Object.keys(keywords).length > 0 && (
                <Alert severity="warning" sx={{ mt: 2 }}>
                  La somme doit égaler 100% (actuellement {totalWeight}%)
                </Alert>
              )}
            </Paper>
          </Grid>
        </Grid>

        {/* Delete Keyword Dialog */}
        <Dialog open={openDeleteKeywordDialog} onClose={() => setOpenDeleteKeywordDialog(false)}>
          <DialogTitle>Supprimer le mot-clé ?</DialogTitle>
          <DialogContent>
            <Typography>
              Êtes-vous sûr de vouloir supprimer le mot-clé <strong>{keywordToDelete}</strong> ?
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenDeleteKeywordDialog(false)}>Annuler</Button>
            <Button onClick={handleConfirmDeleteKeyword} variant="contained" color="error">
              Supprimer
            </Button>
          </DialogActions>
        </Dialog>
      </Container>
    </Box>
  );
}

export default ProjectEditor;
