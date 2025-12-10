# ValueCell 智能证券投资组合分析系统 (Technical Analyzer)

> **原子级项目文档**  
> 版本: 1.0.0 | 架构: C/S分离 | 核心驱动: Python/Flask + React/Vite

## 1. 产品目的 (Product Purpose)

本项目旨在构建一个**高度自动化、可视化的A股市场技术分析与投资组合管理平台**。它解决了个人投资者在多只股票监控、复杂技术指标计算以及交易信号捕捉上的痛点。

核心目标包括：
*   **自动化数据获取**：消除手动下载行情的繁琐，直接对接开源财经数据接口。
*   **深度技术分析**：提供超越基础行情软件的高级指标计算（如SuperTrend, Ichimoku Cloud等）。
*   **组合动态监控**：实时跟踪持仓盈亏、风险分布及信号状态。
*   **交互式可视化**：利用现代Web技术提供流畅的K线图表与指标叠加分析。

## 2. 产品设计 (Product Design)

系统采用前后端分离的**RESTful架构**，确保了数据处理的高效性与用户界面的响应速度。

### 2.1 架构图解
*   **后端 (Backend)**: 负责数据清洗、量化指标运算、信号生成及PDF报告渲染。
*   **前端 (Frontend)**: 负责用户交互、实时图表绘制、状态管理及数据展示。
*   **数据层 (Data Layer)**: 基于AKShare获取实时/历史行情，本地JSON/Excel文件作为持久化存储。

### 2.2 目录结构说明
```text
/
├── advanced_indicators.py   # 高级指标算法实现 (SuperTrend, ATR等)
├── advanced_signals.py      # 复合交易信号逻辑判断
├── analyzer.py             # 核心分析调度器，整合数据与指标
├── data_fetcher.py         # 数据获取适配器 (对接AKShare)
├── indicators.py           # 基础指标库 (MA, MACD, RSI, KDJ)
├── portfolio_service.py    # 投资组合增删改查业务逻辑
├── web_app.py              # Flask HTTP服务器入口及路由定义
├── signals.py              # 基础买卖信号定义
├── config.py               # 全局配置参数
├── requirements.txt        # Python依赖清单
├── vercel.json             # Vercel 部署配置
├── client/                 # 前端工程目录
│   ├── src/                # React 源代码
│   ├── vite.config.ts      # Vite 构建配置
│   └── package.json        # 前端依赖清单
└── output/                 # 分析报告与导出文件存储区
```

## 3. 产品功能 (Product Features)

### 3.1 核心分析引擎
*   **多维度指标计算**:
    *   **趋势类**: 移动平均线 (MA), 指数平滑移动平均 (EMA), 布林带 (Bollinger Bands), 一目均衡表 (Ichimoku Cloud).
    *   **动量类**: 相对强弱指数 (RSI), 随机指标 (KDJ), 平滑异同移动平均线 (MACD).
    *   **波动类**: 真实波幅 (ATR), 超级趋势 (SuperTrend).
*   **信号系统**:
    *   自动识别金叉/死叉。
    *   基于SuperTrend的趋势反转信号。
    *   RSI超买/超卖预警。

### 3.2 交互式仪表盘 (Frontend)
*   **专业级K线图表**: 集成 `Lightweight Charts`，支持缩放、平移、十字光标查看。
*   **动态指标切换**: 用户可实时开关主图/副图指标。
*   **组合概览**: 卡片式展示总资产、日收益、个股表现热力分布。

### 3.3 数据管理与导出
*   **多格式导出**: 支持生成 Excel 详细数据表 (`.xlsx`) 及 JSON 原始数据。
*   **PDF 研报**: 服务端渲染包含图表与信号解读的 PDF 分析报告 (由 `reportlab` 驱动)。

## 4. 技术栈 (Tech Stack)

### 4.1 后端 (Server)
*   **Runtime**: Python 3.12+
*   **Web Framework**: Flask 3.0+ (REST API服务)
*   **Data Source**: AKShare (开源财经数据接口)
*   **Data Processing**: Pandas, NumPy (向量化计算)
*   **Technical Analysis**: TA-Lib (C底层的高性能技术分析库)
*   **Utilities**: OpenPyXL (Excel处理), ReportLab (PDF生成)

### 4.2 前端 (Client)
*   **Framework**: React 18
*   **Language**: TypeScript 5.0+
*   **Build Tool**: Vite 5.0+
*   **UI System**: Tailwind CSS (原子化CSS框架), Lucide React (图标库)
*   **Charts**: Lightweight Charts (TradingView核心库), Recharts (数据可视化)
*   **State/Network**: Fetch API, React Hooks

## 5. 安装与部署 (Installation)

### 5.1 环境预备
*   Python 3.12 或更高版本
*   Node.js 18.0 或更高版本
*   Git

### 5.2 后端启动
1.  创建并激活虚拟环境:
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Linux/Mac
    source venv/bin/activate
    ```
2.  安装依赖:
    ```bash
    pip install -r requirements.txt
    ```
    *注意: TA-Lib 安装可能需要预编译的 wheel 文件，请根据系统架构下载对应的 `.whl` 安装。*
3.  启动服务:
    ```bash
    python web_app.py
    ```
    服务默认运行在 `http://localhost:5000`。

### 5.3 前端启动
1.  进入前端目录:
    ```bash
    cd client
    ```
2.  安装依赖:
    ```bash
    npm install
    ```
3.  启动开发服务器:
    ```bash
    npm run dev
    ```
    访问终端显示的本地地址 (通常为 `http://localhost:5173`)。

## 6. 配置说明 (Configuration)

### 6.1 后端配置
主要配置位于 `config.py` (如有) 或环境变量中。
*   `CHINESE_FONT`: 设置 PDF 生成时的中文字体路径，防止乱码。
*   `HAVE_REPORT`: 控制是否启用 PDF 生成功能的布尔开关。

### 6.2 前端配置
位于 `client/vite.config.ts`。
*   **Proxy**: 默认配置了代理，将 `/api` 请求转发至 `http://127.0.0.1:5000`，解决跨域问题。

## 7. 注意事项 (Notes)
*   **数据延迟**: 免费源数据可能存在一定的分钟级延迟，不适用于高频交易。
*   **编码**: 本项目统一采用 **UTF-8** 编码，Windows环境下控制台输出已做特殊适配。
*   **API限制**: 请勿高频并发请求数据接口，以免触发源站反爬限制。