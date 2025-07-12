import os
import logging
from typing import Dict, List, Optional, Any, Tuple

# AutoGen imports
import autogen
from autogen import Agent, UserProxyAgent, AssistantAgent, GroupChat, GroupChatManager

# Configure logging
logger = logging.getLogger(__name__)

# Get API keys from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

class VisaInterviewOrchestrator:
    """
    AutoGen-based orchestrator for the visa interview process.
    Coordinates multiple agents to handle different aspects of the interview.
    """
    
    def __init__(self, visa_type: str, question_count: int):
        """
        Initialize the orchestrator with interview parameters.
        
        Args:
            visa_type: Type of visa being applied for (e.g., "tourist", "student")
            question_count: Number of questions to ask in the interview
        """
        self.visa_type = visa_type
        self.question_count = question_count
        self.agents = {}
        self.group_chat = None
        self.chat_manager = None
        
        # Configure the agents
        self._setup_agents()
    
    def _setup_agents(self):
        """Set up the AutoGen agents for the interview process."""
        # Configure LLM config
        llm_config = {
            "config_list": [{
                "model": MODEL_NAME,
                "api_key": OPENAI_API_KEY
            }],
            "temperature": 0.7
        }
        
        # Create the interview coordinator agent
        self.agents["coordinator"] = AssistantAgent(
            name="InterviewCoordinator",
            system_message=f"""You are the coordinator for a {self.visa_type} visa interview process.
Your role is to manage the flow of the interview, ensuring all required topics are covered and
the process follows the correct sequence. You'll work with specialized agents to conduct a thorough
{self.question_count}-question interview.""",
            llm_config=llm_config
        )
        
        # Create the question generator agent
        self.agents["questioner"] = AssistantAgent(
            name="QuestionGenerator",
            system_message=f"""You are specialized in generating relevant questions for {self.visa_type} visa interviews.
Focus on creating clear, specific questions that assess the applicant's eligibility and intentions.
For a {self.visa_type} visa, important topics include relevant travel details, background information, and visa-specific requirements.""",
            llm_config=llm_config
        )
        
        # Create the response evaluator agent
        self.agents["evaluator"] = AssistantAgent(
            name="ResponseEvaluator",
            system_message="""You analyze and evaluate applicant responses in visa interviews.
Provide metrics on relevance, clarity, detail, and consistency for each answer.
Flag any contradictions or concerns that might affect visa eligibility.""",
            llm_config=llm_config
        )
        
        # Create the feedback generator agent
        self.agents["feedback"] = AssistantAgent(
            name="FeedbackGenerator",
            system_message="""You provide comprehensive feedback on visa interview performance.
At the end of the interview, analyze all responses to generate an overall assessment,
numerical metrics, and specific improvement suggestions.""",
            llm_config=llm_config
        )
        
        # Create a user proxy for the applicant
        self.agents["applicant"] = UserProxyAgent(
            name="Applicant",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0
        )
        
        # Set up group chat for agent collaboration
        agent_list = list(self.agents.values())
        self.group_chat = GroupChat(
            agents=agent_list,
            messages=[],
            max_round=self.question_count * 2 + 5  # Allow enough rounds for all questions + evaluation
        )
        
        self.chat_manager = GroupChatManager(
            groupchat=self.group_chat,
            llm_config=llm_config
        )
    
    async def start_interview(self) -> Dict[str, Any]:
        """
        Start the interview process by having the coordinator initiate the session.
        
        Returns:
            Dict containing the initial greeting and first question
        """
        # Have the coordinator initiate the interview
        await self.chat_manager.a_initiate_chat(
            self.agents["coordinator"],
            message=f"Let's begin a {self.visa_type} visa interview with {self.question_count} questions."
        )
        
        # Extract the first question from the conversation
        chat_history = self.group_chat.messages
        first_message = chat_history[1] if len(chat_history) > 1 else None
        
        if first_message:
            return {
                "greeting": "Welcome to your visa interview.",
                "first_question": first_message.get("content", "Could you tell us about your travel plans?")
            }
        
        # Default response if something went wrong
        return {
            "greeting": "Welcome to your visa interview.",
            "first_question": "Could you tell us about your travel plans?"
        }
    
    async def process_response(self, question: str, answer: str) -> Dict[str, Any]:
        """
        Process an applicant's response and get the next question.
        
        Args:
            question: The question that was asked
            answer: The applicant's answer to the question
            
        Returns:
            Dict containing evaluation metrics and the next question
        """
        # Submit the applicant's response to the group chat
        response_message = f"Question: {question}\nApplicant's answer: {answer}"
        
        # Have the applicant agent provide the response to the group
        await self.agents["applicant"].a_send(
            response_message,
            self.chat_manager
        )
        
        # Let the evaluator assess the response
        evaluation_prompt = f"Please evaluate the applicant's answer to: '{question}'"
        await self.agents["evaluator"].a_send(
            evaluation_prompt,
            self.chat_manager
        )
        
        # Have the questioner generate the next question
        next_question_prompt = "Based on the conversation so far, what should be the next question?"
        await self.agents["questioner"].a_send(
            next_question_prompt,
            self.chat_manager
        )
        
        # Extract evaluation and next question from the chat
        chat_history = self.group_chat.messages
        evaluation = None
        next_question = None
        
        # Find the last evaluation and question in the chat
        for msg in reversed(chat_history):
            content = msg.get("content", "")
            if msg.get("name") == "ResponseEvaluator" and not evaluation:
                evaluation = content
            if msg.get("name") == "QuestionGenerator" and not next_question:
                next_question = content
            if evaluation and next_question:
                break
        
        # Extract metrics from evaluation (simplified parsing)
        import re
        
        # Default metrics
        metrics = {
            "relevance": 7.0,
            "clarity": 7.0,
            "detail": 6.0,
            "consistency": 8.0
        }
        
        # Try to extract metrics from the evaluation text
        if evaluation:
            for metric in metrics.keys():
                pattern = fr"{metric}[:\s]+(\d+(?:\.\d+)?)"
                match = re.search(pattern, evaluation, re.IGNORECASE)
                if match:
                    try:
                        metrics[metric] = float(match.group(1))
                    except ValueError:
                        pass
        
        # Extract the actual question from the generated text
        if next_question:
            question_match = re.search(r'(?:^|[\.\n])\s*([^\.]+\?)', next_question)
            if question_match:
                next_question = question_match.group(1).strip()
        
        return {
            "metrics": metrics,
            "next_question": next_question or "Could you elaborate on your previous answer?"
        }
    
    async def complete_interview(self) -> Dict[str, Any]:
        """
        Complete the interview and generate final feedback.
        
        Returns:
            Dict containing feedback and overall metrics
        """
        # Request final feedback from the feedback generator
        await self.agents["coordinator"].a_send(
            "The interview is now complete. Please generate final feedback and evaluation.",
            self.chat_manager
        )
        
        await self.agents["feedback"].a_send(
            "Based on the entire interview, provide comprehensive feedback and overall metrics for the applicant.",
            self.chat_manager
        )
        
        # Extract feedback from the chat
        chat_history = self.group_chat.messages
        feedback = None
        
        for msg in reversed(chat_history):
            if msg.get("name") == "FeedbackGenerator":
                feedback = msg.get("content", "")
                break
        
        # Default metrics
        metrics = {
            "fluency": 7.5,
            "confidence": 7.0,
            "contentAccuracy": 7.0,
            "responseTime": 8.0
        }
        
        # Try to extract metrics from the feedback text
        if feedback:
            import re
            for metric in metrics.keys():
                pattern = fr"{metric}[:\s]+(\d+(?:\.\d+)?)"
                match = re.search(pattern, feedback, re.IGNORECASE)
                if match:
                    try:
                        metrics[metric] = float(match.group(1))
                    except ValueError:
                        pass
        
        return {
            "metrics": metrics,
            "feedback": feedback or "Thank you for completing the interview. Based on your responses, you have demonstrated adequate understanding of the visa requirements."
        }
