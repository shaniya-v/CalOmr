"""
Database setup and management for CalOmr using Supabase + pgvector
"""
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
from typing import Dict, List, Optional
import numpy as np
from config import Config
import time


class DatabaseManager:
    """Manages Supabase database operations with pgvector for RAG"""
    
    def __init__(self):
        """Initialize Supabase client and embedding model"""
        self.supabase: Client = create_client(
            Config.SUPABASE_URL,
            Config.SUPABASE_KEY
        )
        
        # Initialize embedding model for vector search
        print("Loading embedding model...")
        self.embedder = SentenceTransformer(Config.EMBEDDING_MODEL)
        print(f"✓ Loaded {Config.EMBEDDING_MODEL}")
    
    def get_setup_sql(self) -> str:
        """
        Return SQL setup script for Supabase
        Run this in Supabase SQL Editor to set up tables
        """
        return """
-- Enable pgvector extension for similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Main questions table with embeddings
CREATE TABLE IF NOT EXISTS questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_text TEXT NOT NULL,
    subject VARCHAR(50) NOT NULL CHECK (subject IN ('math', 'physics', 'chemistry')),
    topic VARCHAR(100),
    difficulty VARCHAR(20) CHECK (difficulty IN ('easy', 'medium', 'hard')),
    equations TEXT[],  -- Array of LaTeX equations
    keywords TEXT[],
    options JSONB NOT NULL,  -- {"A": "...", "B": "...", "C": "...", "D": "..."}
    correct_answer CHAR(1) CHECK (correct_answer IN ('A', 'B', 'C', 'D')),
    reasoning TEXT,
    confidence INTEGER CHECK (confidence BETWEEN 0 AND 100),
    image_url TEXT,
    embedding vector(384),  -- Embedding dimension for all-MiniLM-L6-v2
    solved_by VARCHAR(50),  -- 'groq_vision', 'groq_reasoning', 'rag', etc.
    solve_time_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for fast vector similarity search (cosine distance)
CREATE INDEX IF NOT EXISTS questions_embedding_idx 
ON questions USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create indexes for filtering
CREATE INDEX IF NOT EXISTS questions_subject_idx ON questions(subject);
CREATE INDEX IF NOT EXISTS questions_topic_idx ON questions(topic);
CREATE INDEX IF NOT EXISTS questions_difficulty_idx ON questions(difficulty);
CREATE INDEX IF NOT EXISTS questions_created_at_idx ON questions(created_at DESC);

-- Query log for analytics
CREATE TABLE IF NOT EXISTS query_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID REFERENCES questions(id),
    response_time_ms INTEGER,
    cache_hit BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS query_log_created_at_idx ON query_log(created_at DESC);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_questions_updated_at 
BEFORE UPDATE ON questions
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function for vector similarity search with filtering
CREATE OR REPLACE FUNCTION match_questions(
    query_embedding vector(384),
    match_subject text,
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 3
)
RETURNS TABLE (
    id uuid,
    question_text text,
    topic varchar(100),
    equations text[],
    options jsonb,
    correct_answer char(1),
    reasoning text,
    confidence integer,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        questions.id,
        questions.question_text,
        questions.topic,
        questions.equations,
        questions.options,
        questions.correct_answer,
        questions.reasoning,
        questions.confidence,
        1 - (questions.embedding <=> query_embedding) as similarity
    FROM questions
    WHERE questions.subject = match_subject
    AND 1 - (questions.embedding <=> query_embedding) > match_threshold
    ORDER BY questions.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Statistics view
CREATE OR REPLACE VIEW question_stats AS
SELECT 
    subject,
    COUNT(*) as total_questions,
    AVG(confidence) as avg_confidence,
    AVG(solve_time_ms) as avg_solve_time_ms
FROM questions
GROUP BY subject;
"""
    
    def store_question(
        self,
        question_data: Dict,
        answer: str,
        reasoning: str,
        confidence: int,
        solve_time_ms: int,
        solved_by: str
    ) -> Optional[str]:
        """
        Store a solved question with vector embedding in Supabase
        
        Args:
            question_data: Parsed question data
            answer: The correct answer (A/B/C/D)
            reasoning: Solution reasoning
            confidence: Confidence score (0-100)
            solve_time_ms: Time taken to solve in milliseconds
            solved_by: Method used to solve
            
        Returns:
            Question ID if successful, None otherwise
        """
        try:
            # Create text for embedding
            embedding_text = (
                f"{question_data['question_text']} "
                f"{' '.join(question_data.get('equations', []))}"
            )
            
            # Generate embedding vector
            embedding = self.embedder.encode(embedding_text).tolist()
            
            # Prepare data for insertion
            insert_data = {
                'question_text': question_data['question_text'],
                'subject': question_data['subject'],
                'topic': question_data.get('topic'),
                'difficulty': question_data.get('difficulty'),
                'equations': question_data.get('equations', []),
                'keywords': question_data.get('keywords', []),
                'options': question_data['options'],
                'correct_answer': answer,
                'reasoning': reasoning,
                'confidence': confidence,
                'embedding': embedding,
                'solved_by': solved_by,
                'solve_time_ms': solve_time_ms
            }
            
            # Insert into Supabase
            result = self.supabase.table('questions').insert(insert_data).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]['id']
            
            return None
            
        except Exception as e:
            print(f"❌ Error storing question: {e}")
            return None
    
    def search_similar_questions(
        self,
        question_text: str,
        equations: List[str],
        subject: str
    ) -> Optional[Dict]:
        """
        Search for similar questions using vector similarity (RAG)
        
        Args:
            question_text: The question text
            equations: List of LaTeX equations
            subject: Subject (math/physics/chemistry)
            
        Returns:
            Dict with answer and metadata if found, None otherwise
        """
        try:
            # Create embedding for search
            search_text = f"{question_text} {' '.join(equations)}"
            search_embedding = self.embedder.encode(search_text).tolist()
            
            # Call the match_questions RPC function
            result = self.supabase.rpc(
                'match_questions',
                {
                    'query_embedding': search_embedding,
                    'match_subject': subject,
                    'match_threshold': Config.SIMILARITY_THRESHOLD,
                    'match_count': Config.TOP_K_RESULTS
                }
            ).execute()
            
            # Check if we found similar questions
            if result.data and len(result.data) > 0:
                best_match = result.data[0]
                similarity = best_match['similarity']
                
                # Only use if similarity is above high confidence threshold
                if similarity > Config.HIGH_CONFIDENCE_THRESHOLD:
                    return {
                        'answer': best_match['correct_answer'],
                        'confidence': int(similarity * 100),
                        'source': 'rag_database',
                        'reasoning': best_match['reasoning'],
                        'similar_question': best_match['question_text'],
                        'topic': best_match['topic']
                    }
            
            return None
            
        except Exception as e:
            print(f"⚠️ RAG search error: {e}")
            return None
    
    def log_query(
        self,
        question_id: Optional[str],
        response_time_ms: int,
        cache_hit: bool,
        error_message: Optional[str] = None
    ):
        """Log a query for analytics"""
        try:
            self.supabase.table('query_log').insert({
                'question_id': question_id,
                'response_time_ms': response_time_ms,
                'cache_hit': cache_hit,
                'error_message': error_message
            }).execute()
        except Exception as e:
            print(f"⚠️ Error logging query: {e}")
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        try:
            # Total questions
            total_result = self.supabase.table('questions').select('*', count='exact').execute()
            total_questions = total_result.count
            
            # Questions by subject
            subject_stats = {}
            for subject in Config.SUPPORTED_SUBJECTS:
                result = self.supabase.table('questions')\
                    .select('*', count='exact')\
                    .eq('subject', subject)\
                    .execute()
                subject_stats[subject] = result.count
            
            # Cache hit rate
            total_queries_result = self.supabase.table('query_log')\
                .select('*', count='exact')\
                .execute()
            total_queries = total_queries_result.count
            
            cache_hits_result = self.supabase.table('query_log')\
                .select('*', count='exact')\
                .eq('cache_hit', True)\
                .execute()
            cache_hits = cache_hits_result.count
            
            cache_hit_rate = (cache_hits / total_queries * 100) if total_queries > 0 else 0
            
            return {
                'total_questions': total_questions,
                'by_subject': subject_stats,
                'total_queries': total_queries,
                'cache_hits': cache_hits,
                'cache_hit_rate': cache_hit_rate
            }
            
        except Exception as e:
            print(f"❌ Error getting statistics: {e}")
            return {}


if __name__ == "__main__":
    # Initialize and print setup SQL
    db = DatabaseManager()
    print("\n" + "="*60)
    print("🗄️  SUPABASE SETUP SQL")
    print("="*60)
    print("\nCopy and run this SQL in your Supabase SQL Editor:\n")
    print(db.get_setup_sql())
    print("\n" + "="*60)
