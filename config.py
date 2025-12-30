"""
Configuration management for CalOmr
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    # API Keys
    GROQ_API_KEY = os.getenv('Groq_API')
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    
    # Groq Models
    GROQ_VISION_MODEL = "llama-3.2-90b-vision-preview"
    GROQ_REASONING_MODEL = "llama-3.3-70b-versatile"
    GROQ_FAST_MODEL = "llama-3.1-8b-instant"
    GROQ_MATH_MODEL = "llama-3.1-70b-versatile"
    
    # Embedding Model
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION = 384
    
    # RAG Settings
    SIMILARITY_THRESHOLD = 0.7  # Minimum similarity for RAG match
    HIGH_CONFIDENCE_THRESHOLD = 0.85  # Use cached answer threshold
    TOP_K_RESULTS = 3  # Number of similar questions to retrieve
    
    # Temperature Settings
    VISION_TEMPERATURE = 0.1  # Low for accurate parsing
    SOLVING_TEMPERATURE = 0.2  # Low for consistent solving
    VERIFICATION_TEMPERATURE = 0.1  # Lowest for verification
    
    # Timeouts (seconds)
    API_TIMEOUT = 30
    DATABASE_TIMEOUT = 10
    
    # Subjects
    SUPPORTED_SUBJECTS = ['math', 'physics', 'chemistry']
    
    @classmethod
    def validate(cls):
        """Validate that all required config is present"""
        required = [
            ('GROQ_API_KEY', cls.GROQ_API_KEY),
            ('SUPABASE_URL', cls.SUPABASE_URL),
            ('SUPABASE_KEY', cls.SUPABASE_KEY)
        ]
        
        missing = [name for name, value in required if not value]
        
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        return True

# Validate on import
Config.validate()
