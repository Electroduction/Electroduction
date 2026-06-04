// Central API config — reads VITE_API_URL env var, falls back to localhost for dev
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
