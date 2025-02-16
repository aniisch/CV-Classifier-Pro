import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  IconButton,
  Paper,
  Typography,
  Grid
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';

const CVAnalyzerForm = ({ onAnalysisComplete }) => {
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
      onAnalysisComplete(data); // Passer toute la réponse
    } catch (error) {
      setError(error.message);
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

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
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
        />

        <Typography variant="subtitle1" sx={{ mt: 2, mb: 1 }}>
          Mots-clés et pondérations
        </Typography>

        {keywords.map((keyword, index) => (
          <Grid container spacing={2} key={index} sx={{ mb: 1 }}>
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Mot-clé"
                value={keyword.keyword}
                onChange={(e) => handleKeywordChange(index, 'keyword', e.target.value)}
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
              />
            </Grid>
            <Grid item xs={1} sx={{ display: 'flex', alignItems: 'center' }}>
              {keywords.length > 1 && (
                <IconButton onClick={() => handleRemoveKeyword(index)} color="error">
                  <DeleteIcon />
                </IconButton>
              )}
            </Grid>
          </Grid>
        ))}

        <Button
          startIcon={<AddIcon />}
          onClick={handleAddKeyword}
          sx={{ mt: 1 }}
        >
          Ajouter un mot-clé
        </Button>

        {error && (
          <Typography color="error" sx={{ mt: 2 }}>
            {error}
          </Typography>
        )}

        <Button
          type="submit"
          variant="contained"
          color="primary"
          fullWidth
          sx={{ mt: 3 }}
        >
          Analyser les CVs
        </Button>
      </Box>
    </Paper>
  );
};

export default CVAnalyzerForm;
