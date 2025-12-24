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

        <Typography variant="subtitle2" sx={{ mt: 2, fontWeight: 600 }}>
          Mode Analyse IA (LLM)
        </Typography>
        <Box component="ol" sx={{ pl: 2 }}>
          <li>Configurez d'abord l'IA via l'icone <strong>engrenage</strong> (voir section 8)</li>
          <li>Importez une offre d'emploi (obligatoire pour l'IA)</li>
          <li>Selectionnez le mode <strong>"Analyse IA"</strong> (icone cerveau)</li>
          <li>Choisissez la source des CVs (tous, top N, ou selection manuelle)</li>
          <li>Lancez l'analyse</li>
        </Box>
        <Paper variant="outlined" sx={{ p: 1.5, mt: 1, bgcolor: 'warning.light', color: 'warning.contrastText' }}>
          <Typography variant="body2">
            <strong>Important :</strong> Pour selectionner des CVs specifiques (Top N ou manuel),
            lancez d'abord une analyse par mots-cles ou offre, puis passez en mode IA.
          </Typography>
        </Paper>

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
          <li>Cliquez sur <strong>"Importer"</strong> dans la section "Offres d'Emploi"</li>
          <li>Selectionnez un fichier PDF ou TXT</li>
          <li>Les competences techniques sont detectees automatiquement</li>
          <li>La ponderation est calculee selon la frequence d'apparition</li>
          <li>Utilisez cette offre pour analyser les CVs</li>
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Section 6: Modifier les Ponderations */}
        <Typography variant="h6" color="primary" gutterBottom>
          6. Modifier les Ponderations d'une Offre
        </Typography>
        <Typography paragraph>
          Apres avoir importe une offre, vous pouvez ajuster les ponderations :
        </Typography>
        <Box component="ol" sx={{ pl: 2 }}>
          <li>Dans la liste des offres, cliquez sur l'icone <strong>crayon</strong> (a cote de la poubelle)</li>
          <li>Modifiez les pourcentages de chaque competence</li>
          <li>Supprimez les competences non pertinentes avec l'icone <strong>poubelle</strong></li>
          <li>Assurez-vous que le total fait <strong>100%</strong></li>
          <li>Cliquez sur <strong>"Sauvegarder"</strong></li>
        </Box>
        <Paper variant="outlined" sx={{ p: 1.5, mt: 1, bgcolor: 'info.light', color: 'info.contrastText' }}>
          <Typography variant="body2">
            <strong>Note :</strong> Les competences les plus mentionnees dans l'offre ont automatiquement un poids plus eleve.
          </Typography>
        </Paper>

        <Divider sx={{ my: 2 }} />

        {/* Section 7: Historique */}
        <Typography variant="h6" color="primary" gutterBottom>
          7. Historique
        </Typography>
        <Typography paragraph>
          Toutes vos analyses sont sauvegardees. Allez dans <strong>"Historique"</strong> pour
          consulter les analyses passees, exporter les rapports ou supprimer les anciennes analyses.
        </Typography>

        <Divider sx={{ my: 2 }} />

        {/* Section 8: Configurer l'IA */}
        <Typography variant="h6" color="primary" gutterBottom>
          8. Configurer l'IA (LLM)
        </Typography>
        <Typography paragraph>
          Pour utiliser l'analyse IA, configurez d'abord le provider :
        </Typography>
        <Box component="ol" sx={{ pl: 2 }}>
          <li>Cliquez sur l'icone <strong>engrenage</strong> (en haut a droite)</li>
          <li>Choisissez un provider :
            <Box component="ul" sx={{ pl: 2, mt: 0.5 }}>
              <li><strong>Ollama (Local)</strong> : Gratuit, donnees privees</li>
              <li><strong>OpenAI</strong> : GPT-4, necessite cle API</li>
              <li><strong>Anthropic</strong> : Claude, necessite cle API</li>
            </Box>
          </li>
          <li>Selectionnez un modele</li>
          <li>Entrez votre cle API (sauf Ollama)</li>
          <li>Cliquez sur <strong>"Tester la connexion"</strong></li>
          <li>Cliquez sur <strong>"Sauvegarder"</strong></li>
        </Box>
        <Paper variant="outlined" sx={{ p: 1.5, mt: 1, bgcolor: 'success.light', color: 'success.contrastText' }}>
          <Typography variant="body2">
            <strong>Ollama (gratuit) :</strong> Telechargez sur ollama.com, puis tapez <code>ollama pull llama3.2</code> dans un terminal.
            Vos CVs restent sur votre PC !
          </Typography>
        </Paper>

        <Divider sx={{ my: 2 }} />

        {/* Section 9: Comprendre le Rapport IA */}
        <Typography variant="h6" color="primary" gutterBottom>
          9. Comprendre le Rapport IA
        </Typography>
        <Typography paragraph>
          Le rapport IA affiche un classement avec scores et recommandations :
        </Typography>

        <TableContainer component={Paper} variant="outlined" sx={{ mt: 1 }}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell><strong>Icone</strong></TableCell>
                <TableCell><strong>Signification</strong></TableCell>
                <TableCell><strong>Score</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              <TableRow>
                <TableCell>✅</TableCell>
                <TableCell sx={{ color: 'success.main' }}>Fortement recommande</TableCell>
                <TableCell>80-100</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>⚠️</TableCell>
                <TableCell sx={{ color: 'warning.main' }}>A considerer</TableCell>
                <TableCell>60-79</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>❌</TableCell>
                <TableCell sx={{ color: 'error.main' }}>Non recommande</TableCell>
                <TableCell>0-59</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>❓</TableCell>
                <TableCell sx={{ color: 'text.secondary' }}>Non evalue</TableCell>
                <TableCell>-</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>

        <Paper variant="outlined" sx={{ p: 1.5, mt: 2, bgcolor: 'grey.100' }}>
          <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>
            Pourquoi "❓ Non evalue" ?
          </Typography>
          <Typography variant="body2">
            L'IA n'a pas pu extraire un score. Causes possibles :
          </Typography>
          <Box component="ul" sx={{ pl: 2, mt: 0.5, mb: 0 }}>
            <li>CV illisible (images au lieu de texte)</li>
            <li>Reponse LLM incomplete ou interrompue</li>
            <li>Probleme de connexion / timeout</li>
          </Box>
          <Typography variant="body2" sx={{ mt: 1 }}>
            <strong>Solution :</strong> Relancez l'analyse pour ce CV, ou verifiez que le PDF contient du texte.
          </Typography>
        </Paper>

        <Divider sx={{ my: 2 }} />

        {/* Support */}
        <Typography variant="h6" color="primary" gutterBottom>
          Support
        </Typography>
        <Box component="ul" sx={{ pl: 2 }}>
          <li>Verifiez que vos CVs sont au format PDF avec texte selectionnable</li>
          <li>Assurez-vous que le dossier contient des fichiers</li>
          <li>Pour l'IA : verifiez qu'Ollama est lance ou que votre cle API est valide</li>
          <li>Redemarrez l'application si necessaire</li>
        </Box>

        <Box sx={{ mt: 3, textAlign: 'center' }}>
          <Typography variant="caption" color="text.secondary">
            CV Classifier Pro - Version 3.1.0
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
