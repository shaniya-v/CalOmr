import React, { useState } from 'react';
import axios from 'axios';
import './App.css';
import UploadArea from './components/UploadArea';
import ResultDisplay from './components/ResultDisplay';
import Statistics from './components/Statistics';

// Use environment variable for API URL
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [verify, setVerify] = useState(false);

  const handleFileSelect = (file) => {
    setSelectedFile(file);
    setResult(null);
    setError(null);

    // Create preview URL
    const reader = new FileReader();
    reader.onloadend = () => {
      setPreviewUrl(reader.result);
    };
    reader.readAsDataURL(file);
  };

  const handleClear = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setResult(null);
    setError(null);
  };

  const handleSolve = async () => {
    if (!selectedFile) {
      alert('Please select an image first');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await axios.post(`${API_URL}/solve?verify=${verify}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 60000, // 60 second timeout
      });

      setResult(response.data);
    } catch (err) {
      console.error('Error solving question:', err);
      if (err.response) {
        setError(`Error: ${err.response.data.detail || err.response.statusText}`);
      } else if (err.request) {
        setError('No response from server. Make sure the API is running on port 8000.');
      } else {
        setError(`Error: ${err.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <div className="container">
        {/* Header */}
        <div className="header">
          <h1>🎓 CalOmr</h1>
          <p>AI-Powered STEM Question Solver with RAG</p>
        </div>

        {/* Main Content */}
        <div className="main-content">
          {/* Left Column - Upload & Solve */}
          <div className="card">
            <h2>📸 Upload Question</h2>
            
            {!previewUrl ? (
              <UploadArea 
                onFileSelect={handleFileSelect} 
                selectedFile={selectedFile} 
              />
            ) : (
              <div className="image-preview">
                <img src={previewUrl} alt="Question preview" />
                <p>{selectedFile?.name}</p>
              </div>
            )}

            {selectedFile && (
              <div>
                <div style={{ 
                  marginTop: '20px', 
                  padding: '15px', 
                  background: 'rgba(135, 206, 235, 0.1)', 
                  borderRadius: '10px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px'
                }}>
                  <input
                    type="checkbox"
                    id="verify-checkbox"
                    checked={verify}
                    onChange={(e) => setVerify(e.target.checked)}
                    style={{ width: '20px', height: '20px', cursor: 'pointer' }}
                  />
                  <label htmlFor="verify-checkbox" style={{ cursor: 'pointer', color: '#4a90e2' }}>
                    Enable answer verification (slower but more accurate)
                  </label>
                </div>

                <div className="button-group">
                  <button 
                    onClick={handleSolve} 
                    disabled={loading}
                    className="button"
                  >
                    {loading ? '⏳ Solving...' : '🚀 Solve Question'}
                  </button>
                  <button 
                    onClick={handleClear}
                    disabled={loading}
                    className="button button-secondary"
                  >
                    🗑️ Clear
                  </button>
                </div>
              </div>
            )}

            {loading && (
              <div className="loading">
                <div className="spinner"></div>
                <p>Analyzing question with AI...</p>
                <p style={{ fontSize: '0.9em', opacity: 0.7 }}>
                  This may take 2-3 seconds
                </p>
              </div>
            )}

            {error && (
              <div className="error">
                ❌ {error}
              </div>
            )}
          </div>

          {/* Right Column - Results or Stats */}
          <div className="card">
            <h2>{result ? '✅ Result' : '📊 Statistics'}</h2>
            
            {result ? (
              <ResultDisplay result={result} />
            ) : (
              <Statistics />
            )}
          </div>
        </div>

        {/* Footer Info */}
        <div className="card" style={{ textAlign: 'center' }}>
          <p style={{ color: '#4a90e2', fontSize: '1.1em' }}>
            ⚡ Powered by <strong>Groq AI</strong> + <strong>Supabase RAG</strong>
          </p>
          <p style={{ color: '#666', fontSize: '0.9em', marginTop: '10px' }}>
            Ultra-fast question solving • 92%+ accuracy • Smart caching
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;
