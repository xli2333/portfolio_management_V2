-- 智能投资组合系统 - 数据库初始化脚本

-- 1. 创建持仓表
CREATE TABLE IF NOT EXISTS public.holdings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    symbol TEXT NOT NULL,
    shares BIGINT NOT NULL DEFAULT 0,
    cost_basis DOUBLE PRECISION NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, symbol)
);

-- 2. 创建知识库文档表
CREATE TABLE IF NOT EXISTS public.knowledge_documents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    symbol TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_size BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    file_type TEXT
);

-- 3. 启用行级安全
ALTER TABLE public.holdings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_documents ENABLE ROW LEVEL SECURITY;

-- 4. 删除旧策略
DROP POLICY IF EXISTS "Users can view own holdings" ON public.holdings;
DROP POLICY IF EXISTS "Users can insert own holdings" ON public.holdings;
DROP POLICY IF EXISTS "Users can update own holdings" ON public.holdings;
DROP POLICY IF EXISTS "Users can delete own holdings" ON public.holdings;
DROP POLICY IF EXISTS "Users can view own documents" ON public.knowledge_documents;
DROP POLICY IF EXISTS "Users can insert own documents" ON public.knowledge_documents;
DROP POLICY IF EXISTS "Users can delete own documents" ON public.knowledge_documents;

-- 5. 创建 holdings 表策略
CREATE POLICY "Users can view own holdings"
    ON public.holdings FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own holdings"
    ON public.holdings FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own holdings"
    ON public.holdings FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own holdings"
    ON public.holdings FOR DELETE
    USING (auth.uid() = user_id);

-- 6. 创建 knowledge_documents 表策略
CREATE POLICY "Users can view own documents"
    ON public.knowledge_documents FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own documents"
    ON public.knowledge_documents FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own documents"
    ON public.knowledge_documents FOR DELETE
    USING (auth.uid() = user_id);

-- 7. 创建索引
CREATE INDEX IF NOT EXISTS idx_holdings_user_id ON public.holdings(user_id);
CREATE INDEX IF NOT EXISTS idx_holdings_symbol ON public.holdings(symbol);
CREATE INDEX IF NOT EXISTS idx_holdings_user_symbol ON public.holdings(user_id, symbol);
CREATE INDEX IF NOT EXISTS idx_knowledge_user_id ON public.knowledge_documents(user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_symbol ON public.knowledge_documents(symbol);
CREATE INDEX IF NOT EXISTS idx_knowledge_user_symbol ON public.knowledge_documents(user_id, symbol);

-- 8. 验证
SELECT schemaname, tablename, rowsecurity as rls_enabled
FROM pg_tables
WHERE schemaname = 'public' AND tablename IN ('holdings', 'knowledge_documents');

SELECT tablename, COUNT(*) as policy_count
FROM pg_policies
WHERE schemaname = 'public' AND tablename IN ('holdings', 'knowledge_documents')
GROUP BY tablename;
