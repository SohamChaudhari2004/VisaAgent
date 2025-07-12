import json
import logging
import os
import random
from typing import Dict, List, Optional

import chromadb
import httpx
from chromadb.config import Settings

logger = logging.getLogger(__name__)

# Get Mistral API key from environment
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./data/chromadb")

# Initialize ChromaDB
try:
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    visa_collection = client.get_or_create_collection(name="visa_questions")
    logger.info("ChromaDB initialized successfully")
except Exception as e:
    logger.error(f"Error initializing ChromaDB: {str(e)}", exc_info=True)
    visa_collection = None

# Sample questions as fallback
SAMPLE_QUESTIONS = {
    "tourist": [
        "What is the purpose of your visit to our country?",
        "How long do you plan to stay?",
        "Where will you be staying during your visit?",
        "Have you visited our country before?",
        "What places are you planning to visit during your stay?",
        "Do you have relatives or friends in our country?",
        "How much money are you bringing for your trip?",
        "What is your occupation in your home country?",
        "Who is sponsoring your trip?",
        "When are you planning to return to your home country?"
    ],
    "student": [
        "Which university have you been accepted to?",
        "What program will you be studying?",
        "Why did you choose this specific university?",
        "How will your studies in our country benefit your career?",
        "How are you planning to finance your education?",
        "Have you paid the tuition fees yet?",
        "What are your plans after completing your studies?",
        "Do you have any family members studying or working in our country?",
        "How proficient are you in our language?",
        "Tell me about your previous educational background."
    ]
}

async def retrieve_question_from_chroma(visa_type: str) -> str:
    """
    Query ChromaDB + Mistral to get a relevant question.
    
    Args:
        visa_type: Type of visa (tourist or student)
        
    Returns:
        str: A question related to the visa type
    """
    # Defensive logging
    logger.info(f"Retrieving question for {visa_type} visa type")
    
    # Fallback to sample questions if ChromaDB is not available
    if not visa_collection or not MISTRAL_API_KEY:
        logger.warning("Using fallback sample questions (ChromaDB or MISTRAL_API_KEY not available)")
        questions = SAMPLE_QUESTIONS.get(visa_type, SAMPLE_QUESTIONS["tourist"])
        selected = random.choice(questions)
        logger.info(f"Selected fallback question: {selected}")
        return selected
    
    try:
        # Get context from ChromaDB
        logger.debug("Querying ChromaDB")
        results = visa_collection.query(
            query_texts=[f"question about {visa_type} visa"],
            n_results=3
        )
        
        # If no results, fallback to sample questions
        if not results or not results['documents'] or not results['documents'][0]:
            logger.warning("No results from ChromaDB, using sample questions")
            questions = SAMPLE_QUESTIONS.get(visa_type, SAMPLE_QUESTIONS["tourist"])
            selected = random.choice(questions)
            logger.info(f"Selected fallback question: {selected}")
            return selected
        
        # Prepare context for Mistral API
        context = "\n".join(results['documents'][0])
        
        # Query Mistral API to generate a question
        logger.debug("Sending request to Mistral API")
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    "https://api.mistral.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {MISTRAL_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "mistral-tiny",
                        "messages": [
                            {
                                "role": "system",
                                "content": f"You are a visa officer conducting an interview for a {visa_type} visa. Ask a relevant question based on the context."
                            },
                            {
                                "role": "user",
                                "content": f"Generate a single question for a {visa_type} visa interview. Make it concise and natural as if spoken by a visa officer. Context: {context}"
                            }
                        ],
                        "max_tokens": 100
                    }
                )
            
            # Process response
            if response.status_code == 200:
                data = response.json()
                question = data['choices'][0]['message']['content'].strip()
                logger.info(f"Generated question: {question}")
                return question
            else:
                logger.error(f"Mistral API error: {response.text}")
                # Fallback to sample questions on API error
                questions = SAMPLE_QUESTIONS.get(visa_type, SAMPLE_QUESTIONS["tourist"])
                selected = random.choice(questions)
                logger.info(f"Selected fallback question after API error: {selected}")
                return selected
        except httpx.TimeoutException:
            logger.error("Mistral API request timed out")
            questions = SAMPLE_QUESTIONS.get(visa_type, SAMPLE_QUESTIONS["tourist"])
            selected = random.choice(questions)
            logger.info(f"Selected fallback question after timeout: {selected}")
            return selected
            
    except Exception as e:
        logger.error(f"Error retrieving question: {str(e)}", exc_info=True)
        # Fallback to sample questions on error
        questions = SAMPLE_QUESTIONS.get(visa_type, SAMPLE_QUESTIONS["tourist"])
        selected = random.choice(questions)
        logger.info(f"Selected fallback question after error: {selected}")
        return selected

async def init_chroma_collection():
    """Initialize ChromaDB with sample visa questions if empty."""
    if not visa_collection:
        return
        
    # Check if collection is empty
    info = visa_collection.count()
    if info > 0:
        logger.info(f"ChromaDB collection already contains {info} documents")
        return
    
    logger.info("Initializing ChromaDB collection with sample questions")
    
    # Prepare documents for both visa types
    documents = []
    metadatas = []
    ids = []
    
    # Add tourist visa questions
    for i, question in enumerate(SAMPLE_QUESTIONS["tourist"]):
        documents.append(question)
        metadatas.append({"visa_type": "tourist"})
        ids.append(f"tourist_{i}")
    
    # Add student visa questions
    for i, question in enumerate(SAMPLE_QUESTIONS["student"]):
        documents.append(question)
        metadatas.append({"visa_type": "student"})
        ids.append(f"student_{i}")
    
    # Add to collection
    try:
        visa_collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"Added {len(documents)} questions to ChromaDB collection")
    except Exception as e:
        logger.error(f"Error adding documents to ChromaDB: {str(e)}", exc_info=True)
