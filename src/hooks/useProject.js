import { useState, useEffect, useCallback } from 'react';
import { apiUrl } from '../config';

export function useProject() {
  const [currentProject, setCurrentProject] = useState(null);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Récupérer tous les projets
  const fetchProjects = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(apiUrl('/api/projects'));
      if (!response.ok) throw new Error('Erreur lors de la récupération des projets');
      const data = await response.json();
      setProjects(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Erreur fetchProjects:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Récupérer un projet spécifique
  const fetchProject = useCallback(async (projectId) => {
    try {
      setLoading(true);
      const response = await fetch(apiUrl(`/api/projects/${projectId}`));
      if (!response.ok) throw new Error('Projet non trouvé');
      const data = await response.json();
      setCurrentProject(data);
      setError(null);
      return data;
    } catch (err) {
      setError(err.message);
      console.error('Erreur fetchProject:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  // Créer un nouveau projet
  const createProject = useCallback(async (name, description = '', keywords = {}) => {
    try {
      setLoading(true);
      const response = await fetch(apiUrl('/api/projects'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, description, keywords })
      });
      if (!response.ok) throw new Error('Erreur lors de la création du projet');
      const newProject = await response.json();
      setCurrentProject(newProject);
      setProjects([newProject, ...projects]);
      setError(null);
      return newProject;
    } catch (err) {
      setError(err.message);
      console.error('Erreur createProject:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, [projects]);

  // Mettre à jour un projet
  const updateProject = useCallback(async (projectId, updates) => {
    try {
      setLoading(true);
      const response = await fetch(apiUrl(`/api/projects/${projectId}`), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      });
      if (!response.ok) throw new Error('Erreur lors de la mise à jour du projet');
      const updated = await response.json();
      setCurrentProject(updated);
      setProjects(projects.map(p => p.id === projectId ? updated : p));
      setError(null);
      return updated;
    } catch (err) {
      setError(err.message);
      console.error('Erreur updateProject:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, [projects]);

  // Supprimer un projet
  const deleteProject = useCallback(async (projectId) => {
    try {
      setLoading(true);
      const response = await fetch(apiUrl(`/api/projects/${projectId}`), {
        method: 'DELETE'
      });
      if (!response.ok) throw new Error('Erreur lors de la suppression du projet');
      setProjects(projects.filter(p => p.id !== projectId));
      if (currentProject?.id === projectId) {
        setCurrentProject(null);
      }
      setError(null);
      return true;
    } catch (err) {
      setError(err.message);
      console.error('Erreur deleteProject:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, [projects, currentProject]);

  // Sélectionner un projet
  const selectProject = useCallback(async (projectId) => {
    const project = await fetchProject(projectId);
    return project;
  }, [fetchProject]);

  // Charger les projets au premier rendu
  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  return {
    currentProject,
    projects,
    loading,
    error,
    fetchProjects,
    fetchProject,
    createProject,
    updateProject,
    deleteProject,
    selectProject,
    setCurrentProject
  };
}
