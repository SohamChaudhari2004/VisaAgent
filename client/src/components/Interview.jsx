import React, { useEffect } from 'react';
import { useInterview } from '../context/InterviewContext';

const Interview = () => {
  const { 
    interviewState,
    setCurrentQuestion,
    addToTranscript 
  } = useInterview();
  
  const { 
    visaType, 
    questionCount,
    currentQuestion,
    questionNumber,
    transcript
  } = interviewState;
  
  // Sample questions for demo purposes
  const touristQuestions = [
    "What is the purpose of your visit?",
    "How long are you planning to stay?",
    "Where will you be staying during your visit?",
    "Have you visited our country before?",
    "Do you have any family or friends in our country?"
  ];
  
  const studentQuestions = [
    "Which university will you be attending?",
    "What course will you be studying?",
    "How will you fund your studies?",
    "What are your plans after graduation?",
    "Why did you choose to study in our country?"
  ];
  
  // Calculate progress percentage
  const progress = questionNumber / questionCount * 100;
  
  // Simulate the interview process
  useEffect(() => {
    if (questionNumber < questionCount) {
      const questions = visaType === 'tourist' ? touristQuestions : studentQuestions;
      const questionIndex = questionNumber % questions.length;
      const nextQuestion = questions[questionIndex];
      
      const timer = setTimeout(() => {
        setCurrentQuestion(nextQuestion);
      }, 1000);
      
      return () => clearTimeout(timer);
    }
  }, [questionNumber, questionCount, visaType, setCurrentQuestion, touristQuestions, studentQuestions]);
  
  // Simulate answering questions
  useEffect(() => {
    if (currentQuestion && questionNumber <= questionCount) {
      const timer = setTimeout(() => {
        addToTranscript(currentQuestion, "This is a simulated answer.");
      }, 3000);
      
      return () => clearTimeout(timer);
    }
  }, [currentQuestion, questionNumber, questionCount, addToTranscript]);

  return (
    <div className="interview-container">
      <div className="interview-status">
        <div className="progress-bar">
          <div 
            className="progress-fill" 
            style={{ width: `${progress}%` }}
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
      
      {transcript.length > 0 && transcript[transcript.length - 1] && (
        <div className="answer-box">
          <h3>Your Answer:</h3>
          <p>{transcript[transcript.length - 1].answer}</p>
        </div>
      )}
    </div>
  );
};

export default Interview;
