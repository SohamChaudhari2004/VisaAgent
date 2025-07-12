import logging
import os
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime

# LangChain imports
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory

# AutoGen imports
import autogen
from autogen import Agent, UserProxyAgent, AssistantAgent, GroupChat, GroupChatManager

from .rag import retrieve_question_from_chroma, SAMPLE_QUESTIONS

# Configure logging
logger = logging.getLogger(__name__)

# Get API keys from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

class InterviewAgent:
    """LangChain and AutoGen-based agent for conducting visa interviews."""
    
    def __init__(self, visa_type: str, question_count: int):
        self.visa_type = visa_type
        self.question_count = question_count
        self.questions_asked = 0
        self.conversation_history = []
        self.current_question = None
        
        # Initialize LangChain components
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Initialize language models
        self.llm = ChatOpenAI(
            temperature=0.7,
            model_name=MODEL_NAME,
            api_key=OPENAI_API_KEY
        )
        
        # Set up the AutoGen agents configuration
        self._setup_autogen_agents()
    
    def _setup_autogen_agents(self):
        """Set up AutoGen agents for the interview process."""
        # Configure LLM config for AutoGen
        llm_config = {
            "config_list": [{
                "model": MODEL_NAME,
                "api_key": OPENAI_API_KEY
            }],
            "temperature": 0.7
        }
        
        # Create the interview officer agent
        self.interview_officer = AssistantAgent(
            name="InterviewOfficer",
            system_message=f"""You are a visa officer conducting an interview for a {self.visa_type} visa.
Your goal is to determine if the applicant qualifies for the visa by asking relevant questions.
Be professional, thorough, and fair in your evaluation.
For {self.visa_type} visa, focus on topics like: {', '.join(self._get_relevant_topics())}.
Your main task is to ask questions and evaluate answers.
""",
            llm_config=llm_config,
            description="A professional visa interview officer who asks questions and evaluates responses."
        )
        
        # Create the evaluation agent
        self.evaluator = AssistantAgent(
            name="Evaluator",
            system_message="""You are an expert evaluator of visa interview responses.
Your job is to analyze applicant answers for clarity, relevance, consistency, and detail.
Provide numerical scores (1-10) and brief justifications for each evaluation.
""",
            llm_config=llm_config,
            description="An evaluation expert who scores and analyzes interview responses."
        )
        
        # Create the feedback agent
        self.feedback_agent = AssistantAgent(
            name="FeedbackProvider",
            system_message="""You are a feedback specialist for visa interviews.
Analyze the entire interview to provide comprehensive feedback and improvement suggestions.
Focus on communication style, content, and overall performance.
Generate both quantitative metrics and qualitative feedback.
""",
            llm_config=llm_config,
            description="A feedback specialist who provides comprehensive assessment at the end of the interview."
        )
        
        # Create a user proxy agent to represent the applicant
        self.user_proxy = UserProxyAgent(
            name="Applicant",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0,
            description="The visa applicant being interviewed."
        )
        
        # Create a group chat for the agents to interact
        self.agents = [
            self.interview_officer,
            self.evaluator, 
            self.feedback_agent,
            self.user_proxy
        ]
        
        self.group_chat = GroupChat(
            agents=self.agents, 
            messages=[],
            max_round=10
        )
        
        # Create a manager for the group chat
        self.chat_manager = GroupChatManager(
            groupchat=self.group_chat,
            llm_config=llm_config
        )
    
    def _get_relevant_topics(self) -> List[str]:
        """Get relevant topics based on visa type."""
        if self.visa_type == "tourist":
            return ["travel plans", "duration of stay", "financial means", "return intentions", "purpose of visit"]
        elif self.visa_type == "student":
            return ["educational background", "chosen program", "financial support", "career plans", "language proficiency"]
        else:
            return ["purpose of visit", "duration of stay", "financial means"]
    
    @tool
    async def generate_question(self) -> str:
        """Generate the next interview question based on visa type and conversation history."""
        # First try to use AutoGen to generate a contextual question
        if self.questions_asked > 0 and self.conversation_history:
            # Convert conversation history to a formatted string
            history_text = "\n".join([
                f"Question: {q}\nAnswer: {a}" for q, a in self.conversation_history
            ])
            
            # Ask interview_officer to generate the next question
            response = await self.interview_officer.a_generate(
                messages=[{
                    "role": "user",
                    "content": f"Based on this interview history, generate the next question for a {self.visa_type} visa interview:\n\n{history_text}"
                }]
            )
            
            question = response.get("content", "").strip()
            if question and "?" in question:
                # Extract the actual question if there's additional text
                import re
                question_match = re.search(r'(?:^|[\.\n])\s*([^\.]+\?)', question)
                if question_match:
                    question = question_match.group(1).strip()
        else:
            # Use RAG for the initial questions
            question = retrieve_question_from_chroma(self.visa_type)
        
        self.current_question = question
        self.questions_asked += 1
        return question
    
    @tool
    async def evaluate_answer(self, answer: str) -> Dict[str, float]:
        """
        Evaluate the applicant's answer to the current question using the evaluator agent.
        
        Args:
            answer: The applicant's transcribed answer
            
        Returns:
            Dict with evaluation metrics: relevance, clarity, detail, consistency
        """
        # Add to conversation history
        if self.current_question:
            self.conversation_history.append((self.current_question, answer))
        
        # If no valid API keys, return basic metrics
        if not OPENAI_API_KEY:
            return {
                "relevance": 7.0,
                "clarity": 7.0,
                "detail": 6.0,
                "consistency": 8.0
            }
        
        # Prepare context from conversation history
        context = "\n".join([f"Q: {q}\nA: {a}" for q, a in self.conversation_history])
        
        # Use the evaluator agent to assess the answer
        response = await self.evaluator.a_generate(
            messages=[{
                "role": "user",
                "content": f"""
                Evaluate this visa interview answer:
                
                Question: {self.current_question}
                Answer: {answer}
                
                Previous conversation:
                {context}
                
                Score from 1-10 on:
                - relevance: How relevant is the answer to the question?
                - clarity: How clear and articulate is the answer?
                - detail: Does the answer provide sufficient detail?
                - consistency: Is the answer consistent with previous answers?
                
                Return your evaluation as a JSON object with these four numerical scores.
                """
            }]
        )
        
        try:
            # Parse the response as JSON
            import json
            import re
            
            # Extract JSON from the response
            content = response.get("content", "")
            json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
            if json_match:
                metrics = json.loads(json_match.group(1))
            else:
                try:
                    # Look for anything that might be JSON in the response
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        metrics = json.loads(json_match.group(0))
                    else:
                        # Fallback if JSON parsing fails
                        metrics = {
                            "relevance": 7.0,
                            "clarity": 7.0,
                            "detail": 6.0,
                            "consistency": 8.0
                        }
                except:
                    # Fallback if JSON parsing fails
                    metrics = {
                        "relevance": 7.0,
                        "clarity": 7.0,
                        "detail": 6.0,
                        "consistency": 8.0
                    }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error evaluating answer: {str(e)}")
            return {
                "relevance": 7.0,
                "clarity": 7.0,
                "detail": 6.0,
                "consistency": 8.0
            }
    
    @tool
    async def generate_feedback(self) -> Tuple[Dict[str, float], str]:
        """
        Generate overall feedback and metrics for the interview session using the feedback agent.
        
        Returns:
            Tuple of (metrics dict, feedback string)
        """
        # Calculate default metrics
        default_metrics = {
            "fluency": 7.0,
            "confidence": 7.0,
            "contentAccuracy": 7.0,
            "responseTime": 7.0
        }
        
        # If we have conversation history, use the feedback agent
        if self.conversation_history and OPENAI_API_KEY:
            try:
                # Prepare context
                context = "\n".join([f"Q: {q}\nA: {a}" for q, a in self.conversation_history])
                
                # Use the feedback agent to generate comprehensive feedback
                response = await self.feedback_agent.a_generate(
                    messages=[{
                        "role": "user",
                        "content": f"""
                        Evaluate this complete {self.visa_type} visa interview and provide feedback:
                        
                        Interview transcript:
                        {context}
                        
                        Provide:
                        1. Detailed feedback on the applicant's performance (2-3 paragraphs)
                        2. Numerical scores (1-10) for: fluency, confidence, contentAccuracy, responseTime
                        
                        Format your response as a JSON object with 'feedback' and 'metrics' keys.
                        """
                    }]
                )
                
                # Parse the response
                import json
                import re
                
                content = response.get("content", "")
                # Try to extract JSON from the response
                json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                else:
                    try:
                        # Look for anything that might be JSON in the response
                        json_match = re.search(r'\{.*\}', content, re.DOTALL)
                        if json_match:
                            result = json.loads(json_match.group(0))
                        else:
                            # Extract structured feedback if JSON parsing fails
                            feedback = content
                            result = {
                                "feedback": feedback,
                                "metrics": default_metrics
                            }
                    except:
                        # Fallback if JSON parsing fails
                        result = {
                            "feedback": "Based on your interview responses, you demonstrated adequate knowledge about your visa application. To improve, consider providing more detailed and specific answers to questions. Overall, your application shows promise, but would benefit from better preparation on the key requirements for this visa type.",
                            "metrics": default_metrics
                        }
                
                metrics = result.get("metrics", default_metrics)
                feedback = result.get("feedback", "Thank you for completing the interview.")
                
                return metrics, feedback
                
            except Exception as e:
                logger.error(f"Error generating feedback: {str(e)}")
        
        # Fallback feedback
        feedback = "Based on your interview responses, you demonstrated adequate knowledge about your visa application. To improve, consider providing more detailed and specific answers to questions."
        
        return default_metrics, feedback
    
    async def next_question(self) -> str:
        """Get the next question in the interview process."""
        if self.questions_asked >= self.question_count:
            return None
            
        question = await self.generate_question()
        return question
    
    async def process_answer(self, answer_text: str) -> Dict[str, float]:
        """Process and evaluate the applicant's answer."""
        metrics = await self.evaluate_answer(answer_text)
        return metrics
    
    async def complete_interview(self) -> Tuple[Dict[str, float], str]:
        """Complete the interview and generate final feedback."""
        metrics, feedback = await self.generate_feedback()
        return metrics, feedback
