import { useState, useCallback } from 'react';
import { apiUrl } from '../config';

export function useJobOffer() {
  const [jobOffers, setJobOffers] = useState([]);
  const [currentJobOffer, setCurrentJobOffer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Recuperer toutes les offres d'un projet
  const fetchJobOffers = useCallback(async (projectId) => {
    if (!projectId) return;

    try {
      setLoading(true);
      const response = await fetch(apiUrl(`/api/projects/${projectId}/job-offers`));
      if (!response.ok) throw new Error('Erreur lors de la recuperation des offres');
      const data = await response.json();
      setJobOffers(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Erreur fetchJobOffers:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Recuperer une offre specifique
  const fetchJobOffer = useCallback(async (offerId) => {
    try {
      setLoading(true);
      const response = await fetch(apiUrl(`/api/job-offers/${offerId}`));
      if (!response.ok) throw new Error('Offre non trouvee');
      const data = await response.json();
      setCurrentJobOffer(data);
      setError(null);
      return data;
    } catch (err) {
      setError(err.message);
      console.error('Erreur fetchJobOffer:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  // Creer une nouvelle offre (upload fichier)
  const createJobOffer = useCallback(async (projectId, filePath) => {
    try {
      setLoading(true);
      const response = await fetch(apiUrl(`/api/projects/${projectId}/job-offers`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_path: filePath })
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erreur lors de la creation de l\'offre');
      }
      const newJobOffer = await response.json();
      setJobOffers(prev => [newJobOffer, ...prev]);
      setCurrentJobOffer(newJobOffer);
      setError(null);
      return newJobOffer;
    } catch (err) {
      setError(err.message);
      console.error('Erreur createJobOffer:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  // Mettre a jour les requirements d'une offre
  const updateJobOffer = useCallback(async (offerId, requirements) => {
    try {
      setLoading(true);
      const response = await fetch(apiUrl(`/api/job-offers/${offerId}`), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requirements })
      });
      if (!response.ok) throw new Error('Erreur lors de la mise a jour de l\'offre');
      const updated = await response.json();
      setCurrentJobOffer(updated);
      setJobOffers(prev => prev.map(jo => jo.id === offerId ? updated : jo));
      setError(null);
      return updated;
    } catch (err) {
      setError(err.message);
      console.error('Erreur updateJobOffer:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  // Supprimer une offre
  const deleteJobOffer = useCallback(async (offerId) => {
    try {
      setLoading(true);
      const response = await fetch(apiUrl(`/api/job-offers/${offerId}`), {
        method: 'DELETE'
      });
      if (!response.ok) throw new Error('Erreur lors de la suppression de l\'offre');
      setJobOffers(prev => prev.filter(jo => jo.id !== offerId));
      if (currentJobOffer?.id === offerId) {
        setCurrentJobOffer(null);
      }
      setError(null);
      return true;
    } catch (err) {
      setError(err.message);
      console.error('Erreur deleteJobOffer:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, [currentJobOffer]);

  // Analyser avec une offre
  const analyzeWithJobOffer = useCallback(async (projectId, offerId, folderPath) => {
    try {
      setLoading(true);
      const response = await fetch(apiUrl(`/api/projects/${projectId}/analyze-offer/${offerId}`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folder_path: folderPath })
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erreur lors de l\'analyse');
      }
      const data = await response.json();
      setError(null);
      return data;
    } catch (err) {
      setError(err.message);
      console.error('Erreur analyzeWithJobOffer:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    jobOffers,
    currentJobOffer,
    loading,
    error,
    fetchJobOffers,
    fetchJobOffer,
    createJobOffer,
    updateJobOffer,
    deleteJobOffer,
    analyzeWithJobOffer,
    setCurrentJobOffer
  };
}
