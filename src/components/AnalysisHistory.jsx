import React, { useState, useEffect } from 'react';
import { 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  Box, 
  Typography,
  Paper
} from '@mui/material';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

const AnalysisHistory = ({ onAnalysisSelect }) => {
  const [analyses, setAnalyses] = useState([]);
  const [selectedAnalysis, setSelectedAnalysis] = useState('');

  // Charger l'historique des analyses
  useEffect(() => {
    const fetchAnalyses = async () => {
      try {
        const response = await fetch('/api/analyses');
        const data = await response.json();
        setAnalyses(data);
      } catch (error) {
        console.error('Erreur lors du chargement de l\'historique:', error);
      }
    };
    fetchAnalyses();
  }, []);

  // Gérer la sélection d'une analyse
  const handleAnalysisChange = async (event) => {
    const analysisId = event.target.value;
    setSelectedAnalysis(analysisId);

    if (analysisId) {
      try {
        const response = await fetch(`/api/analyses/${analysisId}`);
        const data = await response.json();
        onAnalysisSelect(data.report);
      } catch (error) {
        console.error('Erreur lors du chargement de l\'analyse:', error);
      }
    }
  };

  // Formater la date pour l'affichage
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return format(date, "d MMMM yyyy 'à' HH:mm", { locale: fr });
  };

  return (
    <Paper elevation={3} sx={{ p: 2, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        📋 Historique des Analyses
      </Typography>
      <FormControl fullWidth>
        <InputLabel id="analysis-history-label">
          Sélectionner une analyse précédente
        </InputLabel>
        <Select
          labelId="analysis-history-label"
          value={selectedAnalysis}
          onChange={handleAnalysisChange}
          label="Sélectionner une analyse précédente"
        >
          <MenuItem value="">
            <em>Choisir une analyse</em>
          </MenuItem>
          {analyses.map((analysis) => (
            <MenuItem key={analysis.id} value={analysis.id}>
              Analyse du {formatDate(analysis.date)}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    </Paper>
  );
};

export default AnalysisHistory;
