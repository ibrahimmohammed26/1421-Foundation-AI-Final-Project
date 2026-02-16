import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Settings:
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/ancientwave")
    
    # Vector DB path
    VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "data/knowledge_base.db")
    
    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    
    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = ENVIRONMENT == "development"

settings = Settings()