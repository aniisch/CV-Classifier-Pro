import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  IconButton,
  Paper,
  Typography,
  Grid,
  Tooltip,
  Zoom,
  Collapse
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import FolderOpenIcon from '@mui/icons-material/FolderOpen';
import SendIcon from '@mui/icons-material/Send';

const CVAnalyzerForm = ({ onAnalysisComplete, onAnalysisStart }) => {
  const [folderPath, setFolderPath] = useState('');
  const [keywords, setKeywords] = useState([
    { keyword: '', weight: '' }
  ]);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Valider que tous les champs sont remplis
    if (!folderPath || keywords.some(k => !k.keyword || !k.weight)) {
      setError('Veuillez remplir tous les champs');
      return;
    }

    // Convertir les keywords en objet pour l'API
    const keywordsObject = {};
    keywords.forEach(k => {
      keywordsObject[k.keyword] = parseFloat(k.weight);
    });

    try {
      onAnalysisStart?.();
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          folderPath,
          keywords: keywordsObject,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erreur lors de l\'analyse');
      }

      const data = await response.json();
      onAnalysisComplete(data);
    } catch (error) {
      setError(error.message);
      onAnalysisComplete(null);
    }
  };

  const handleAddKeyword = () => {
    setKeywords([...keywords, { keyword: '', weight: '' }]);
  };

  const handleRemoveKeyword = (index) => {
    setKeywords(keywords.filter((_, i) => i !== index));
  };

  const handleKeywordChange = (index, field, value) => {
    const newKeywords = [...keywords];
    newKeywords[index][field] = value;
    setKeywords(newKeywords);
  };

  const totalWeight = keywords.reduce((sum, k) => sum + (parseFloat(k.weight) || 0), 0);
  const isWeightValid = totalWeight === 100;

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
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
        🔍 Analyse de CV
      </Typography>
      
      <Box component="form" onSubmit={handleSubmit}>
        <TextField
          fullWidth
          label="Chemin du dossier des CVs"
          value={folderPath}
          onChange={(e) => setFolderPath(e.target.value)}
          margin="normal"
          placeholder="C:\Users\username\Documents\CVs"
          InputProps={{
            startAdornment: <FolderOpenIcon color="action" sx={{ mr: 1 }} />,
          }}
          sx={{ mb: 3 }}
        />

        <Typography variant="subtitle1" sx={{ mt: 2, mb: 1, display: 'flex', alignItems: 'center' }}>
          Mots-clés et pondérations
          <Typography 
            variant="body2" 
            color={isWeightValid ? "success.main" : "error.main"}
            sx={{ ml: 2 }}
          >
            (Total: {totalWeight}%)
          </Typography>
        </Typography>

        {keywords.map((keyword, index) => (
          <Collapse in key={index}>
            <Grid container spacing={2} sx={{ mb: 1 }}>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  label="Mot-clé"
                  value={keyword.keyword}
                  onChange={(e) => handleKeywordChange(index, 'keyword', e.target.value)}
                  sx={{ mb: 1 }}
                />
              </Grid>
              <Grid item xs={5}>
                <TextField
                  fullWidth
                  label="Pondération (%)"
                  type="number"
                  value={keyword.weight}
                  onChange={(e) => handleKeywordChange(index, 'weight', e.target.value)}
                  inputProps={{ min: 0, max: 100 }}
                  error={totalWeight > 100}
                />
              </Grid>
              <Grid item xs={1} sx={{ display: 'flex', alignItems: 'center' }}>
                {keywords.length > 1 && (
                  <Tooltip title="Supprimer ce mot-clé" placement="top">
                    <IconButton 
                      onClick={() => handleRemoveKeyword(index)} 
                      color="error"
                      size="small"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Tooltip>
                )}
              </Grid>
            </Grid>
          </Collapse>
        ))}

        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
          <Tooltip title="Ajouter un nouveau mot-clé" placement="top">
            <Button
              startIcon={<AddIcon />}
              onClick={handleAddKeyword}
              variant="outlined"
              size="small"
            >
              Ajouter un mot-clé
            </Button>
          </Tooltip>

          <Zoom in={!error}>
            <Button
              type="submit"
              variant="contained"
              color="primary"
              endIcon={<SendIcon />}
              disabled={!isWeightValid || !folderPath}
            >
              Analyser les CVs
            </Button>
          </Zoom>
        </Box>

        {error && (
          <Collapse in>
            <Typography color="error" sx={{ mt: 2 }}>
              {error}
            </Typography>
          </Collapse>
        )}
      </Box>
    </Paper>
  );
};

export default CVAnalyzerForm;
