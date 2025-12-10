# 🚀 云端部署检查清单

快速检查你的部署配置是否正确。

---

## ☑️ 部署前检查

### 代码准备

- [ ] 所有更改已提交到 Git
- [ ] 代码已推送到 GitHub
- [ ] `.env` 文件**未**提交（在 `.gitignore` 中）

### 账号注册

- [ ] Supabase 账号已注册
- [ ] Render 账号已注册
- [ ] Vercel 账号已注册
- [ ] GitHub 仓库已创建

---

## ☑️ Supabase 配置

### 项目创建

- [ ] Supabase 项目已创建
- [ ] 数据库密码已保存
- [ ] Project URL 已复制
- [ ] anon public key 已复制

### 数据表创建

- [ ] `holdings` 表已创建
- [ ] `knowledge_documents` 表已创建
- [ ] RLS（行级安全）已启用
- [ ] RLS 策略已创建（4 个 holdings + 3 个 documents）
- [ ] 索引已创建

### 认证配置

- [ ] Email 认证已启用
- [ ] 邮箱验证设置已确认（开发环境可关闭）

**测试 SQL**：在 SQL Editor 运行以下查询测试表是否创建成功：
```sql
SELECT * FROM public.holdings LIMIT 1;
SELECT * FROM public.knowledge_documents LIMIT 1;
```

---

## ☑️ Render 后端部署

### 服务配置

- [ ] GitHub 仓库已连接
- [ ] Service Name 已设置
- [ ] Region 已选择（Singapore/Oregon）
- [ ] Runtime 设置为 `Docker`
- [ ] Instance Type 选择 `Free`

### 环境变量

必须设置的环境变量（4 个）：

- [ ] `SUPABASE_URL` = `https://xxxxx.supabase.co`
- [ ] `SUPABASE_KEY` = `eyJhbGc...`（anon public key）
- [ ] `GEMINI_API_KEY` = `AIzaSy...`
- [ ] `PORT` = `10000`

### 部署验证

- [ ] 部署状态显示 "Live"（绿色）
- [ ] 服务 URL 已复制
- [ ] 访问 `https://your-backend.onrender.com/api/health` 返回成功

---

## ☑️ Vercel 前端部署

### 项目配置

- [ ] GitHub 仓库已导入
- [ ] Framework Preset 识别为 `Vite`
- [ ] **Root Directory** 设置为 `client`（重要！）
- [ ] Build Command: `npm run build`
- [ ] Output Directory: `dist`

### 环境变量

必须设置的环境变量（3 个）：

- [ ] `VITE_API_URL` = Render 后端 URL（**不要加斜杠**）
- [ ] `VITE_SUPABASE_URL` = Supabase Project URL
- [ ] `VITE_SUPABASE_ANON_KEY` = Supabase anon public key

**示例**：
```
✅ https://stock-portfolio-backend.onrender.com
❌ https://stock-portfolio-backend.onrender.com/
```

### 部署验证

- [ ] 部署状态显示 "Ready"
- [ ] 访问 Vercel URL 能看到登录界面
- [ ] 浏览器控制台无报错

---

## ☑️ 功能测试

### 用户注册与登录

- [ ] 能够注册新用户
- [ ] 收到确认邮件（或已禁用验证）
- [ ] 能够登录系统
- [ ] 能够登出

### 数据功能

- [ ] 点击"刷新数据"能加载数据
- [ ] 能添加新持仓
- [ ] 能修改持仓数量/成本
- [ ] 能删除持仓
- [ ] 数据正确显示

### 数据隔离

- [ ] 注册第二个测试账号
- [ ] 第二个账号看不到第一个账号的数据
- [ ] 两个账号数据完全独立

### AI 功能

- [ ] 能切换到 AI 投顾标签
- [ ] 能进入股票知识库
- [ ] 能上传文档
- [ ] AI 对话功能正常

---

## ☑️ 生产环境优化（可选）

### 安全性

- [ ] 启用 Supabase 邮箱验证
- [ ] 配置自定义域名
- [ ] 启用 HTTPS（自动）

### 性能

- [ ] 设置 Render 定期 ping（避免休眠）
- [ ] 配置 CDN（Vercel 自带）
- [ ] 监控服务状态

### 备份

- [ ] 配置 Supabase 自动备份
- [ ] 导出重要配置文档

---

## ⚠️ 常见错误检查

### 前端无法连接后端

检查项：
- [ ] Vercel `VITE_API_URL` 是否正确（不要加斜杠）
- [ ] Render 服务是否在线（可能休眠，等待 30-60 秒）
- [ ] 浏览器控制台是否有 CORS 错误

### 登录后看不到数据

检查项：
- [ ] Supabase RLS 是否启用
- [ ] RLS 策略是否创建
- [ ] 后端环境变量是否正确
- [ ] 用户 ID 是否正确传递

### 注册失败

检查项：
- [ ] Supabase Auth 是否启用
- [ ] Vercel Supabase 环境变量是否正确
- [ ] 密码是否至少 6 位
- [ ] 邮箱格式是否正确

---

## 📞 获取帮助

如果遇到问题：

1. **查看日志**：
   - Render: Dashboard → Logs
   - Vercel: Deployment → Build Logs
   - Supabase: Dashboard → Logs

2. **检查文档**：
   - 完整部署指南：`CLOUD_DEPLOYMENT_GUIDE.md`
   - Supabase 文档：https://supabase.com/docs
   - Render 文档：https://render.com/docs
   - Vercel 文档：https://vercel.com/docs

3. **常见问题**：参考 `CLOUD_DEPLOYMENT_GUIDE.md` 第 6 节

---

**✅ 全部勾选完成？恭喜你成功部署到云端！** 🎉
