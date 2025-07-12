import React, { createContext, useContext, useReducer } from "react";

// Create the context
const InterviewContext = createContext();

// Initial state
const initialState = {
  status: "setup", // setup, interviewing, completed
  visaType: "tourist",
  voice: "VoiceA",
  questionCount: 5,
  currentQuestion: null,
  questionNumber: 0,
  currentAnswer: "",
  transcript: [],
  metrics: null,
  feedback: null,
  error: null,
};

// Reducer function
function interviewReducer(state, action) {
  switch (action.type) {
    case "START_INTERVIEW":
      return {
        ...state,
        status: "interviewing",
        visaType: action.payload.visaType,
        voice: action.payload.voice,
        questionCount: action.payload.questionCount,
        questionNumber: 0,
        transcript: [],
        currentQuestion: null,
        currentAnswer: "",
        metrics: null,
        feedback: null,
        error: null,
      };

    case "SET_QUESTION":
      return {
        ...state,
        currentQuestion: action.payload,
        questionNumber: state.questionNumber + 1,
        currentAnswer: "",
      };

    case "SET_ANSWER":
      return {
        ...state,
        currentAnswer: action.payload,
      };

    case "LOG_QA":
      return {
        ...state,
        transcript: [
          ...state.transcript,
          {
            question: state.currentQuestion,
            answer: action.payload,
            timestamp: new Date(),
          },
        ],
      };

    case "COMPLETE_INTERVIEW":
      return {
        ...state,
        status: "completed",
        metrics: action.payload.metrics,
        feedback: action.payload.feedback,
      };

    case "SET_ERROR":
      return {
        ...state,
        error: action.payload,
      };

    case "RESET_INTERVIEW":
      return initialState;

    // Add missing action types for setup
    case "UPDATE_VISA_TYPE":
      return {
        ...state,
        visaType: action.payload,
      };

    case "UPDATE_VOICE":
      return {
        ...state,
        voice: action.payload,
      };

    case "UPDATE_QUESTION_COUNT":
      return {
        ...state,
        questionCount: action.payload,
      };

    default:
      return state;
  }
}

// Provider component
export const InterviewProvider = ({ children }) => {
  const [interviewState, dispatch] = useReducer(interviewReducer, initialState);

  // Value to be provided
  const value = {
    interviewState,
    dispatch,
  };

  return (
    <InterviewContext.Provider value={value}>
      {children}
    </InterviewContext.Provider>
  );
};

// Custom hook for using the context
export const useInterview = () => {
  const context = useContext(InterviewContext);
  if (context === undefined) {
    throw new Error("useInterview must be used within an InterviewProvider");
  }
  return context;
};
