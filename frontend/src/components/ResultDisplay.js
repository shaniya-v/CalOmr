import React from 'react';

const ResultDisplay = ({ result }) => {
  if (!result) return null;

  const getSourceBadge = (source) => {
    if (source === 'rag_database') {
      return <span className="badge badge-cache">⚡ Cached</span>;
    } else if (source === 'groq_solved') {
      return <span className="badge badge-ai">🤖 AI Solved</span>;
    }
    return <span className="badge badge-success">✓ Solved</span>;
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 90) return '#4caf50';
    if (confidence >= 70) return '#87ceeb';
    return '#ff9800';
  };

  return (
    <div className="result">
      <div style={{ textAlign: 'center', marginBottom: '20px' }}>
        {getSourceBadge(result.source)}
      </div>

      <div className="result-answer">
        Answer: <span style={{ color: '#4a90e2' }}>{result.answer}</span>
      </div>

      <div className="result-info">
        <div className="info-item">
          <label>Confidence</label>
          <span style={{ color: getConfidenceColor(result.confidence) }}>
            {result.confidence}%
          </span>
        </div>

        <div className="info-item">
          <label>Subject</label>
          <span>{result.question_data?.subject?.toUpperCase() || 'N/A'}</span>
        </div>

        <div className="info-item">
          <label>Topic</label>
          <span>{result.question_data?.topic || 'N/A'}</span>
        </div>

        <div className="info-item">
          <label>Difficulty</label>
          <span>{result.question_data?.difficulty || 'N/A'}</span>
        </div>

        <div className="info-item">
          <label>Time Taken</label>
          <span>{result.total_time_seconds?.toFixed(2)}s</span>
        </div>

        <div className="info-item">
          <label>Method</label>
          <span>{result.source === 'rag_database' ? 'Database' : 'AI Model'}</span>
        </div>
      </div>

      {result.question_data?.question_text && (
        <div className="result-reasoning">
          <h3>📝 Question</h3>
          <pre>{result.question_data.question_text}</pre>
        </div>
      )}

      {result.question_data?.equations && result.question_data.equations.length > 0 && (
        <div className="result-reasoning">
          <h3>📐 Equations</h3>
          {result.question_data.equations.map((eq, idx) => (
            <pre key={idx}>• {eq}</pre>
          ))}
        </div>
      )}

      {result.question_data?.options && (
        <div className="result-reasoning">
          <h3>🔘 Options</h3>
          {Object.entries(result.question_data.options).map(([key, value]) => (
            <pre key={key} style={{ 
              fontWeight: key === result.answer ? 'bold' : 'normal',
              color: key === result.answer ? '#4a90e2' : '#555',
              background: key === result.answer ? 'rgba(135, 206, 235, 0.1)' : 'transparent',
              padding: '5px',
              borderRadius: '5px',
              margin: '5px 0'
            }}>
              {key === result.answer ? '✓ ' : '  '}{key}: {value}
            </pre>
          ))}
        </div>
      )}

      {result.reasoning && result.source !== 'rag_database' && (
        <div className="result-reasoning">
          <h3>💡 Detailed Reasoning</h3>
          <pre>{result.reasoning}</pre>
        </div>
      )}
    </div>
  );
};

export default ResultDisplay;
