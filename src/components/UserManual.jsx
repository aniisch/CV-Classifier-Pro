import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Divider,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';

const UserManual = ({ open, onClose }) => {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { maxHeight: '85vh' }
      }}
    >
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <HelpOutlineIcon color="primary" />
          <Typography variant="h6">Guide d'utilisation</Typography>
        </Box>
        <IconButton onClick={onClose} size="small">
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers sx={{ p: 3 }}>
        {/* Section 1: Creer un Projet */}
        <Typography variant="h6" color="primary" gutterBottom>
          1. Creer un Projet
        </Typography>
        <Typography paragraph>
          Sur l'ecran d'accueil, cliquez sur <strong>"Nouveau Projet"</strong>,
          donnez un nom a votre projet (ex: "Recrutement Developpeur Python"),
          ajoutez une description optionnelle, puis cliquez sur <strong>"Creer"</strong>.
        </Typography>

        <Divider sx={{ my: 2 }} />

        {/* Section 2: Configurer les Mots-cles */}
        <Typography variant="h6" color="primary" gutterBottom>
          2. Configurer les Mots-cles
        </Typography>
        <Typography paragraph>
          Apres avoir cree un projet, configurez les competences recherchees :
        </Typography>
        <Box component="ul" sx={{ pl: 2 }}>
          <li>Cliquez sur <strong>"Editer"</strong> a cote du projet</li>
          <li>Ajoutez des mots-cles avec leur ponderation (ex: Python = 30%, Django = 20%)</li>
          <li>Le total doit faire <strong>100%</strong></li>
          <li>Cliquez sur <strong>"Sauvegarder"</strong></li>
        </Box>
        <Paper variant="outlined" sx={{ p: 1.5, mt: 1, bgcolor: 'info.light', color: 'info.contrastText' }}>
          <Typography variant="body2">
            <strong>Astuce :</strong> Mettez une ponderation plus elevee pour les competences essentielles.
          </Typography>
        </Paper>

        <Divider sx={{ my: 2 }} />

        {/* Section 3: Analyser des CVs */}
        <Typography variant="h6" color="primary" gutterBottom>
          3. Analyser des CVs
        </Typography>

        <Typography variant="subtitle2" sx={{ mt: 1, fontWeight: 600 }}>
          Mode Mots-cles (Simple)
        </Typography>
        <Box component="ol" sx={{ pl: 2 }}>
          <li>Selectionnez votre projet</li>
          <li>Cliquez sur <strong>"Analyser"</strong></li>
          <li>Choisissez le dossier contenant vos CVs (format PDF)</li>
          <li>Selectionnez le mode <strong>"Mots-cles du projet"</strong></li>
          <li>Lancez l'analyse</li>
        </Box>

        <Typography variant="subtitle2" sx={{ mt: 2, fontWeight: 600 }}>
          Mode Offre d'Emploi
        </Typography>
        <Box component="ol" sx={{ pl: 2 }}>
          <li>Importez d'abord une offre d'emploi (PDF ou TXT)</li>
          <li>Les competences sont extraites automatiquement</li>
          <li>Modifiez les ponderations si necessaire</li>
          <li>Lancez l'analyse avec l'offre selectionnee</li>
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Section 4: Comprendre les Resultats */}
        <Typography variant="h6" color="primary" gutterBottom>
          4. Comprendre les Resultats
        </Typography>
        <Typography paragraph>
          Le rapport affiche le <strong>score global</strong> (pourcentage de correspondance),
          les <strong>details par competence</strong>, et le <strong>classement</strong> des CVs.
        </Typography>

        <TableContainer component={Paper} variant="outlined" sx={{ mt: 1 }}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell><strong>Score</strong></TableCell>
                <TableCell><strong>Interpretation</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              <TableRow>
                <TableCell>80-100%</TableCell>
                <TableCell sx={{ color: 'success.main' }}>Excellent candidat</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>60-79%</TableCell>
                <TableCell sx={{ color: 'info.main' }}>Bon candidat</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>40-59%</TableCell>
                <TableCell sx={{ color: 'warning.main' }}>Candidat moyen</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>0-39%</TableCell>
                <TableCell sx={{ color: 'error.main' }}>Ne correspond pas</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>

        <Divider sx={{ my: 2 }} />

        {/* Section 5: Importer une Offre */}
        <Typography variant="h6" color="primary" gutterBottom>
          5. Importer une Offre d'Emploi
        </Typography>
        <Box component="ol" sx={{ pl: 2 }}>
          <li>Cliquez sur <strong>"Importer Offre"</strong> dans votre projet</li>
          <li>Selectionnez un fichier PDF ou TXT</li>
          <li>Les competences techniques sont detectees automatiquement</li>
          <li>Ajustez les ponderations selon l'importance</li>
          <li>Utilisez cette offre pour analyser les CVs</li>
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Section 6: Historique */}
        <Typography variant="h6" color="primary" gutterBottom>
          6. Historique
        </Typography>
        <Typography paragraph>
          Toutes vos analyses sont sauvegardees. Allez dans <strong>"Historique"</strong> pour
          consulter les analyses passees, exporter les rapports ou supprimer les anciennes analyses.
        </Typography>

        <Divider sx={{ my: 2 }} />

        {/* Support */}
        <Typography variant="h6" color="primary" gutterBottom>
          Support
        </Typography>
        <Box component="ul" sx={{ pl: 2 }}>
          <li>Verifiez que vos CVs sont au format PDF</li>
          <li>Assurez-vous que le dossier contient des fichiers</li>
          <li>Redemarrez l'application si necessaire</li>
        </Box>

        <Box sx={{ mt: 3, textAlign: 'center' }}>
          <Typography variant="caption" color="text.secondary">
            CV Classifier Pro - Version 2.1.0
          </Typography>
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} variant="contained">
          Fermer
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default UserManual;
