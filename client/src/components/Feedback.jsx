import React from 'react';
import { useInterview } from '../context/InterviewContext';

const Feedback = ({ onReset }) => {
  const { interviewState } = useInterview();
  const { metrics, feedback, transcript } = interviewState;

  // Calculate overall score
  const calculateOverallScore = () => {
    if (!metrics) return 0;

    const scores = Object.values(metrics);
    return scores.reduce((sum, score) => sum + score, 0) / scores.length;
  };

  const overallScore = calculateOverallScore();
  const formattedScore = overallScore.toFixed(1);

  const renderScoreBar = (score, label) => {
    if (!metrics) return null;

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
      <h2>Interview Feedback</h2>

      {metrics ? (
        <>
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
            <p>{feedback || 'No feedback available.'}</p>
          </div>

          {transcript && transcript.length > 0 && (
            <div className="interview-log">
              <h3>Interview Transcript</h3>
              <div className="log-entries">
                {transcript.map((entry, index) => (
                  <div key={index} className="log-entry">
                    <div className="log-question">
                      <strong>Q:</strong> {entry.question}
                    </div>
                    <div className="log-answer">
                      <strong>A:</strong> {entry.answer}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <button className="reset-button" onClick={onReset}>
            Start New Interview
          </button>
        </>
      ) : (
        <div className="loading-feedback">
          <p>Generating your feedback...</p>
          <button className="reset-button" onClick={onReset}>
            Start New Interview
          </button>
        </div>
      )}
    </div>
  );
};

export default Feedback;
