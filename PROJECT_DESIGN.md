# 股票投资组合管理系统设计文档 (Portfolio System Design)

## 1. 项目背景与目标
当前系统主要针对单个股票进行技术指标分析。本次升级旨在构建一个基于**云端架构**的投资组合管理功能，支持多端访问、数据持久化及深入的持仓分析。

## 2. 云端架构设计 (Cloud Architecture)

本方案采用 **Vercel + Render + Supabase** 的分离式架构，以发挥各平台优势。

```text
+------------------+       +------------------+       +------------------+
|  前端 (Vercel)   |       |   后端 (Render)  |       | 数据库 (Supabase)|
| [React + Vite]   | HTTPS |  [Python Flask]  | TCP   |   [PostgreSQL]   |
|                  |------>|                  |------>|                  |
| 1. 用户交互界面  | REST  | 1. AkShare数据源 | SQL   | 1. 用户持仓数据  |
| 2. 数据可视化    | API   | 2. 核心指标计算  |       | 2. 用户配置信息  |
| 3. 路由管理      |       | 3. 业务逻辑处理  |       |                  |
+------------------+       +------------------+       +------------------+
```

### 选型理由
*   **Vercel**: 极速的前端托管，全球CDN，适合 React SPA 应用。
*   **Render**: 适合运行 Python Web 服务。相比 Vercel Serverless，Render 提供完整的运行环境，不会因数据抓取时间过长（>10s）而超时。
*   **Supabase**: 提供托管的 PostgreSQL 数据库，免去维护数据库的繁琐，自带 API 和管理面板。

## 3. 核心功能需求

### 3.1 投资组合管理 (Portfolio Management)
*   **数据存储**：持仓数据存入 Supabase `holdings` 表。
*   **增删改查**：
    *   添加股票：代码、持仓数量、成本单价。
    *   编辑：修改持仓数量或成本。
    *   删除：移除自选股。

### 3.2 实时仪表盘 (Live Dashboard)
*   **自动计算**：后端实时获取最新股价，结合数据库中的持仓信息，计算：
    *   当前市值 (Market Value)
    *   浮动盈亏 (Unrealized P&L)
    *   盈亏比例 (P&L %)
*   **展示形式**：卡片式汇总 + 详细数据表格。

### 3.3 图表联动
*   点击持仓列表中的股票，前端路由跳转至详情页，调用现有的 `Analyzer` 模块进行深度技术分析。

## 4. 数据库设计 (Supabase Schema)

我们需要在 Supabase 中创建一个名为 `holdings` 的表。

| 字段名 (Column) | 类型 (Type) | 说明 (Description)      |
| :--- | :--- | :--- |
| `id` | uuid | 主键 (Primary Key) |
| `symbol` | text | 股票代码 (如 "600519") |
| `shares` | integer | 持仓股数 |
| `cost_basis` | float | 平均持仓成本单价 |
| `created_at` | timestamptz | 创建时间 |
| `updated_at` | timestamptz | 更新时间 |

*(注：暂不引入复杂的用户系统，默认单用户模式，若需多用户可增加 `user_id` 字段)*

## 5. 交互流程图 (Interaction Flow)

```text
[用户] 打开 Vercel 部署的前端页面
  |
  +---> [页面加载] 请求 Render 后端 /api/portfolio
          |
          +---> [Render] 查询 Supabase 获取持仓列表 (symbol, shares, cost)
          |       |
          |       +---> [Supabase] 返回数据
          |
          +---> [Render] 调用 AkShare 获取这些股票的 *实时现价*
          |
          +---> [Render] 计算 (现价 - 成本) * 数量 = 盈亏
          |
          +---> [Render] 返回完整的 JSON 数据给前端
  |
  +---> [前端渲染] 展示仪表盘、总资产饼图、持仓列表
  |
  +---> [用户操作] 点击 "添加股票"
          |
          +---> 弹出模态框 -> 输入代码/价格/数量 -> 确认
          |
          +---> POST /api/portfolio -> Render -> 写入 Supabase
```

## 6. 开发实施步骤

1.  **基础设施准备**：
    *   [ ] 注册/配置 Supabase 项目，获取 `SUPABASE_URL` 和 `SUPABASE_KEY`。
    *   [ ] 在 Supabase SQL 编辑器中创建 `holdings` 表。
2.  **后端改造 (Python)**：
    *   [ ] 安装 `supabase` Python 客户端。
    *   [ ] 创建 `db.py` 模块负责数据库连接。
    *   [ ] 更新 `web_app.py`，新增 `/api/portfolio` 系列接口。
3.  **前端开发 (React)**：
    *   [ ] 配置 `.env.local` 指向 Render 的 API 地址。
    *   [ ] 开发 Dashboard 组件。
    *   [ ] 开发 AddStock 组件。
4.  **部署**：
    *   [ ] 部署后端到 Render (配置环境变量)。
    *   [ ] 部署前端到 Vercel (配置环境变量)。