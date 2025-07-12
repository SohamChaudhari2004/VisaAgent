import React, { useEffect, useRef, useState } from "react";
import { useAudio } from "../hooks/useAudio";
import "./Recorder.css";

const Recorder = ({ isActive, onAudioChunk, onStopRecording }) => {
  const {
    isRecording,
    audioLevel,
    startRecording,
    stopRecording,
    error,
    getLatestChunk,
  } = useAudio();

  const isInitialRender = useRef(true);
  const [bars, setBars] = useState(Array(12).fill(10));

  // Start/stop recording based on active state
  useEffect(() => {
    if (isInitialRender.current) {
      isInitialRender.current = false;
      return;
    }

    if (isActive && !isRecording) {
      console.log("Recorder: Starting recording");
      startRecording();
    } else if (!isActive && isRecording) {
      console.log("Recorder: Stopping recording");
      stopRecording();
      onStopRecording?.();
    }
  }, [isActive, isRecording, startRecording, stopRecording, onStopRecording]);

  // Send audio chunks to parent component
  useEffect(() => {
    if (isRecording) {
      console.log("Recorder: Setting up audio chunk interval");
      const intervalId = setInterval(() => {
        const chunk = getLatestChunk();
        if (chunk) {
          onAudioChunk?.(chunk);
        }
      }, 100);

      return () => {
        console.log("Recorder: Clearing audio chunk interval");
        clearInterval(intervalId);
      };
    }
  }, [isRecording, getLatestChunk, onAudioChunk]);

  // Update bars for visualization based on audio level
  useEffect(() => {
    if (isRecording) {
      const newBars = Array(12)
        .fill(0)
        .map(() => {
          // Base height on audio level plus some randomness
          const base = audioLevel || 10;
          const randomFactor = Math.random() * 30;
          return Math.max(10, Math.min(100, base + randomFactor));
        });

      setBars(newBars);
    } else {
      setBars(Array(12).fill(10));
    }
  }, [isRecording, audioLevel]);

  return (
    <div className="recorder-container">
      <div className={`recording-indicator ${isRecording ? "active" : ""}`}>
        {isRecording ? "Recording your answer..." : "Ready to record"}
      </div>

      {error && <p className="error-message">{error}</p>}

      <div className="mic-visualization">
        <div className="waveform">
          {bars.map((height, i) => (
            <div
              key={i}
              className="waveform-bar"
              style={{ height: `${height}%` }}
            ></div>
          ))}
        </div>
      </div>

      {isRecording && (
        <button
          className="stop-recording-btn"
          onClick={() => {
            stopRecording();
            onStopRecording?.();
          }}
        >
          Stop Recording
        </button>
      )}
    </div>
  );
};

export default Recorder;
