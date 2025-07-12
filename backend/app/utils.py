import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)

def create_llm_config(model: str = None, temperature: float = 0.7) -> Dict[str, Any]:
    """
    Create a configuration for language models that works with both LangChain and AutoGen.
    
    Args:
        model: The model name to use (defaults to environment variable or gpt-3.5-turbo)
        temperature: The temperature setting for the model
        
    Returns:
        Dict containing the LLM configuration
    """
    # Get API keys from environment
    openai_api_key = os.getenv("OPENAI_API_KEY")
    groq_api_key = os.getenv("GROQ_API_KEY")
    model_name = model or os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    
    # Base config
    config = {
        "temperature": temperature
    }
    
    # AutoGen style config
    autogen_config = {
        "config_list": []
    }
    
    # Add OpenAI configuration if available
    if openai_api_key:
        autogen_config["config_list"].append({
            "model": model_name,
            "api_key": openai_api_key
        })
        
        # LangChain style
        config["openai_api_key"] = openai_api_key
        config["model_name"] = model_name
    
    # Add Groq configuration if available
    if groq_api_key:
        autogen_config["config_list"].append({
            "model": "llama3-70b-8192",  # Default Groq model
            "api_key": groq_api_key,
            "base_url": "https://api.groq.com/openai/v1"
        })
        
        # LangChain style
        config["groq_api_key"] = groq_api_key
    
    # Combine configs
    config["autogen"] = autogen_config
    
    return config

def extract_json_from_text(text: str) -> Dict[str, Any]:
    """
    Attempt to extract a JSON object from text that might contain markdown or other content.
    
    Args:
        text: Text that may contain JSON
        
    Returns:
        Extracted JSON as dict, or empty dict if extraction fails
    """
    import re
    import json
    
    # Try to find JSON in code blocks first
    json_match = re.search(r'```(?:json)?\n(.*?)\n```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except:
            pass
    
    # Try to find anything that looks like a JSON object
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except:
            pass
    
    # Return empty dict if all extraction attempts fail
    return {}

def extract_question_from_text(text: str) -> str:
    """
    Extract a question from text that might contain additional content.
    
    Args:
        text: Text that may contain a question
        
    Returns:
        Extracted question, or original text if no question found
    """
    import re
    
    # Look for a sentence ending with a question mark
    question_match = re.search(r'(?:^|[\.\n])\s*([^\.]+\?)', text)
    if question_match:
        return question_match.group(1).strip()
    
    return text.strip()
