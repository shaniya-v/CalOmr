import React, { useState, useEffect } from 'react';
import axios from 'axios';

const Statistics = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/stats');
      setStats(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to load statistics');
      console.error('Stats error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    // Refresh stats every 30 seconds
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Loading statistics...</p>
      </div>
    );
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  if (!stats) {
    return <div>No statistics available</div>;
  }

  return (
    <div>
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total Questions</div>
          <div className="stat-value">{stats.total_questions || 0}</div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Total Queries</div>
          <div className="stat-value">{stats.total_queries || 0}</div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Cache Hit Rate</div>
          <div className="stat-value">{(stats.cache_hit_rate || 0).toFixed(1)}%</div>
        </div>
      </div>

      {stats.by_subject && (
        <div className="subject-stats">
          <div className="subject-item">
            <h4>📐 Math</h4>
            <p>{stats.by_subject.math || 0}</p>
          </div>

          <div className="subject-item">
            <h4>⚛️ Physics</h4>
            <p>{stats.by_subject.physics || 0}</p>
          </div>

          <div className="subject-item">
            <h4>🧪 Chemistry</h4>
            <p>{stats.by_subject.chemistry || 0}</p>
          </div>
        </div>
      )}

      <div style={{ textAlign: 'center', marginTop: '20px' }}>
        <button onClick={fetchStats} className="button button-secondary">
          🔄 Refresh Stats
        </button>
      </div>
    </div>
  );
};

export default Statistics;
