import React from 'react';

const ResultsDisplay = ({ results, onReset }) => {
  if (!results || !results.metrics || !results.feedback) {
    return (
      <div className="results-container">
        <h2>No Results Available</h2>
        <button onClick={onReset}>Start New Interview</button>
      </div>
    );
  }

  const { metrics, feedback } = results;
  
  // Calculate overall score
  const scores = Object.values(metrics);
  const overallScore = scores.reduce((sum, score) => sum + score, 0) / scores.length;
  const formattedScore = overallScore.toFixed(1);
  
  const renderScoreBar = (score, label) => {
    const percentage = (score / 10) * 100;
    
    return (
      <div className="score-item">
        <span>{label}</span>
        <div className="score-bar">
          <div 
            className="score-fill" 
            style={{ width: `${percentage}%` }}
          ></div>
        </div>
        <span>{score.toFixed(1)}</span>
      </div>
    );
  };

  return (
    <div className="feedback-container">
      <h2>Your Interview Results</h2>
      
      <div className="score-overview">
        <div className="total-score">
          <div className="score-circle">
            {formattedScore}
            <span className="out-of">/10</span>
          </div>
          <p>Overall Score</p>
        </div>
        
        <div className="score-details">
          {renderScoreBar(metrics.fluency, 'Fluency')}
          {renderScoreBar(metrics.confidence, 'Confidence')}
          {renderScoreBar(metrics.contentAccuracy, 'Content')}
          {renderScoreBar(metrics.responseTime, 'Response Time')}
        </div>
      </div>
      
      <div className="feedback-text">
        <h3>Feedback</h3>
        <p>{feedback}</p>
      </div>
      
      {results.transcript && results.transcript.length > 0 && (
        <div className="interview-log">
          <h3>Interview Transcript</h3>
          <div className="log-entries">
            {results.transcript.map((entry, index) => (
              <div key={index} className="log-entry">
                <strong>Q: {entry.question}</strong>
                <p>A: {entry.answer}</p>
              </div>
            ))}
          </div>
        </div>
      )}
      
      <button className="reset-button" onClick={onReset}>
        Start New Interview
      </button>
    </div>
  );
};

export default ResultsDisplay;
