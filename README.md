# 智研知库

> 面向计算机学科的 RAG 智能学习 Agent 工作台

智研知库是一个纯前端可运行的演示项目，把「Agent 流式对话、RAG 引用溯源、知识库配置、检索调试、知识依赖图谱」整合进同一个学习工作台。所有数据均由前端 Mock 生成，无需启动后端服务。

## 技术架构

### 技术栈

- Vue 3 + TypeScript + Vite
- Pinia
- Vue Router
- Element Plus
- Tailwind CSS
- markdown-it + highlight.js
- ECharts

### 分层设计

- **视图层**：Vue 3 组合式 API + Element Plus，页面组件按路由拆分。
- **状态层**：Pinia 管理登录态、会话与 RAG 参数，并通过 localStorage 持久化。
- **服务层**：`src/services/` 统一封装 Agent 流式对话、Mock API 与 SSE 解析，视图不直接依赖 Mock 实现。
- **数据层**：`src/data/mockData.ts` 提供课程、知识片段、知识图谱等演示数据。
- **工具层**：`src/utils/` 提供检索排序、异步控制、格式化与存储等纯函数。

## 环境配置与运行

### 环境要求

| 工具 | 版本 |
| --- | --- |
| Node.js | >= 18（推荐 20 LTS） |
| npm | >= 9 |

### 安装与启动

```bash
# 1. 安装依赖（国内网络可使用 npmmirror 镜像）
npm install --registry=https://registry.npmmirror.com

# 2. 可选：复制环境变量模板
cp .env.example .env.local

# 3. 启动开发服务器
npm run dev
```

浏览器访问：<http://localhost:5173>

演示账号已预填：

```text
账号：admin
密码：123456
```

### 环境变量

| 变量名 | 必填 | 说明 |
| --- | --- | --- |
| `VITE_API_BASE_URL` | 否 | 真实后端地址；不配置时使用前端 Mock 服务（当前默认） |

项目为纯前端 Mock 演示，无需任何 API 密钥即可运行。若后续接入真实大模型或检索服务，请仅通过环境变量注入密钥：本地使用 `.env.local`，部署时使用托管平台的环境变量配置。**严禁将密钥写入源码或提交到仓库**；`.env`、`.env.*` 已被 `.gitignore` 忽略，仅保留 `.env.example` 模板。

### 依赖清单

完整依赖见 [package.json](package.json)，主要依赖如下：

| 依赖 | 用途 |
| --- | --- |
| `vue` / `vue-router` / `pinia` | 页面渲染、路由与全局状态 |
| `element-plus` | UI 组件库 |
| `echarts` | 知识图谱力导向图 |
| `markdown-it` / `highlight.js` | 回答 Markdown 渲染与代码高亮 |
| `tailwindcss` | 原子化样式 |
| `vite` / `typescript` / `vue-tsc` | 构建与类型检查 |

### 其他命令

```bash
# 类型检查
npm run type-check

# 生产构建
npm run build

# 预览构建产物
npm run preview
```

## 页面与路由

| 路由 | 页面 | 说明 |
| --- | --- | --- |
| `/login` | 登录 | 极简账号密码登录，Mock 鉴权，登录态保存在 localStorage |
| `/workspace` | Agent 对话工作台 | 三栏布局：会话列表、流式聊天、Agent 运行台 |
| `/knowledge` | 知识库管理 | 课程/知识点统计、课程索引、RAG Top-K 与阈值配置 |
| `/rag-debug` | RAG 检索调试 | 输入 query，展示召回片段、相似度分数与阶段耗时 |
| `/graph` | 知识图谱 | ECharts 力导向图，仅呈现客观课程先修关系 |

侧边栏中的 **NCF 推荐 Demo** 是独立弹窗演示，不属于核心 RAG 流程。

## 核心实现

### Mock SSE 流式聊天

- `src/services/mockAgentServer.ts`：模拟后端 SSE 服务，按 `step`、`tool`、`retrieval`、`citations`、`delta`、`done` 事件逐段推送。
- `src/services/sse.ts`：实现 `ReadableStream` 的 SSE 帧解析。
- `src/services/agentService.ts`：UI 唯一依赖的 Agent 服务层，支持 `AbortController` 中断。

后续对接真实后端时，只需将 `createMockAgentSseStream` 替换为返回 `response.body` 的真实 `fetch` 请求，事件格式保持不变即可。

### Agent 思考面板

每条 AI 消息保存独立 `AgentTrace`，包括：

- 思考步骤及状态（等待 / 执行中 / 完成）
- 工具调用记录、入参、出参、耗时
- 本次检索命中的知识库片段与相似度

AI 回答完成后面板会自动折叠，可随时重新展开查看。

### RAG 参数共享

Top-K 与相似度阈值保存在 `useRagStore` 中并持久化到 localStorage。知识库管理页、RAG 检索调试页与 Agent 对话工作台共用同一套参数，修改后全局生效。

### 知识图谱

- 23 个知识点、33 条依赖边，分为数理与编程基础、计算机核心、进阶方向、大模型与 RAG 四个领域。
- 使用 ECharts `graph + force` 布局，支持拖拽、缩放、领域筛选。
- 点击节点可查看前置知识、后继方向与课程出处。
- 不包含任何用户掌握度、学习画像或推荐权重数据。

### 状态处理

- 骨架屏：知识库、RAG 检索调试、知识图谱加载态。
- 空状态：无会话、无检索结果、无引用来源等。
- 加载态：登录、检索、索引刷新、NCF 推理。
- 错误提示：服务层异常、流式中断、请求重试。

## 目录结构

```text
src/
├── components/
│   ├── chat/                   # 会话列表、聊天消息、思考面板、引用卡片、输入框等
│   ├── feedback/               # 通用空状态/错误状态
│   ├── rag/                    # 检索结果卡片
│   ├── AppSidebar.vue
│   ├── BrandMark.vue
│   ├── NcfDemoDialog.vue
│   └── PageHeader.vue
├── data/
│   └── mockData.ts             # 课程、知识片段、图谱、NCF 等 Mock 数据
├── layouts/
│   └── AppLayout.vue
├── router/
│   └── index.ts
├── services/
│   ├── agentService.ts         # Agent 流式事件入口
│   ├── mockAgentServer.ts      # Mock SSE 服务端
│   ├── mockApi.ts              # 知识库、检索、登录、NCF Mock API
│   └── sse.ts                  # SSE Parser
├── stores/
│   ├── auth.ts
│   ├── chat.ts
│   └── rag.ts
├── styles/
│   └── index.css
├── types/
│   └── index.ts
├── utils/
│   ├── async.ts
│   ├── format.ts
│   ├── id.ts
│   ├── retrieval.ts
│   └── storage.ts
└── views/
    ├── LoginView.vue
    ├── WorkbenchView.vue
    ├── KnowledgeBaseView.vue
    ├── RagDebugView.vue
    └── KnowledgeGraphView.vue
```

## 团队信息

| 成员 | 角色 | 主要分工 |
| --- | --- | --- |
| Hua-Jian-Xiao | 项目负责人 / 前端开发 | 整体架构、Agent 对话工作台、RAG 检索调试、知识图谱、文档与部署 |

- 联系方式：1419955217@qq.com

## 说明

- 这是纯前端 Mock 项目，不包含真实鉴权、后端接口或持久化数据库。
- 会话、登录态与 RAG 配置保存在浏览器 localStorage 中。
- 清除站点 localStorage 可恢复初始演示数据。
