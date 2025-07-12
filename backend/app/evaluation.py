import logging
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional

import httpx

logger = logging.getLogger(__name__)

# Get Mistral API key from environment
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

async def evaluate_session(session_log: List[Tuple[str, str, datetime]]) -> Tuple[Dict, str]:
    """
    Score fluency, confidence, content accuracy, response time.
    
    Args:
        session_log: List of (question, answer, timestamp) tuples
    
    Returns:
        Tuple[Dict, str]: Metrics dictionary and feedback text
    """
    if not session_log:
        logger.warning("Empty session log, returning default evaluation")
        return {
            "fluency": 5.0,
            "confidence": 5.0,
            "contentAccuracy": 5.0,
            "responseTime": 5.0
        }, "No interview data available for evaluation."
    
    # Default metrics in case of API failure
    default_metrics = {
        "fluency": 7.0,
        "confidence": 6.5,
        "contentAccuracy": 7.5,
        "responseTime": 8.0
    }
    
    # Format the session log for the LLM
    formatted_log = []
    for i, (question, answer, timestamp) in enumerate(session_log):
        formatted_log.append(f"Q{i+1}: {question}\nA{i+1}: {answer}\n")
    
    interview_text = "\n".join(formatted_log)
    
    # If no API key, return default metrics
    if not MISTRAL_API_KEY:
        logger.warning("MISTRAL_API_KEY not set, using default evaluation")
        return default_metrics, generate_feedback_from_metrics(default_metrics)
    
    try:
        # Query Mistral API for evaluation
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {MISTRAL_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "mistral-small",
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are an expert visa interview evaluator. "
                                "You will analyze the interview transcript and provide scores on four criteria: "
                                "1. Fluency (how well the person expresses themselves) - score 1-10 "
                                "2. Confidence (how confident they sound) - score 1-10 "
                                "3. Content Accuracy (how well they answer the questions) - score 1-10 "
                                "4. Response Time (how quickly and efficiently they respond) - score 1-10 "
                                "Return your evaluation as JSON with these four metrics and detailed feedback."
                            )
                        },
                        {
                            "role": "user",
                            "content": f"Evaluate this visa interview transcript and provide scores and feedback:\n\n{interview_text}"
                        }
                    ],
                    "response_format": { "type": "json_object" },
                    "max_tokens": 500
                },
                timeout=15.0
            )
        
        # Process response
        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['message']['content']
            
            # Parse the JSON response
            import json
            try:
                evaluation = json.loads(content)
                
                # Extract metrics and feedback
                metrics = {
                    "fluency": float(evaluation.get("fluency", 7.0)),
                    "confidence": float(evaluation.get("confidence", 7.0)),
                    "contentAccuracy": float(evaluation.get("content_accuracy", 7.0)),
                    "responseTime": float(evaluation.get("response_time", 7.0))
                }
                
                feedback = evaluation.get("feedback", generate_feedback_from_metrics(metrics))
                
                logger.info(f"Evaluation completed with metrics: {metrics}")
                return metrics, feedback
                
            except json.JSONDecodeError:
                logger.error(f"Error parsing evaluation JSON: {content}")
                return default_metrics, generate_feedback_from_metrics(default_metrics)
        else:
            logger.error(f"Mistral API error: {response.text}")
            return default_metrics, generate_feedback_from_metrics(default_metrics)
            
    except Exception as e:
        logger.error(f"Evaluation error: {str(e)}", exc_info=True)
        return default_metrics, generate_feedback_from_metrics(default_metrics)

def generate_feedback_from_metrics(metrics: Dict) -> str:
    """Generate generic feedback based on metrics."""
    avg_score = sum(metrics.values()) / len(metrics)
    
    if avg_score >= 8.0:
        return (
            "Excellent interview performance! You communicated clearly and confidently. "
            "Your answers were relevant and well-structured. You're well-prepared for your visa interview."
        )
    elif avg_score >= 6.0:
        return (
            "Good interview performance. You answered most questions adequately, but there's room for improvement. "
            "Try to be more specific in your answers and work on expressing yourself more confidently."
        )
    else:
        return (
            "Your interview needs improvement. Focus on providing more relevant answers and practice speaking more fluently. "
            "Make sure to listen carefully to questions and take your time to formulate complete responses."
        )
