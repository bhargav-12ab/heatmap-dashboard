/**
 * Dashboard Page - Main page that combines index selection and heatmap display.
 */
import React, { useState, useEffect } from 'react';
import { Container, Box, Typography, Paper, FormControl, InputLabel, Select, MenuItem } from '@mui/material';
import IndexSelector from '../components/IndexSelector';
import Heatmap from '../components/Heatmap';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import { fetchIndices, fetchHeatmap } from '../services/api';

const Dashboard = () => {
  // State management
  const [indices, setIndices] = useState([]);
  const [selectedIndex, setSelectedIndex] = useState('');
  const [forwardPeriod, setForwardPeriod] = useState(null); // null means current/MoM returns
  const [heatmapData, setHeatmapData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [indicesLoading, setIndicesLoading] = useState(true);

  // Load indices on component mount
  useEffect(() => {
    loadIndices();
  }, []);

  /**
   * Load the list of available indices from the API.
   */
  const loadIndices = async () => {
    setIndicesLoading(true);
    setError(null);

    try {
      const data = await fetchIndices();
      setIndices(data);
      setIndicesLoading(false);
    } catch (err) {
      setError(err.message);
      setIndicesLoading(false);
    }
  };

  /**
   * Handle index selection and load heatmap data.
   */
  const handleSelectIndex = async (indexName) => {
    setSelectedIndex(indexName);

    if (!indexName) {
      setHeatmapData(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await fetchHeatmap(indexName, forwardPeriod);
      setHeatmapData(data);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setHeatmapData(null);
      setLoading(false);
    }
  };

  /**
   * Handle forward period selection.
   */
  const handleForwardPeriodChange = async (period) => {
    setForwardPeriod(period);
    
    // Reload data with new period if an index is selected
    if (selectedIndex) {
      setLoading(true);
      setError(null);
      
      try {
        const data = await fetchHeatmap(selectedIndex, period);
        setHeatmapData(data);
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setHeatmapData(null);
        setLoading(false);
      }
    }
  };

  /**
   * Retry loading indices on error.
   */
  const handleRetry = () => {
    if (indicesLoading || loading) return;
    if (!indices.length) {
      loadIndices();
    } else if (selectedIndex) {
      handleSelectIndex(selectedIndex);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%)',
        py: 4,
      }}
    >
      <Container maxWidth="xl">
        {/* Header */}
        <Paper
          elevation={0}
          sx={{
            p: 4,
            mb: 4,
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white',
            textAlign: 'center',
            borderRadius: 3,
          }}
        >
          <Typography variant="h3" fontWeight="700" gutterBottom>
            Financial Heatmap Dashboard
          </Typography>
          <Typography variant="h6" fontWeight="400" sx={{ opacity: 0.95 }}>
            {forwardPeriod ? `Forward Returns Analysis (${forwardPeriod})` : 'Month-over-Month Returns Analysis'}
          </Typography>
        </Paper>

        {/* Main Content */}
        <Paper
          elevation={0}
          sx={{
            p: 4,
            backgroundColor: 'white',
            borderRadius: 3,
            border: '1px solid #e0e0e0',
            boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
          }}
        >
          {/* Index Selector */}
          {indicesLoading ? (
            <LoadingSpinner message="Loading indices..." />
          ) : error && !indices.length ? (
            <ErrorMessage message={error} onRetry={handleRetry} />
          ) : (
            <>
              <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
                <Box sx={{ flex: 1 }}>
                  <IndexSelector
                    indices={indices}
                    selectedIndex={selectedIndex}
                    onSelectIndex={handleSelectIndex}
                    disabled={loading}
                  />
                </Box>
                <Box sx={{ minWidth: 200 }}>
                  <FormControl fullWidth>
                    <InputLabel>Return Period</InputLabel>
                    <Select
                      value={forwardPeriod || 'current'}
                      onChange={(e) => handleForwardPeriodChange(e.target.value === 'current' ? null : e.target.value)}
                      label="Return Period"
                      disabled={loading}
                    >
                      <MenuItem value="current">Current (MoM)</MenuItem>
                      <MenuItem value="1M">1 Month Forward</MenuItem>
                      <MenuItem value="3M">3 Months Forward</MenuItem>
                      <MenuItem value="6M">6 Months Forward</MenuItem>
                      <MenuItem value="1Y">1 Year Forward</MenuItem>
                      <MenuItem value="2Y">2 Years Forward</MenuItem>
                      <MenuItem value="3Y">3 Years Forward</MenuItem>
                      <MenuItem value="4Y">4 Years Forward</MenuItem>
                    </Select>
                  </FormControl>
                </Box>
              </Box>

              {/* Heatmap Display */}
              {loading && <LoadingSpinner message="Generating heatmap..." />}

              {error && selectedIndex && !loading && (
                <ErrorMessage message={error} onRetry={handleRetry} />
              )}

              {heatmapData && !loading && !error && (
                <Box sx={{ mt: 4 }}>
                  <Heatmap
                    indexName={heatmapData.index}
                    heatmapData={heatmapData.heatmap}
                    monthlyPrice={heatmapData.monthly_price}
                    monthlyProfits={heatmapData.monthly_profits}
                    avgMonthlyProfits3y={heatmapData.avg_monthly_profits_3y}
                    rankPercentile4y={heatmapData.rank_percentile_4y}
                    inverseRankPercentile={heatmapData.inverse_rank_percentile}
                    monthlyRankPercentile={heatmapData.monthly_rank_percentile}
                  />
                </Box>
              )}

              {/* Placeholder message when no index selected */}
              {!selectedIndex && !loading && !error && (
                <Box
                  sx={{
                    textAlign: 'center',
                    py: 8,
                    color: 'text.secondary',
                  }}
                >
                  <Typography variant="h5" fontWeight="500">
                    Select an index to view the heatmap
                  </Typography>
                  <Typography variant="body1" sx={{ mt: 2 }}>
                    Choose from {indices.length} available indices
                  </Typography>
                </Box>
              )}
            </>
          )}
        </Paper>

        {/* Footer */}
        <Box sx={{ textAlign: 'center', mt: 4, color: 'text.secondary' }}>
          <Typography variant="body2">
            Data updated as of November 14, 2025 | Powered by FastAPI & React
          </Typography>
        </Box>
      </Container>
    </Box>
  );
};

export default Dashboard;
