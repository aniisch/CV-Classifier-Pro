import { useState, useCallback } from 'react';

const useError = () => {
  const [error, setError] = useState(null);

  const handleError = useCallback((error) => {
    let errorMessage = "Une erreur inattendue s'est produite";
    let errorDetails = {};

    try {
      if (error.response) {
        // Erreur de l'API avec une réponse
        const { detail } = error.response.data;
        if (typeof detail === 'object' && detail.message) {
          errorMessage = detail.message;
          errorDetails = detail.details || {};
        } else {
          errorMessage = detail || errorMessage;
        }
      } else if (error.message) {
        // Erreur JavaScript standard
        errorMessage = error.message;
      }
    } catch (e) {
      console.error('Erreur lors du traitement de l\'erreur:', e);
    }

    setError({
      message: errorMessage,
      details: errorDetails,
      timestamp: new Date()
    });

    // Effacer l'erreur après 5 secondes
    setTimeout(() => {
      setError(null);
    }, 5000);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    error,
    setError: handleError,
    clearError
  };
};

export default useError;
