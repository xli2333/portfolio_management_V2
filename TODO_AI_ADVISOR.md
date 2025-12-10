# AI 投顾与知识库系统开发计划 (TODO List) - Revised 3

## 已完成功能 (Completed)
- [x] **基础设施**：`KnowledgeService` (PDF解析, 本地/Supabase存储)。
- [x] **前端重构**：Dashboard Tab, `AIAdvisorView`, `StockKnowledgeBase` UI。
- [x] **知识库管理**：文件上传、列表、删除。
- [x] **智能对话**：`/api/chat` 集成 Gemini，支持全量文档上下文注入 (Context Injection)。
- [x] **Markdown 渲染**：前端支持漂亮的 Markdown 排版。
- [x] **聊天记录管理**：本地持久化 (24h)，**多选导出为 PDF** 到知识库。

---

## 第三阶段：AI Agent 与搜索研究系统 (AI Agent & Search)

### 3.1 搜索工具集成 (`agent_tools.py`)
- [ ] **Google Search 工具**：
    - [ ] 利用 Gemini 的 Grounding 功能 (如果可用) 或封装 `google-generativeai` 的 Tools API。
    - [ ] 实现 `search_web(query)` 函数，返回相关性高的搜索结果片段。

### 3.2 顶级分析师 Agent 逻辑 (`analyst_agent.py`)
- [ ] **Prompt Engineering**：编写“顶级分析师”的 System Prompt。
    - [ ] 角色设定：华尔街顶级分析师 (Wall Street Analyst)。
    - [ ] 核心能力：能够处理超长文本 (Long Context)，能够判断何时需要联网搜索补充信息。
    - [ ] 任务：分析公司基本面、行业趋势、投资逻辑。
- [ ] **研究工作流 (Workflow)**：
    - [ ] **信息源融合**：同时读取用户勾选的内部 PDF 资料 + 实时网络搜索结果。
    - [ ] **深度思考**：利用 `gemini-2.5-pro` 进行推理，对比内部资料与外部新闻的异同。
    - [ ] **结构化输出**：生成包含“核心观点”、“风险提示”、“估值分析”的标准研报结构。

### 3.3 报告生成接口
- [ ] **后端接口**：`POST /api/agent/generate_report`。
- [ ] **输入**：`symbol`, `model` (gemini-2.5-pro), `selected_file_ids`。
- [ ] **执行逻辑**：
    1. 读取选定文件全量内容。
    2. 调用 Agent 执行研究（含搜索）。
    3. 生成 Markdown 格式的深度研报。

---

## 第四阶段：报告渲染与持久化 (Report Generation & Saving)

### 4.1 PDF 报告生成器升级 (`report_generator.py`)
- [ ] **Markdown 转 PDF 增强**：
    - [ ] 支持大标题、二级标题、加粗、列表等 Markdown 语法的 PDF 渲染（目前 `create_chat_pdf` 比较基础）。
    - [ ] 增加封面页（公司名称、生成时间、分析师署名）。
- [ ] **自动入库**：
    - [ ] 将生成的研报 PDF 保存到 `knowledge_base/{symbol}/reports/`。
    - [ ] 自动调用 `knowledge_service.save_document`，类型标记为 `ai_report`。

### 4.2 前端交互完善 (`StockKnowledgeBase.tsx`)
- [ ] **“生成深度研报”按钮**：
    - [ ] 在知识库页面添加显著的 Action Button（例如“启动 Deep Research”）。
    - [ ] 点击后进入 Loading 状态（可能需要几十秒）。
- [ ] **生成过程反馈**：
    - [ ] (可选) 显示 Agent 的思考过程步骤（例如：“正在阅读财报...”、“正在搜索行业新闻...”）。

---

## 第五阶段：整合与测试 (Integration & Testing)

### 5.1 整体联调
- [ ] **全流程测试**：
    1.  上传一份 2024 年财报 PDF。
    2.  勾选该财报。
    3.  点击“生成深度研报”。
    4.  验证：生成的报告是否包含了财报里的数据？是否包含了最近几天的新闻（证明搜索生效）？
    5.  验证：报告是否自动出现在左侧文档列表中？
    6.  验证：能否针对这份新生成的报告继续提问？