import React, { useState } from 'react';
import {
  Container,
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  CardActions,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip,
  Paper
} from '@mui/material';
import { Delete as DeleteIcon, Edit as EditIcon, Add as AddIcon } from '@mui/icons-material';
import { useProject } from '../hooks/useProject';

function HomeScreen({ onProjectSelect }) {
  const { projects, currentProject, loading, error, createProject, deleteProject } = useProject();
  const [openDialog, setOpenDialog] = useState(false);
  const [dialogMode, setDialogMode] = useState('create'); // 'create' ou 'delete'
  const [selectedProject, setSelectedProject] = useState(null);
  const [formData, setFormData] = useState({ name: '', description: '' });
  const [confirmDelete, setConfirmDelete] = useState(false);

  const handleOpenCreateDialog = () => {
    setDialogMode('create');
    setFormData({ name: '', description: '' });
    setOpenDialog(true);
  };

  const handleCreateProject = async () => {
    if (!formData.name.trim()) {
      alert('Le nom du projet est requis');
      return;
    }

    const newProject = await createProject(formData.name, formData.description);
    if (newProject) {
      setOpenDialog(false);
      setFormData({ name: '', description: '' });
    }
  };

  const handleDeleteClick = (project) => {
    setSelectedProject(project);
    setConfirmDelete(true);
  };

  const handleConfirmDelete = async () => {
    if (selectedProject) {
      const success = await deleteProject(selectedProject.id);
      if (success) {
        setConfirmDelete(false);
        setSelectedProject(null);
      }
    }
  };

  const handleProjectClick = (project) => {
    onProjectSelect(project);
  };

  return (
    <Box sx={{ minHeight: '100vh', background: 'linear-gradient(45deg, #f5f5f5 30%, #e3f2fd 90%)', py: 4 }}>
      <Container maxWidth="lg">
        {/* Header */}
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 'bold', mb: 1 }}>
            CV Classifier Pro
          </Typography>
          <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 3 }}>
            Gérez vos projets d'analyse de CV
          </Typography>
        </Box>

        {/* Error Alert */}
        {error && (
          <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>
            {error}
          </Alert>
        )}

        {/* Create Project Button */}
        <Box sx={{ mb: 4, display: 'flex', justifyContent: 'center' }}>
          <Button
            variant="contained"
            size="large"
            startIcon={<AddIcon />}
            onClick={handleOpenCreateDialog}
            disabled={loading}
          >
            Créer un projet
          </Button>
        </Box>

        {/* Projects Grid */}
        {loading && projects.length === 0 ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
            <CircularProgress />
          </Box>
        ) : projects.length === 0 ? (
          <Paper elevation={0} sx={{ p: 4, textAlign: 'center', borderRadius: 2, bgcolor: 'rgba(255,255,255,0.5)' }}>
            <Typography variant="h6" color="text.secondary">
              Aucun projet créé
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Cliquez sur "Créer un projet" pour commencer
            </Typography>
          </Paper>
        ) : (
          <Grid container spacing={3}>
            {projects.map((project) => (
              <Grid item xs={12} sm={6} md={4} key={project.id}>
                <Card
                  sx={{
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    cursor: 'pointer',
                    transition: 'transform 0.2s, boxShadow 0.2s',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: '0 8px 16px rgba(0,0,0,0.15)'
                    }
                  }}
                  onClick={() => handleProjectClick(project)}
                >
                  <CardContent sx={{ flexGrow: 1 }}>
                    <Typography variant="h6" component="div" gutterBottom sx={{ fontWeight: 'bold' }}>
                      {project.name}
                    </Typography>
                    {project.description && (
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {project.description}
                      </Typography>
                    )}
                    <Typography variant="caption" color="text.secondary">
                      {Object.keys(project.keywords || {}).length} mots-clés configurés
                    </Typography>
                    <Typography variant="caption" display="block" color="text.secondary" sx={{ mt: 1 }}>
                      Créé le {new Date(project.created_at).toLocaleDateString('fr-FR')}
                    </Typography>
                  </CardContent>
                  <CardActions sx={{ pt: 0 }}>
                    <Tooltip title="Éditer le projet">
                      <IconButton
                        size="small"
                        color="primary"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleProjectClick(project);
                        }}
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Supprimer le projet">
                      <IconButton
                        size="small"
                        color="error"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteClick(project);
                        }}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}

        {/* Create Project Dialog */}
        <Dialog open={openDialog && dialogMode === 'create'} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Créer un nouveau projet</DialogTitle>
          <DialogContent sx={{ pt: 2 }}>
            <TextField
              autoFocus
              fullWidth
              label="Nom du projet"
              variant="outlined"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="Ex: Recrutement DevOps 2025"
              sx={{ mb: 2 }}
            />
            <TextField
              fullWidth
              label="Description (optionnel)"
              variant="outlined"
              multiline
              rows={3}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Décrivez le contexte du projet..."
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenDialog(false)}>Annuler</Button>
            <Button onClick={handleCreateProject} variant="contained" disabled={loading}>
              Créer
            </Button>
          </DialogActions>
        </Dialog>

        {/* Delete Confirmation Dialog */}
        <Dialog open={confirmDelete} onClose={() => setConfirmDelete(false)}>
          <DialogTitle>Supprimer le projet ?</DialogTitle>
          <DialogContent>
            <Typography>
              Êtes-vous sûr de vouloir supprimer le projet <strong>{selectedProject?.name}</strong> ? Cette action est irréversible.
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setConfirmDelete(false)}>Annuler</Button>
            <Button onClick={handleConfirmDelete} variant="contained" color="error" disabled={loading}>
              Supprimer
            </Button>
          </DialogActions>
        </Dialog>
      </Container>
    </Box>
  );
}

export default HomeScreen;
