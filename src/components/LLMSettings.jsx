import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Typography,
  Alert,
  CircularProgress,
  Chip,
  IconButton,
  InputAdornment,
  Divider,
  Link
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  CheckCircle,
  Error as ErrorIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { apiUrl } from '../config';

const PROVIDERS = [
  {
    id: 'ollama',
    name: 'Ollama (Local)',
    description: 'Gratuit, local, donnees privees',
    requiresApiKey: false,
    defaultModel: 'llama3.2',
    models: ['llama3.2', 'llama3.1', 'mistral', 'codellama', 'phi3']
  },
  {
    id: 'openai',
    name: 'OpenAI',
    description: 'GPT-4, rapide et fiable',
    requiresApiKey: true,
    defaultModel: 'gpt-4o-mini',
    models: ['gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo']
  },
  {
    id: 'anthropic',
    name: 'Anthropic',
    description: 'Claude, excellent raisonnement',
    requiresApiKey: true,
    defaultModel: 'claude-sonnet-4-20250514',
    models: ['claude-sonnet-4-20250514', 'claude-3-5-sonnet-20241022', 'claude-3-haiku-20240307']
  }
];

function LLMSettings({ open, onClose }) {
  const [settings, setSettings] = useState({
    provider: 'ollama',
    api_key: '',
    model: 'llama3.2',
    ollama_url: 'http://localhost:11434'
  });
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [error, setError] = useState(null);
  const [showApiKey, setShowApiKey] = useState(false);
  const [availableModels, setAvailableModels] = useState([]);

  // Charger les settings au montage
  useEffect(() => {
    if (open) {
      fetchSettings();
    }
  }, [open]);

  const fetchSettings = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(apiUrl('/api/llm-settings'));
      if (response.ok) {
        const data = await response.json();
        setSettings({
          provider: data.provider || 'ollama',
          api_key: data.api_key || '',
          model: data.model || 'llama3.2',
          ollama_url: data.ollama_url || 'http://localhost:11434'
        });
      }
    } catch (err) {
      console.error('Erreur chargement settings:', err);
      setError('Erreur lors du chargement des parametres');
    } finally {
      setLoading(false);
    }
  };

  const handleProviderChange = (event) => {
    const newProvider = event.target.value;
    const providerConfig = PROVIDERS.find(p => p.id === newProvider);
    setSettings(prev => ({
      ...prev,
      provider: newProvider,
      model: providerConfig?.defaultModel || '',
      api_key: newProvider === 'ollama' ? '' : prev.api_key
    }));
    setTestResult(null);
    setAvailableModels([]);
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      const response = await fetch(apiUrl('/api/llm-settings'), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });
      if (response.ok) {
        onClose();
      } else {
        const data = await response.json();
        setError(data.detail || 'Erreur lors de la sauvegarde');
      }
    } catch (err) {
      setError('Erreur lors de la sauvegarde');
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      // D'abord sauvegarder les settings
      await fetch(apiUrl('/api/llm-settings'), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });

      // Puis tester la connexion
      const response = await fetch(apiUrl('/api/llm-settings/test'));
      const data = await response.json();
      setTestResult(data);

      // Si Ollama, mettre a jour les modeles disponibles
      if (data.status === 'ok' && data.available_models) {
        setAvailableModels(data.available_models);
      }
    } catch (err) {
      setTestResult({ status: 'error', message: 'Erreur de connexion au serveur' });
    } finally {
      setTesting(false);
    }
  };

  const currentProvider = PROVIDERS.find(p => p.id === settings.provider);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          Configuration LLM
        </Box>
      </DialogTitle>

      <DialogContent>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 1 }}>
            {error && (
              <Alert severity="error" onClose={() => setError(null)}>
                {error}
              </Alert>
            )}

            {/* Provider Selection */}
            <FormControl fullWidth>
              <InputLabel>Provider</InputLabel>
              <Select
                value={settings.provider}
                label="Provider"
                onChange={handleProviderChange}
              >
                {PROVIDERS.map(provider => (
                  <MenuItem key={provider.id} value={provider.id}>
                    <Box>
                      <Typography variant="body1">{provider.name}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {provider.description}
                      </Typography>
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Ollama URL (only for Ollama) */}
            {settings.provider === 'ollama' && (
              <>
                <TextField
                  fullWidth
                  label="URL Ollama"
                  value={settings.ollama_url}
                  onChange={(e) => setSettings(prev => ({ ...prev, ollama_url: e.target.value }))}
                  placeholder="http://localhost:11434"
                  helperText="URL du serveur Ollama local"
                />
                <Alert severity="info" icon={<InfoIcon />}>
                  <Typography variant="body2">
                    <strong>Installation Ollama:</strong>
                  </Typography>
                  <Typography variant="body2" component="div">
                    1. Telecharger sur{' '}
                    <Link href="https://ollama.ai" target="_blank" rel="noopener">
                      ollama.ai
                    </Link>
                    <br />
                    2. Lancer: <code>ollama run llama3.2</code>
                  </Typography>
                </Alert>
              </>
            )}

            {/* API Key (for OpenAI and Anthropic) */}
            {currentProvider?.requiresApiKey && (
              <TextField
                fullWidth
                label="Cle API"
                type={showApiKey ? 'text' : 'password'}
                value={settings.api_key}
                onChange={(e) => setSettings(prev => ({ ...prev, api_key: e.target.value }))}
                placeholder={settings.provider === 'openai' ? 'sk-...' : 'sk-ant-...'}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton onClick={() => setShowApiKey(!showApiKey)} edge="end">
                        {showApiKey ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  )
                }}
              />
            )}

            {/* Model Selection */}
            <FormControl fullWidth>
              <InputLabel>Modele</InputLabel>
              <Select
                value={settings.model}
                label="Modele"
                onChange={(e) => setSettings(prev => ({ ...prev, model: e.target.value }))}
              >
                {/* Modeles predefinis */}
                {currentProvider?.models.map(model => (
                  <MenuItem key={model} value={model}>{model}</MenuItem>
                ))}
                {/* Modeles Ollama detectes */}
                {availableModels.filter(m => !currentProvider?.models.includes(m)).map(model => (
                  <MenuItem key={model} value={model}>
                    {model} <Chip label="detecte" size="small" sx={{ ml: 1 }} />
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Divider />

            {/* Test Connection */}
            <Box>
              <Button
                variant="outlined"
                onClick={handleTest}
                disabled={testing}
                startIcon={testing ? <CircularProgress size={20} /> : null}
              >
                {testing ? 'Test en cours...' : 'Tester la connexion'}
              </Button>

              {testResult && (
                <Alert
                  severity={testResult.status === 'ok' ? 'success' : 'error'}
                  icon={testResult.status === 'ok' ? <CheckCircle /> : <ErrorIcon />}
                  sx={{ mt: 2 }}
                >
                  {testResult.status === 'ok' ? (
                    <>
                      Connexion reussie!
                      {testResult.available_models && (
                        <Typography variant="body2" sx={{ mt: 1 }}>
                          Modeles disponibles: {testResult.available_models.join(', ')}
                        </Typography>
                      )}
                    </>
                  ) : (
                    testResult.message
                  )}
                </Alert>
              )}
            </Box>
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Annuler</Button>
        <Button
          variant="contained"
          onClick={handleSave}
          disabled={saving || loading}
          startIcon={saving ? <CircularProgress size={20} /> : null}
        >
          {saving ? 'Sauvegarde...' : 'Sauvegarder'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default LLMSettings;
