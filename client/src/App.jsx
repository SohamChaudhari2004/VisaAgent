import React from "react";
import "./App.css";
import Header from "./components/Header";
import { useInterview } from "./context/InterviewContext";
import InterviewSetup from "./components/InterviewSetup";
import InterviewForm from "./components/InterviewForm";
import InterviewSession from "./components/InterviewSession";
import Feedback from "./components/Feedback";
import ConnectionStatus from "./components/ConnectionStatus";

function App() {
  const { interviewState, dispatch } = useInterview();
  const { status, error } = interviewState;

  const handleStartInterview = (config) => {
    console.log("Starting interview with config:", config);
    dispatch({
      type: "START_INTERVIEW",
      payload: config,
    });
  };

  const handleReset = () => {
    console.log("Resetting interview");
    dispatch({ type: "RESET_INTERVIEW" });
  };

  return (
    <div className="app-container">
      <ConnectionStatus />

      <Header />

      {error && (
        <div className="error-banner">
          <p>{error}</p>
          <button
            onClick={() => dispatch({ type: "SET_ERROR", payload: null })}
          >
            Dismiss
          </button>
        </div>
      )}

      <main>
        {status === "setup" && (
          <>
            <InterviewSetup />
            <InterviewForm onStartInterview={handleStartInterview} />
          </>
        )}

        {status === "interviewing" && <InterviewSession />}

        {status === "completed" && <Feedback onReset={handleReset} />}
      </main>

      <footer>
        <p>
          © {new Date().getFullYear()} SRVISA - Audio-based Visa Interview
          Training
        </p>
      </footer>
    </div>
  );
}

export default App;
