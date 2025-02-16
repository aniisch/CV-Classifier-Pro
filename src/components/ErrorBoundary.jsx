import React from 'react';
import { Box, Paper, Typography, Button } from '@mui/material';
import ErrorIcon from '@mui/icons-material/Error';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false,
      error: null,
      errorInfo: null
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({
      error,
      errorInfo
    });
    
    // Ici, vous pourriez envoyer l'erreur à un service de monitoring
    console.error('Error caught by boundary:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
    // Recharger l'application
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '100vh',
            p: 3
          }}
        >
          <Paper
            elevation={3}
            sx={{
              p: 4,
              maxWidth: 600,
              width: '100%',
              textAlign: 'center'
            }}
          >
            <ErrorIcon 
              color="error" 
              sx={{ fontSize: 60, mb: 2 }} 
            />
            
            <Typography variant="h5" gutterBottom color="error">
              Oups ! Une erreur s'est produite
            </Typography>
            
            <Typography variant="body1" color="text.secondary" paragraph>
              {this.state.error?.message || "L'application a rencontré une erreur inattendue."}
            </Typography>
            
            {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
              <Paper
                sx={{
                  p: 2,
                  mb: 3,
                  bgcolor: 'grey.100',
                  maxHeight: 200,
                  overflow: 'auto',
                  textAlign: 'left'
                }}
              >
                <Typography variant="caption" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                  {this.state.errorInfo.componentStack}
                </Typography>
              </Paper>
            )}
            
            <Button
              variant="contained"
              color="primary"
              onClick={this.handleReset}
              sx={{ mt: 2 }}
            >
              Réessayer
            </Button>
          </Paper>
        </Box>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
