# 云端部署完整指南

完整的 Vercel + Render + Supabase 部署教程（用户注册制 + 数据隔离）

---

## 📋 目录

1. [前置准备](#1-前置准备)
2. [Supabase 数据库配置](#2-supabase-数据库配置)
3. [后端部署到 Render](#3-后端部署到-render)
4. [前端部署到 Vercel](#4-前端部署到-vercel)
5. [验证和测试](#5-验证和测试)
6. [常见问题](#6-常见问题)

---

## 1. 前置准备

### 1.1 需要的账号

- ✅ GitHub 账号（代码托管）
- ✅ [Supabase](https://supabase.com) 账号（数据库 + 认证）
- ✅ [Render](https://render.com) 账号（后端服务）
- ✅ [Vercel](https://vercel.com) 账号（前端托管）

### 1.2 代码推送到 GitHub

```bash
# 确保所有更改已提交
git add .
git commit -m "feat: enable authentication and prepare for cloud deployment"
git push origin main
```

---

## 2. Supabase 数据库配置

### 2.1 创建项目

1. 登录 [Supabase](https://supabase.com)
2. 点击 **"New project"**
3. 填写项目信息：
   - **Name**: `stock-portfolio`（或自定义名称）
   - **Database Password**: 设置一个强密码（**务必保存**）
   - **Region**: 选择离你最近的区域（如 Singapore / Tokyo）
4. 点击 **"Create new project"**（创建需要几分钟）

### 2.2 获取 API 密钥

1. 进入项目后，点击左侧 **Settings** → **API**
2. 复制以下信息（**重要**）：
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon public** key: `eyJhbGc...`（很长的一串）

### 2.3 创建数据表

#### 方法 A：使用 SQL Editor（推荐）

1. 点击左侧 **SQL Editor**
2. 点击 **"New query"**
3. 复制粘贴以下 SQL：

```sql
-- 1. 创建持仓表（holdings）
CREATE TABLE IF NOT EXISTS public.holdings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    symbol TEXT NOT NULL,
    shares BIGINT NOT NULL DEFAULT 0,
    cost_basis DOUBLE PRECISION NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, symbol)
);

-- 2. 创建知识库文档表（knowledge_documents）
CREATE TABLE IF NOT EXISTS public.knowledge_documents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    symbol TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_size BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    file_type TEXT
);

-- 3. 启用 Row Level Security (RLS)
ALTER TABLE public.holdings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_documents ENABLE ROW LEVEL SECURITY;

-- 4. 创建 RLS 策略：用户只能访问自己的数据
-- holdings 表策略
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

-- knowledge_documents 表策略
CREATE POLICY "Users can view own documents"
    ON public.knowledge_documents FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own documents"
    ON public.knowledge_documents FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own documents"
    ON public.knowledge_documents FOR DELETE
    USING (auth.uid() = user_id);

-- 5. 创建索引优化查询
CREATE INDEX IF NOT EXISTS idx_holdings_user_id ON public.holdings(user_id);
CREATE INDEX IF NOT EXISTS idx_holdings_symbol ON public.holdings(symbol);
CREATE INDEX IF NOT EXISTS idx_knowledge_user_symbol ON public.knowledge_documents(user_id, symbol);
```

4. 点击 **"Run"** 执行 SQL
5. 检查是否成功：点击左侧 **Table Editor**，应该能看到 `holdings` 和 `knowledge_documents` 两张表

#### 方法 B：使用 Table Editor（图形界面）

如果不习惯 SQL，也可以手动创建表（略，建议使用方法 A）

### 2.4 配置邮箱认证（可选但推荐）

1. 点击左侧 **Authentication** → **Providers**
2. 找到 **Email**，确保已启用
3. 配置邮件模板（可选）：
   - 点击 **Email Templates**
   - 自定义注册确认邮件内容

### 2.5 禁用邮箱验证（开发环境可选）

如果想跳过邮箱验证直接登录：

1. 点击 **Authentication** → **Settings**
2. 找到 **"Enable email confirmations"**
3. **关闭**这个选项（生产环境建议开启）

---

## 3. 后端部署到 Render

### 3.1 创建 Web Service

1. 登录 [Render](https://render.com)
2. 点击 **"New +"** → **"Web Service"**
3. 连接你的 GitHub 仓库：
   - 点击 **"Connect GitHub"**
   - 选择 `stock_portfolio` 仓库

### 3.2 配置服务

填写以下信息：

| 配置项 | 值 |
|--------|-----|
| **Name** | `stock-portfolio-backend`（或自定义） |
| **Region** | Singapore / Oregon（选择离你近的） |
| **Branch** | `main` |
| **Runtime** | `Docker` |
| **Instance Type** | `Free`（免费版，首次部署选这个） |

### 3.3 设置环境变量

在 **Environment Variables** 部分，添加以下变量：

| Key | Value | 说明 |
|-----|-------|------|
| `SUPABASE_URL` | `https://xxxxx.supabase.co` | 从 Supabase 复制的 Project URL |
| `SUPABASE_KEY` | `eyJhbGc...` | 从 Supabase 复制的 anon public key |
| `GEMINI_API_KEY` | `AIzaSyDd61W7RPOve4ING9Hxh1O-7O4ow7Z527o` | 你的 Gemini API Key |
| `PORT` | `10000` | Render 默认端口 |

### 3.4 部署

1. 点击 **"Create Web Service"**
2. 等待部署完成（首次需要 5-10 分钟，因为要编译 TA-Lib）
3. 部署成功后，复制服务 URL：
   - 格式：`https://stock-portfolio-backend-xxxx.onrender.com`
   - **保存这个 URL，后面需要用**

### 3.5 验证后端

访问：`https://your-backend-url.onrender.com/api/health`

应该返回：`{"status": "ok"}` 或类似信息

---

## 4. 前端部署到 Vercel

### 4.1 创建项目

1. 登录 [Vercel](https://vercel.com)
2. 点击 **"Add New"** → **"Project"**
3. 导入你的 GitHub 仓库

### 4.2 配置项目

| 配置项 | 值 |
|--------|-----|
| **Framework Preset** | `Vite`（自动检测） |
| **Root Directory** | `client` **（重要！必须设置）** |
| **Build Command** | `npm run build`（默认） |
| **Output Directory** | `dist`（默认） |

### 4.3 设置环境变量

在 **Environment Variables** 部分添加：

| Name | Value | 说明 |
|------|-------|------|
| `VITE_API_URL` | `https://stock-portfolio-backend-xxxx.onrender.com` | 你的 Render 后端 URL（**不要加斜杠**） |
| `VITE_SUPABASE_URL` | `https://xxxxx.supabase.co` | Supabase Project URL |
| `VITE_SUPABASE_ANON_KEY` | `eyJhbGc...` | Supabase anon public key |

**重要提示**：
- ✅ 正确：`https://your-backend.onrender.com`
- ❌ 错误：`https://your-backend.onrender.com/`（末尾不要斜杠）

### 4.4 部署

1. 点击 **"Deploy"**
2. 等待部署完成（2-3 分钟）
3. 部署成功后，Vercel 会生成一个 URL：
   - 格式：`https://stock-portfolio-xxxx.vercel.app`

---

## 5. 验证和测试

### 5.1 注册新用户

1. 访问你的 Vercel 前端 URL
2. 看到登录界面，点击 **"新用户？创建账户"**
3. 输入邮箱和密码（密码至少 6 位）
4. 点击 **"注册账户"**
5. 如果启用了邮箱验证：
   - 检查邮箱，点击确认链接
   - 返回登录页面，用刚注册的账号登录
6. 如果禁用了邮箱验证：
   - 直接返回登录页面登录

### 5.2 测试功能

登录后测试以下功能：

#### ✅ 添加持仓
1. 点击右上角 **"刷新数据"** 按钮（首次需要手动刷新）
2. 输入股票代码（如 `AAPL`）、数量、成本
3. 点击添加，检查是否成功

#### ✅ 数据隔离测试
1. 注册第二个测试账号
2. 登录第二个账号
3. 确认看不到第一个账号的持仓数据

#### ✅ AI 投顾功能
1. 添加持仓后，切换到 **"AI 投顾"** 标签页
2. 点击任意股票，进入知识库
3. 测试上传文档、AI 对话功能

### 5.3 检查后端日志

如果遇到问题：

1. 登录 Render Dashboard
2. 点击你的服务
3. 查看 **Logs** 标签，检查错误信息

---

## 6. 常见问题

### Q1: 后端部署失败，提示找不到 Rust 编译器

**A**: 这是正常的，Render 会自动处理。如果持续失败：
- 检查 Dockerfile 是否存在
- 查看 Render Logs 确认具体错误

### Q2: 前端访问后端 API 报 CORS 错误

**A**: 检查后端代码中的 CORS 配置：
```python
# web_app.py
CORS(app, origins=["*"])  # 或指定 Vercel 域名
```

### Q3: 登录后显示"缺少 Supabase 环境变量"

**A**:
1. 检查 Vercel 环境变量是否正确设置
2. 重新部署：Vercel Dashboard → Deployments → Redeploy

### Q4: 数据没有隔离，能看到其他用户的数据

**A**:
1. 确认 Supabase RLS 策略已创建
2. 检查后端是否正确传递 `user_id`
3. 查看 Supabase Dashboard → Table Editor → RLS 是否启用

### Q5: Render 免费版后端休眠

**A**: Render 免费版闲置 15 分钟后会休眠，首次访问需要等待 30-60 秒唤醒。
- 解决方案 1：升级到付费版（$7/月）
- 解决方案 2：使用 cron job 定期 ping 后端

### Q6: 注册后收不到确认邮件

**A**:
1. 检查垃圾邮件文件夹
2. Supabase 免费版每小时限制 4 封邮件
3. 临时方案：关闭邮箱验证（见 2.5 节）

---

## 7. 后续优化

### 7.1 自定义域名

#### Vercel（前端）
1. Vercel Dashboard → Settings → Domains
2. 添加你的域名，按提示配置 DNS

#### Render（后端）
1. Render Dashboard → Settings → Custom Domain
2. 添加域名并配置 DNS

### 7.2 启用 HTTPS

Vercel 和 Render 都自动提供免费 SSL 证书，无需额外配置。

### 7.3 生产环境优化

1. **启用邮箱验证**（Supabase Auth Settings）
2. **配置备份策略**（Supabase Backups）
3. **监控服务状态**（设置 Uptime Robot）
4. **限制 API 调用频率**（避免超出免费额度）

---

## 8. 成本估算

### 免费套餐限制

| 服务 | 免费额度 | 限制 |
|------|----------|------|
| **Supabase** | 500MB 数据库 / 2GB 存储 | 每月 50,000 次认证 |
| **Render** | 750 小时/月 | 单个服务 512MB RAM，15 分钟休眠 |
| **Vercel** | 100GB 带宽 | 无限部署 |

### 升级建议

如果用户增多，建议优先升级：
1. **Render** → Pro ($7/月) - 避免休眠
2. **Supabase** → Pro ($25/月) - 8GB 数据库

---

## 9. 支持和反馈

- **GitHub Issues**: [仓库链接]
- **文档**: 本 README
- **Supabase 文档**: https://supabase.com/docs
- **Render 文档**: https://render.com/docs

---

**🎉 恭喜！你的智能投资组合系统已成功部署到云端！**

用户现在可以通过注册账号访问系统，每个用户的数据完全隔离，安全可靠。
