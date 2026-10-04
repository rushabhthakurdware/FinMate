-- Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Profiles Table
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Transactions Table (Vector dimension 768)
CREATE TABLE IF NOT EXISTS public.transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    description TEXT NOT NULL,
    amount NUMERIC NOT NULL,
    category TEXT NOT NULL,
    is_avoidable BOOLEAN DEFAULT FALSE,
    source TEXT DEFAULT 'csv',
    embedding vector(768),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Risk Profiles Table
CREATE TABLE IF NOT EXISTS public.risk_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    age INT NOT NULL,
    monthly_income NUMERIC NOT NULL,
    emi_amount NUMERIC NOT NULL,
    dependents INT NOT NULL,
    savings NUMERIC NOT NULL,
    horizon_years INT NOT NULL,
    risk_score NUMERIC NOT NULL,
    category TEXT NOT NULL, -- Conservative, Moderate, Aggressive
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Advice History Table
CREATE TABLE IF NOT EXISTS public.advice_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    allocation JSONB NOT NULL,
    projections JSONB NOT NULL,
    explanation TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Knowledge Chunks Table (Vector dimension 768)
CREATE TABLE IF NOT EXISTS public.knowledge_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT NOT NULL,
    embedding vector(768),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.risk_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.advice_history ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "User profiles self access" ON public.profiles FOR ALL USING (auth.uid() = id);
CREATE POLICY "User transactions self access" ON public.transactions FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "User risk profiles self access" ON public.risk_profiles FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "User advice self access" ON public.advice_history FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Public read knowledge" ON public.knowledge_chunks FOR SELECT USING (true);

-- Vector Similarity Functions
CREATE OR REPLACE FUNCTION match_transactions (
  query_embedding vector(768),
  match_threshold float,
  match_count int,
  p_user_id uuid
)
RETURNS TABLE (
  id uuid,
  description text,
  category text,
  similarity float
)
LANGUAGE sql STABLE
AS $$
  SELECT
    transactions.id,
    transactions.description,
    transactions.category,
    1 - (transactions.embedding <=> query_embedding) AS similarity
  FROM transactions
  WHERE transactions.user_id = p_user_id
    AND 1 - (transactions.embedding <=> query_embedding) > match_threshold
  ORDER BY transactions.embedding <=> query_embedding
  LIMIT match_count;
$$;

CREATE OR REPLACE FUNCTION match_knowledge (
  query_embedding vector(768),
  match_threshold float,
  match_count int
)
RETURNS TABLE (
  id uuid,
  title text,
  content text,
  category text,
  similarity float
)
LANGUAGE sql STABLE
AS $$
  SELECT
    knowledge_chunks.id,
    knowledge_chunks.title,
    knowledge_chunks.content,
    knowledge_chunks.category,
    1 - (knowledge_chunks.embedding <=> query_embedding) AS similarity
  FROM knowledge_chunks
  WHERE 1 - (knowledge_chunks.embedding <=> query_embedding) > match_threshold
  ORDER BY knowledge_chunks.embedding <=> query_embedding
  LIMIT match_count;
$$;