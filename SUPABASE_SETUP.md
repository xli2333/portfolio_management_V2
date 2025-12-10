# Supabase 数据库配置脚本

完整的数据库初始化 SQL 代码，直接复制到 Supabase SQL Editor 运行即可。

---

## 📋 使用步骤

1. 登录你的 Supabase 项目
2. 左侧菜单点击 **SQL Editor**
3. 点击 **"New query"**
4. **复制下面的完整 SQL 代码**
5. 粘贴到编辑器
6. 点击右下角 **"Run"** 执行
7. 等待执行完成

---

## 🔧 完整 SQL 代码

```sql
-- ==========================================
-- 智能投资组合系统 - 数据库初始化脚本
-- 用途：创建数据表、启用行级安全策略、创建索引
-- 执行时间：约 5 秒
-- ==========================================

-- ==========================================
-- 第一部分：创建数据表
-- ==========================================

-- 1. 创建持仓表 (holdings)
-- 存储用户的股票持仓信息
CREATE TABLE IF NOT EXISTS public.holdings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    symbol TEXT NOT NULL,
    shares BIGINT NOT NULL DEFAULT 0,
    cost_basis DOUBLE PRECISION NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, symbol)
);

-- 2. 创建知识库文档表 (knowledge_documents)
-- 存储用户上传的研报和文档信息
CREATE TABLE IF NOT EXISTS public.knowledge_documents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    symbol TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_size BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    file_type TEXT
);

-- ==========================================
-- 第二部分：启用行级安全 (Row Level Security)
-- ==========================================

-- 启用 RLS 确保用户只能访问自己的数据
ALTER TABLE public.holdings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_documents ENABLE ROW LEVEL SECURITY;

-- ==========================================
-- 第三部分：创建 RLS 安全策略
-- ==========================================

-- 删除旧策略（如果存在）
DROP POLICY IF EXISTS "Users can view own holdings" ON public.holdings;
DROP POLICY IF EXISTS "Users can insert own holdings" ON public.holdings;
DROP POLICY IF EXISTS "Users can update own holdings" ON public.holdings;
DROP POLICY IF EXISTS "Users can delete own holdings" ON public.holdings;
DROP POLICY IF EXISTS "Users can view own documents" ON public.knowledge_documents;
DROP POLICY IF EXISTS "Users can insert own documents" ON public.knowledge_documents;
DROP POLICY IF EXISTS "Users can delete own documents" ON public.knowledge_documents;

-- Holdings 表的 RLS 策略（4 个）

-- 1. 用户只能查看自己的持仓
CREATE POLICY "Users can view own holdings"
    ON public.holdings FOR SELECT
    USING (auth.uid() = user_id);

-- 2. 用户只能添加自己的持仓
CREATE POLICY "Users can insert own holdings"
    ON public.holdings FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- 3. 用户只能更新自己的持仓
CREATE POLICY "Users can update own holdings"
    ON public.holdings FOR UPDATE
    USING (auth.uid() = user_id);

-- 4. 用户只能删除自己的持仓
CREATE POLICY "Users can delete own holdings"
    ON public.holdings FOR DELETE
    USING (auth.uid() = user_id);

-- Knowledge Documents 表的 RLS 策略（3 个）

-- 1. 用户只能查看自己的文档
CREATE POLICY "Users can view own documents"
    ON public.knowledge_documents FOR SELECT
    USING (auth.uid() = user_id);

-- 2. 用户只能添加自己的文档
CREATE POLICY "Users can insert own documents"
    ON public.knowledge_documents FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- 3. 用户只能删除自己的文档
CREATE POLICY "Users can delete own documents"
    ON public.knowledge_documents FOR DELETE
    USING (auth.uid() = user_id);

-- ==========================================
-- 第四部分：创建索引优化查询性能
-- ==========================================

-- Holdings 表索引
CREATE INDEX IF NOT EXISTS idx_holdings_user_id ON public.holdings(user_id);
CREATE INDEX IF NOT EXISTS idx_holdings_symbol ON public.holdings(symbol);
CREATE INDEX IF NOT EXISTS idx_holdings_user_symbol ON public.holdings(user_id, symbol);

-- Knowledge Documents 表索引
CREATE INDEX IF NOT EXISTS idx_knowledge_user_id ON public.knowledge_documents(user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_symbol ON public.knowledge_documents(symbol);
CREATE INDEX IF NOT EXISTS idx_knowledge_user_symbol ON public.knowledge_documents(user_id, symbol);

-- ==========================================
-- 第五部分：验证配置
-- ==========================================

-- 查看表和 RLS 状态
SELECT
    schemaname,
    tablename,
    rowsecurity as rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
    AND tablename IN ('holdings', 'knowledge_documents');

-- 查看创建的策略数量
SELECT
    tablename,
    COUNT(*) as policy_count
FROM pg_policies
WHERE schemaname = 'public'
    AND tablename IN ('holdings', 'knowledge_documents')
GROUP BY tablename;

-- ==========================================
-- 执行完成！
-- ==========================================

-- 预期结果：
-- ✅ 2 张表已创建
-- ✅ RLS 已启用
-- ✅ 7 个安全策略已创建
-- ✅ 6 个索引已创建
```

