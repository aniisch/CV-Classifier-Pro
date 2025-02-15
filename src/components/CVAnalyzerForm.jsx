import React, { useState } from 'react';
import {
  Box,
  Button,
  TextField,
  Typography,
  IconButton,
  Grid,
  Alert,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';

function CVAnalyzerForm({ onAnalysisComplete }) {
  const [folderPath, setFolderPath] = useState('');
  const [keywords, setKeywords] = useState([{ keyword: '', weight: '' }]);
  const [error, setError] = useState('');

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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validation
    const totalWeight = keywords.reduce((sum, k) => sum + Number(k.weight), 0);
    if (totalWeight !== 100) {
      setError('La somme des pondérations doit être égale à 100%');
      return;
    }

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          folderPath,
          keywords: Object.fromEntries(
            keywords.map(k => [k.keyword, Number(k.weight)])
          ),
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || 'Une erreur est survenue');
      }

      onAnalysisComplete(data.report);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit}>
      <TextField
        fullWidth
        label="Chemin du dossier des CVs"
        value={folderPath}
        onChange={(e) => setFolderPath(e.target.value)}
        margin="normal"
        required
      />

      <Typography variant="h6" sx={{ mt: 3, mb: 2 }}>
        Mots-clés et pondérations
      </Typography>

      {keywords.map((k, index) => (
        <Grid container spacing={2} key={index} sx={{ mb: 2 }}>
          <Grid item xs={5}>
            <TextField
              fullWidth
              label="Mot-clé"
              value={k.keyword}
              onChange={(e) => handleKeywordChange(index, 'keyword', e.target.value)}
              required
            />
          </Grid>
          <Grid item xs={5}>
            <TextField
              fullWidth
              label="Pondération (%)"
              type="number"
              value={k.weight}
              onChange={(e) => handleKeywordChange(index, 'weight', e.target.value)}
              required
              inputProps={{ min: 0, max: 100 }}
            />
          </Grid>
          <Grid item xs={2}>
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
        sx={{ mb: 3 }}
      >
        Ajouter un mot-clé
      </Button>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Button
        type="submit"
        variant="contained"
        color="primary"
        fullWidth
        size="large"
      >
        Analyser les CVs
      </Button>
    </Box>
  );
}

export default CVAnalyzerForm;
