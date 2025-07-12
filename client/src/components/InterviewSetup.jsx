import React from 'react';
import { useInterview } from '../context/InterviewContext';

const InterviewSetup = () => {
  const { interviewState, dispatch } = useInterview();
  const { visaType, voice, questionCount } = interviewState;

  const handleVisaTypeChange = (e) => {
    dispatch({ type: 'UPDATE_VISA_TYPE', payload: e.target.value });
  };

  const handleVoiceChange = (e) => {
    dispatch({ type: 'UPDATE_VOICE', payload: e.target.value });
  };

  const handleQuestionCountChange = (count) => {
    dispatch({ type: 'UPDATE_QUESTION_COUNT', payload: count });
  };

  return (
    <div className="setup-container">
      <h2>Interview Setup</h2>

      <div className="form-group">
        <label htmlFor="visa-type">Visa Type:</label>
        <select
          id="visa-type"
          value={visaType}
          onChange={handleVisaTypeChange}
        >
          <option value="tourist">Tourist</option>
          <option value="student">Student</option>
        </select>
      </div>

      <div className="form-group">
        <label htmlFor="voice">AI Voice:</label>
        <select
          id="voice"
          value={voice}
          onChange={handleVoiceChange}
        >
          <option value="VoiceA">Voice A (Female, US)</option>
          <option value="VoiceB">Voice B (Male, US)</option>
          <option value="VoiceC">Voice C (Female, UK)</option>
        </select>
      </div>

      <div className="form-group subscription-group">
        <label>Subscription Tier:</label>
        <div className="radio-options">
          <label className="radio-label">
            <input
              type="radio"
              name="subscription"
              checked={questionCount === 5}
              onChange={() => handleQuestionCountChange(5)}
            />
            Free (5 Questions)
          </label>
          <label className="radio-label">
            <input
              type="radio"
              name="subscription"
              checked={questionCount === 10}
              onChange={() => handleQuestionCountChange(10)}
            />
            Super (10 Questions)
          </label>
          <label className="radio-label">
            <input
              type="radio"
              name="subscription"
              checked={questionCount === 15}
              onChange={() => handleQuestionCountChange(15)}
            />
            Premium (15 Questions)
          </label>
        </div>
      </div>

      <div className="progress-indicator">
        <div className="progress-step active">1</div>
        <div className="progress-step">2</div>
        <div className="progress-step">3</div>
      </div>
    </div>
  );
};

// export default InterviewSetup;
//       </form>
//     </div>
//   );
// };

export default InterviewSetup;