---

## ✅ 验证结果

执行完成后，应该看到：

### 表和 RLS 状态
```
holdings          | true
knowledge_documents | true
```

### 策略数量
```
holdings          | 4
knowledge_documents | 3
```

---

## 🔍 检查表结构

执行完成后，可以在 Supabase Table Editor 中查看：

### holdings 表结构
| 列名 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键，自动生成 |
| user_id | UUID | 用户ID，外键关联 auth.users |
| symbol | TEXT | 股票代码（如 AAPL） |
| shares | BIGINT | 持仓数量 |
| cost_basis | DOUBLE PRECISION | 成本价 |
| updated_at | TIMESTAMPTZ | 更新时间 |

### knowledge_documents 表结构
| 列名 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键，自动生成 |
| user_id | UUID | 用户ID，外键关联 auth.users |
| symbol | TEXT | 股票代码 |
| filename | TEXT | 文件名 |
| file_size | BIGINT | 文件大小（字节） |
| created_at | TIMESTAMPTZ | 创建时间 |
| file_type | TEXT | 文件类型（如 application/pdf） |

---

## 🛡️ 安全说明

### RLS（行级安全）如何工作？

1. **用户 A** 只能看到 `user_id = A` 的数据
2. **用户 B** 只能看到 `user_id = B` 的数据
3. 即使直接访问 API，也无法跨用户查询数据
4. Supabase 自动验证 `auth.uid()` 与数据库中的 `user_id`

### 示例

```sql
-- 用户 A 登录后查询持仓
SELECT * FROM holdings;
-- 结果：只返回 user_id = A 的记录

-- 用户 B 登录后查询持仓
SELECT * FROM holdings;
-- 结果：只返回 user_id = B 的记录
```

---

## ❓ 常见问题

### Q: 执行 SQL 时报错 "relation already exists"
**A**: 表已存在，可以忽略或先删除表重新创建：
```sql
DROP TABLE IF EXISTS public.knowledge_documents CASCADE;
DROP TABLE IF EXISTS public.holdings CASCADE;
-- 然后重新执行完整脚本
```

### Q: 如何测试 RLS 是否生效？
**A**: 在 SQL Editor 执行：
```sql
-- 应该返回空结果（因为 SQL Editor 没有用户上下文）
SELECT * FROM holdings;
```

### Q: 如何查看所有策略？
**A**: 执行：
```sql
SELECT * FROM pg_policies
WHERE schemaname = 'public';
```

---

## 🎯 下一步

Supabase 配置完成后：

1. ✅ 复制 **Project URL** 和 **anon public key**
2. ✅ 更新本地 `.env` 和 `client/.env` 文件
3. ✅ 测试本地环境
4. ✅ 继续部署到 Render + Vercel

---

**配置完成！现在你的数据库已经准备好了！** 🚀
