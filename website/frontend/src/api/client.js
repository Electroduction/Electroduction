import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({ baseURL: API_BASE });

export const getProjects = (category) =>
  api.get('/api/projects', { params: category ? { category } : {} }).then(r => r.data);

export const getProject = (id) =>
  api.get(`/api/projects/${id}`).then(r => r.data);

export const getStats = () =>
  api.get('/api/stats').then(r => r.data);

export const getLeaderboard = (limit = 10) =>
  api.get('/api/leaderboard', { params: { limit } }).then(r => r.data);

export const sendContact = (payload) =>
  api.post('/api/contact', payload).then(r => r.data);
