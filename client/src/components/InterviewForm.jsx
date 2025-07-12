import React, { useState } from 'react';
import { useInterview } from '../context/InterviewContext';

const InterviewForm = ({ onStartInterview }) => {
  const { interviewState } = useInterview();
  const { visaType, voice, questionCount } = interviewState;

  const [permissionStatus, setPermissionStatus] = useState(null);

  const checkMicrophonePermission = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      // Stop tracks after permission check
      stream.getTracks().forEach(track => track.stop());
      setPermissionStatus('granted');
      return true;
    } catch (err) {
      console.error('Microphone permission error:', err);
      setPermissionStatus('denied');
      return false;
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Check microphone permission
    const hasPermission = await checkMicrophonePermission();
    if (!hasPermission) return;

    // Start interview
    onStartInterview({
      visaType,
      voice,
      questionCount
    });
  };

  return (
    <form className="setup-container" onSubmit={handleSubmit}>
      {permissionStatus === 'denied' && (
        <div className="error-message">
          Microphone access is required for the interview.
          Please allow microphone access in your browser settings.
        </div>
      )}

      <p>
        You're about to start a {visaType} visa interview with {questionCount} questions.
        The interviewer will use {voice === 'VoiceA' ? 'a female US' : voice === 'VoiceB' ? 'a male US' : 'a female UK'} voice.
      </p>

      <p>
        Please ensure you are in a quiet environment and your microphone is working.
        Speak clearly and naturally when answering questions.
      </p>

      <button
        type="submit"
        className="start-button"
      >
        Start Interview
      </button>
    </form>
  );
};

export default InterviewForm;
