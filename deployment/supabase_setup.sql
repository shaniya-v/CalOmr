-- CalOmr Database Setup for Supabase
-- Run this script in Supabase SQL Editor (https://xhfepggdpdwiaoyjlwep.supabase.co)

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
