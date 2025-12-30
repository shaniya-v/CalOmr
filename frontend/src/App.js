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
  const [multiResults, setMultiResults] = useState(null);
  const [error, setError] = useState(null);
  const [verify, setVerify] = useState(false);

  const handleFileSelect = (file) => {
    setSelectedFile(file);
    setResult(null);
    setMultiResults(null);
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
    setMultiResults(null);
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
    setMultiResults(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await axios.post(`${API_URL}/solve?verify=${verify}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 60000,
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

  const handleSolveAll = async () => {
    if (!selectedFile) {
      alert('Please select an image first');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setMultiResults(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await axios.post(`${API_URL}/solve-all`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 180000,
      });

      console.log('Received response:', response.data);
      setMultiResults(response.data);
    } catch (err) {
      console.error('Error solving questions:', err);
      console.error('Error details:', err.response?.data);
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
        <div className="header">
          <h1>🎓 CalOmr</h1>
          <p>AI-Powered STEM Question Solver with RAG</p>
        </div>

        <div className="main-content">
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
                    {loading ? '⏳ Solving...' : '🚀 Solve First Question'}
                  </button>
                  <button 
                    onClick={handleSolveAll} 
                    disabled={loading}
                    className="button"
                    style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
                  >
                    {loading ? '⏳ Processing...' : '🎯 Solve ALL Questions'}
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
                <p>Analyzing questions with AI...</p>
                <p style={{ fontSize: '0.9em', opacity: 0.7 }}>
                  This may take a few seconds
                </p>
              </div>
            )}

            {error && (
              <div className="error">
                ❌ {error}
              </div>
            )}
          </div>

          <div className="card">
            <h2>
              {multiResults ? `✅ All Results (${multiResults.total_questions} questions)` : 
               result ? '✅ Result' : '📊 Statistics'}
            </h2>
            
            {multiResults ? (
              <div>
                <div style={{ marginBottom: '20px', padding: '15px', background: 'rgba(135, 206, 235, 0.1)', borderRadius: '10px' }}>
                  <p><strong>Total Questions:</strong> {multiResults.total_questions || 0}</p>
                  <p><strong>Total Time:</strong> {multiResults.total_time_seconds?.toFixed(2) || 0}s</p>
                  <p><strong>Avg per Question:</strong> {multiResults.total_questions > 0 ? (multiResults.total_time_seconds / multiResults.total_questions).toFixed(2) : 0}s</p>
                </div>
                
                {multiResults.questions?.map((q, idx) => (
                  <div key={idx} style={{
                    marginBottom: '20px',
                    padding: '15px',
                    border: '2px solid #87CEEB',
                    borderRadius: '10px',
                    background: 'white'
                  }}>
                    <h3>Question {q.question_data?.question_number || idx + 1}</h3>
                    <p><strong>Subject:</strong> {q.question_data?.subject || 'Unknown'}</p>
                    <p><strong>Question:</strong> {q.question_data?.question_text?.substring(0, 150)}...</p>
                    <div style={{
                      marginTop: '10px',
                      padding: '10px',
                      background: '#f0f8ff',
                      borderRadius: '8px'
                    }}>
                      <p><strong>Answer:</strong> <span style={{ fontSize: '1.5em', color: '#4a90e2' }}>{q.answer}</span></p>
                      <p><strong>Confidence:</strong> {q.confidence}%</p>
                      <p><strong>Method:</strong> {q.source}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : result ? (
              <ResultDisplay result={result} />
            ) : (
              <Statistics />
            )}
          </div>
        </div>

        <div className="card" style={{ textAlign: 'center' }}>
          <p style={{ color: '#4a90e2', fontSize: '1.1em' }}>
            ⚡ Powered by <strong>Groq AI</strong> + <strong>Supabase RAG</strong> + <strong>Web Search</strong>
          </p>
          <p style={{ color: '#666', fontSize: '0.9em', marginTop: '10px' }}>
            Multi-question solving • Web search integration • Smart caching
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;
