import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Stack,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Alert,
  Tooltip,
  Divider
} from '@mui/material';
import WorkIcon from '@mui/icons-material/Work';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DescriptionIcon from '@mui/icons-material/Description';
import { apiUrl } from '../config';

const JobOfferList = ({ projectId, onAddClick, onOfferSelect, onEditClick, selectedOfferId }) => {
  const [jobOffers, setJobOffers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [offerToDelete, setOfferToDelete] = useState(null);

  const fetchJobOffers = async () => {
    if (!projectId) return;

    setLoading(true);
    try {
      const response = await fetch(apiUrl(`/api/projects/${projectId}/job-offers`));
      if (!response.ok) throw new Error('Erreur lors de la recuperation des offres');
      const data = await response.json();
      setJobOffers(data);
      setError('');
    } catch (err) {
      setError(err.message);
      setJobOffers([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobOffers();
  }, [projectId]);

  const handleDeleteClick = (e, offer) => {
    e.stopPropagation();
    setOfferToDelete(offer);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!offerToDelete) return;

    try {
      const response = await fetch(apiUrl(`/api/job-offers/${offerToDelete.id}`), {
        method: 'DELETE'
      });

      if (!response.ok) throw new Error('Erreur lors de la suppression');

      await fetchJobOffers();

      if (selectedOfferId === offerToDelete.id && onOfferSelect) {
        onOfferSelect(null);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setDeleteDialogOpen(false);
      setOfferToDelete(null);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <WorkIcon color="primary" />
          Offres d'Emploi
          <Chip
            label={`${jobOffers.length} offre${jobOffers.length > 1 ? 's' : ''}`}
            size="small"
            color="primary"
          />
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={onAddClick}
          size="small"
        >
          Importer
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {jobOffers.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 3, color: 'text.secondary' }}>
          <DescriptionIcon sx={{ fontSize: 48, opacity: 0.5, mb: 1 }} />
          <Typography>Aucune offre d'emploi importee</Typography>
          <Typography variant="body2">
            Importez une offre pour analyser les CVs en fonction de ses requirements
          </Typography>
        </Box>
      ) : (
        <List>
          {jobOffers.map((offer, index) => (
            <React.Fragment key={offer.id}>
              {index > 0 && <Divider />}
              <ListItem
                button
                onClick={() => onOfferSelect && onOfferSelect(offer)}
                selected={selectedOfferId === offer.id}
                sx={{
                  borderRadius: 1,
                  '&.Mui-selected': {
                    backgroundColor: 'primary.light',
                    '&:hover': {
                      backgroundColor: 'primary.light'
                    }
                  }
                }}
              >
                <ListItemText
                  primary={
                    <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                      {offer.filename}
                    </Typography>
                  }
                  secondary={
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="caption" color="text.secondary" display="block">
                        Importe le {formatDate(offer.created_at)}
                      </Typography>
                      <Stack direction="row" spacing={0.5} flexWrap="wrap" sx={{ mt: 0.5, gap: 0.5 }}>
                        {offer.requirements && Object.keys(offer.requirements).slice(0, 5).map(kw => (
                          <Chip
                            key={kw}
                            label={kw}
                            size="small"
                            variant="outlined"
                            color="primary"
                          />
                        ))}
                        {offer.requirements && Object.keys(offer.requirements).length > 5 && (
                          <Chip
                            label={`+${Object.keys(offer.requirements).length - 5}`}
                            size="small"
                            color="default"
                          />
                        )}
                      </Stack>
                    </Box>
                  }
                />
                <ListItemSecondaryAction>
                  <Tooltip title="Modifier les ponderations">
                    <IconButton
                      color="primary"
                      onClick={(e) => {
                        e.stopPropagation();
                        onEditClick && onEditClick(offer);
                      }}
                      sx={{ mr: 1 }}
                    >
                      <EditIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Supprimer cette offre">
                    <IconButton
                      edge="end"
                      color="error"
                      onClick={(e) => handleDeleteClick(e, offer)}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Tooltip>
                </ListItemSecondaryAction>
              </ListItem>
            </React.Fragment>
          ))}
        </List>
      )}

      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Confirmer la suppression</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Etes-vous sur de vouloir supprimer l'offre "{offerToDelete?.filename}" ?
            Cette action est irreversible.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Annuler</Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            Supprimer
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
};

export default JobOfferList;
