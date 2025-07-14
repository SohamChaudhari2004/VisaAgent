import React, { useState, useEffect, useCallback } from "react";
import useWebSocket from "../hooks/useWebSocket";
import { useAudio } from "../hooks/useAudio";
import { useInterview } from "../context/InterviewContext";
import Recorder from "./Recorder";

const InterviewSession = () => {
  const { interviewState, dispatch } = useInterview();
  const {
    visaType,
    voice,
    questionCount,
    currentQuestion,
    questionNumber,
    currentAnswer,
  } = interviewState;

  const [isRecording, setIsRecording] = useState(false);
  const [connectionError, setConnectionError] = useState(null);
  const [isInitializing, setIsInitializing] = useState(true);

  const { playAudio } = useAudio();

  // Initialize WebSocket
  const {
    isConnected,
    message,
    audioData,
    error,
    sendBinary,
    startInterview,
    disconnect,
  } = useWebSocket();

  // Handle WebSocket errors
  useEffect(() => {
    if (error) {
      setConnectionError(`Connection error: ${error}`);
      dispatch({ type: "SET_ERROR", payload: error });
    } else {
      setConnectionError(null);
    }
  }, [error, dispatch]);

  // Start interview when component mounts
  useEffect(() => {
    if (isInitializing) {
      console.log("Starting interview with config:", {
        visaType,
        voice,
        questionCount,
      });

      // Add a small delay before connecting to ensure component is fully mounted
      const timer = setTimeout(() => {
        startInterview({
          visaType,
          voice,
          questionCount,
        });
        setIsInitializing(false);
      }, 300);

      return () => clearTimeout(timer);
    }

    // Only disconnect on unmount, not on every effect re-run
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    isInitializing,
    visaType,
    voice,
    questionCount,
    startInterview,
    // disconnect,  <-- REMOVE disconnect from deps to avoid calling it on every render
  ]);

  // Cleanup on unmount only
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  // Handle incoming audio
  useEffect(() => {
    if (audioData) {
      // Fix: Always play audio as soon as it arrives
      playAudio(audioData);
    }
  }, [audioData, playAudio]);

  // Handle incoming messages
  useEffect(() => {
    if (!message) return;

    console.log("Received message:", message);

    if (message.cmd === "start_record") {
      console.log("Starting recording...");
      setIsRecording(true);
    } else if (message.cmd === "ack") {
      console.log("Received answer acknowledgment");
      setIsRecording(false);
    } else if (message.cmd === "error") {
      console.error("Server error:", message.message);
      setConnectionError(message.message);
    }
  }, [message, dispatch]);

  // Listen for global recording events
  useEffect(() => {
    const handleStartRecording = () => {
      console.log("Start recording event received");
      setIsRecording(true);
    };

    window.addEventListener("startRecording", handleStartRecording);

    return () => {
      window.removeEventListener("startRecording", handleStartRecording);
    };
  }, []);

  // Calculate progress percentage
  const progressPercentage =
    questionCount > 0 ? (questionNumber / questionCount) * 100 : 0;

  // Handle audio chunk from recorder
  const handleAudioChunk = useCallback(
    (chunk) => {
      if (isConnected && chunk) {
        console.log("Sending audio chunk...");
        // Convert Blob to ArrayBuffer and send
        const reader = new FileReader();
        reader.onloadend = () => {
          sendBinary(reader.result);
        };
        reader.readAsArrayBuffer(chunk);
      }
    },
    [isConnected, sendBinary]
  );

  // Handle when recording stops
  const handleStopRecording = useCallback(() => {
    console.log("Recording stopped");
    setIsRecording(false);
  }, []);

  return (
    <div className="interview-container">
      {connectionError && (
        <div className="error-message">
          <p>{connectionError}</p>
          <button
            onClick={() => {
              setConnectionError(null);
              setIsInitializing(true);
            }}
          >
            Try Again
          </button>
        </div>
      )}

      <div className="interview-status">
        <div className="connection-status">
          Connection:{" "}
          <span className={isConnected ? "connected" : "disconnected"}>
            {isConnected ? "Connected" : "Disconnected"}
          </span>
        </div>

        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${progressPercentage}%` }}
          ></div>
        </div>
        <div className="question-counter">
          Question {questionNumber} of {questionCount}
        </div>
      </div>

      {currentQuestion && (
        <div className="question-box">
          <h3>Question:</h3>
          <p>{currentQuestion}</p>
        </div>
      )}

      <Recorder
        isActive={isRecording}
        onAudioChunk={handleAudioChunk}
        onStopRecording={handleStopRecording}
      />

      {currentAnswer && (
        <div className="answer-box">
          <h3>Your Answer:</h3>
          <p>{currentAnswer}</p>
        </div>
      )}
    </div>
  );
};

export default InterviewSession;
