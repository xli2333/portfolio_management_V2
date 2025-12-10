# 部署指南：Render + Vercel + Supabase

本指南将详细介绍如何部署您的股票投资组合应用程序。

## 前置要求

*   GitHub 账号 (请确保代码已上传到仓库)。
*   [Render](https://render.com) (用于后端)、[Vercel](https://vercel.com) (用于前端) 和 [Supabase](https://supabase.com) (用于数据库) 的账号。

## 第一部分：数据库配置 (Supabase)

1.  **创建项目**：登录 Supabase 并创建一个新项目。
2.  **获取密钥**：进入 **Project Settings > API**。复制 `Project URL` 和 `anon public` Key。稍后会用到。
3.  **创建数据表**：
    *   进入 **Table Editor** (表格编辑器)。
    *   创建一个名为 `holdings` 的新表。
    *   对于个人项目，可以暂时关闭 RLS (Row Level Security)，或者稍后配置。
    *   添加以下列：
        *   `symbol` (text类型, 设置为主键 Primary Key)
        *   `shares` (int8类型, 整数)
        *   `cost_basis` (float8类型, 浮点数)
        *   `updated_at` (timestamptz类型, 时间戳)
4.  **数据迁移 (可选)**：
    *   如果您本地的 `portfolio.json` 中已有数据，可以使用脚本迁移：
        1.  在本地项目根目录创建一个 `.env` 文件，填入 `SUPABASE_URL` 和 `SUPABASE_KEY`。
        2.  运行命令：`python migrate_to_supabase.py`。

## 第二部分：后端部署 (Render)

1.  **新建服务**：登录 Render，点击 **New +** 并选择 **Web Service**。
2.  **连接仓库**：选择您的 GitHub 仓库。
3.  **配置设置**：
    *   **Name (名称)**：`stock-portfolio-backend` (或您喜欢的名字)。
    *   **Runtime (运行环境)**：选择 `Docker` (Render 会自动识别项目中的 Dockerfile)。
    *   **Region (区域)**：选择离您较近的节点 (例如 Singapore 或 US West)。
    *   **Instance Type (实例类型)**：选择 Free (免费版)。
4.  **环境变量 (Environment Variables)**：
    添加以下键值对：
    *   `SUPABASE_URL`: (填入 Supabase 的 URL)
    *   `SUPABASE_KEY`: (填入 Supabase 的 anon Key)
    *   `GEMINI_API_KEY`: (填入您的 Google Gemini API Key)
    *   `PORT`: `10000` (可选，虽然 Render 会自动设置，但显式指定更稳妥)
5.  **部署**：点击 **Create Web Service**。
    *   *注意：由于需要编译 TA-Lib 库，首次构建可能需要几分钟时间，请耐心等待。*
6.  **获取 URL**：部署成功后，复制服务的 URL (例如 `https://stock-portfolio-backend.onrender.com`)。

## 第三部分：前端部署 (Vercel)

1.  **新建项目**：登录 Vercel，点击 **Add New > Project**。
2.  **导入仓库**：导入同一个 GitHub 仓库。
3.  **配置项目**：
    *   **Framework Preset (框架预设)**：Vercel 通常会自动识别为 `Vite`。
    *   **Root Directory (根目录)**：点击 `Edit`，必须选择 **`client`** 文件夹。**(这一步非常重要！)**
4.  **环境变量**：
    *   展开 **Environment Variables**。
    *   添加 `VITE_API_URL`，值为您刚刚在 Render 部署的后端 URL (例如 `https://stock-portfolio-backend.onrender.com`)。
    *   *注意：URL 末尾不要加斜杠 `/`。*
5.  **部署**：点击 **Deploy**。

## 第四部分：验证

1.  打开 Vercel 生成的前端网址。
2.  Dashboard 应该能正常加载。
3.  由于 Render 免费版在闲置时会休眠，第一次加载可能需要几十秒唤醒后端，请耐心等待。
4.  尝试添加一个股票代码 (例如 NVDA)，查看是否能保存并显示。

## 常见问题

*   **API Error 404**：检查 Render 后端日志，确认 API Key 是否正确，以及模型名称是否支持。
*   **无法保存数据**：检查 Supabase 的 RLS 策略是否阻止了写入，或者 `SUPABASE_KEY` 是否填写正确。
