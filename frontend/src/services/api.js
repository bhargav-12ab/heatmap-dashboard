/**
 * API service for communicating with FastAPI backend.
 * Handles all HTTP requests and error management.
 */
import axios from 'axios';

// Base URL for the FastAPI backend
// Use /api for production, localhost:8001 for development
const API_BASE_URL = import.meta.env.DEV ? 'http://localhost:8001' : '/api';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 second timeout
});

/**
 * Fetch the list of all available indices.
 * 
 * @returns {Promise<string[]>} Array of index names
 * @throws {Error} If the request fails
 */
export const fetchIndices = async () => {
  try {
    const response = await apiClient.get('/indices');
    return response.data.indices;
  } catch (error) {
    console.error('Error fetching indices:', error);
    throw new Error(
      error.response?.data?.detail || 
      'Failed to fetch indices. Please ensure the backend server is running.'
    );
  }
};

/**
 * Fetch heatmap data for a specific index.
 * 
 * @param {string} indexName - Name of the index to fetch heatmap for
 * @param {string} forwardPeriod - Optional forward period ('1M', '3M', '6M', '1Y', '2Y', '3Y', '4Y')
 * @returns {Promise<Object>} Heatmap data with structure: { index, heatmap }
 * @throws {Error} If the request fails
 */
export const fetchHeatmap = async (indexName, forwardPeriod = null) => {
  try {
    const params = forwardPeriod ? { forward_period: forwardPeriod } : {};
    const response = await apiClient.get(`/heatmap/${encodeURIComponent(indexName)}`, { params });
    return response.data;
  } catch (error) {
    console.error(`Error fetching heatmap for ${indexName}:`, error);
    throw new Error(
      error.response?.data?.detail || 
      `Failed to fetch heatmap for ${indexName}. Please try again.`
    );
  }
};

export default {
  fetchIndices,
  fetchHeatmap,
};
