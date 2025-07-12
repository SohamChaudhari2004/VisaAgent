import uvicorn
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Make sure all necessary directories exist
    os.makedirs("data/chromadb", exist_ok=True)
    
    # Validate required environment variables
    required_vars = ["MISTRAL_API_KEY", "GROQ_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logging.warning(f"Missing required environment variables: {', '.join(missing_vars)}")
        logging.warning("Some features may not work correctly without these API keys.")
    else:
        logging.info("All required API keys found in environment variables.")
    
    # Log startup information
    logging.info("Starting SRVISA backend server...")
    logging.info("Make sure you have set all required API keys in .env file")
    
    # Start the server with CORS enabled
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0",  # This allows external connections
        port=8000, 
        reload=True,
        log_level="info",
        # Don't use a URL prefix as we're already using /api in the routes
        root_path=""
    )
