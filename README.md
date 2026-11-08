# 智研知库

> 面向计算机学科的 RAG 智能学习 Agent 工作台

一套可直接运行的 Vue 3 纯前端演示项目。整体采用 Editorial Magazine Style · 学术杂志风：暖纸色页面、衬线展示字体、墨色与酒红点缀、细线分隔、左侧固定索引导航与卡片化内容区，不做传统后台管理系统。

## 技术架构

### 技术栈

- Vue 3 + TypeScript + Vite
- Pinia / Vue Router
- Element Plus
- Tailwind CSS
- markdown-it + highlight.js
- ECharts

### 分层设计

- **视图层**：Vue 3 组合式 API + Element Plus，页面组件按路由拆分。
- **状态层**：Pinia 管理登录态、会话与 RAG 参数，并通过 localStorage 持久化。
- **服务层**：`src/services/` 封装 Agent 流式对话、Mock API 与 SSE 解析，视图不直接依赖 Mock 实现。
- **数据层**：`src/mock/index.ts` 提供课程、知识点、知识片段、图谱与 NCF 模拟数据。
- **工具层**：`src/utils/` 提供检索排序、检索模式、异步控制、格式化与存储等纯函数。

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

登录说明：Mock 鉴权，输入任意账号（至少 2 个字符）和密码（至少 6 位）即可进入，例如 `student / 123456`。

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

## 页面

| 路由 | 页面 | 核心内容 |
| --- | --- | --- |
| `/login` | 登录 | 左右分栏品牌页，账号 / 密码校验、加载态、错误提示 |
| `/workspace` | Agent 对话工作台 | 三栏布局、会话管理、逐字符 SSE、Markdown、引用卡片、思考面板 |
| `/knowledge` | 知识库管理 | 统计卡片、课程 / 知识点标签页与搜索、Top-K / 阈值 / 检索模式 |
| `/rag-debug` | RAG 检索调试 | 召回片段、原文、相似度进度、来源课程、知识点 ID、阶段耗时 |
| `/graph` | 知识图谱 | ECharts 力导向依赖图、节点详情卡、领域筛选 |

侧边栏的 `NCF推荐Demo` 是独立弹窗演示，不进入主业务。

## 已实现能力

### 全局界面

- 统一左侧导航、顶部面包屑、卡片、标签页、按钮、输入框样式。
- 桌面端顶部栏展示知识空间、Mock SSE 状态；移动端提供抽屉导航。
- 学术杂志风浅色工作台：暖纸底色、衬线标题、酒红强调色与细线排版，聚焦 RAG 学习与检索调试，不引入旧选课业务模块。

### Agent 对话

- 左侧新建 / 选择 / 删除会话，当前会话高亮，数据保存在 localStorage。
- 用户消息右对齐，AI 消息左对齐。
- AI 回答使用 `markdown-it` 渲染标题、列表、表格、行内代码与代码块（highlight.js），并逐字符流式追加。
- 每条回答底部展示引用来源卡片：课程名称、知识点 ID、相似度分数、章节与原文片段。
- 可折叠「Agent 思考过程」：思考内容、工具名称、入参、返回结果、召回知识片段。
- 底部多行输入框、`Enter / Shift + Enter`、停止生成、快捷按钮：
  - 生成AI工程师学习路线
  - 查询机器学习前置知识点

### 知识库管理

- 顶部展示课程数量、知识点数量、向量片段数量、最后更新时间。
- 课程列表 / 知识点列表标签页，两个列表均支持本地搜索。
- RAG 参数表单：Top-K、相似度阈值、混合 / 向量 / 关键词检索模式。
- 参数通过 Pinia 持久化，并同步给 Agent 与检索调试页。

### RAG 检索调试

- 左侧测试问题、示例问题、检索参数；右侧召回结果。
- 每条召回结果包含：原文内容、相似度分数与进度条、来源课程、知识点 ID。
- 展示向量化、召回、重排序与总耗时，帮助评审理解 RAG 内部机制。
- 支持无结果时一键降低阈值重新检索。

### 知识图谱

- ECharts `graph + force` 渲染 23 个知识点与 33 条客观先修关系。
- 支持拖拽、缩放、领域筛选。
- 点击节点后，右侧知识点详情卡显示名称、课程、前置知识、后继方向与说明。
- 只呈现课程知识结构，不包含任何个性化学习数据。

## 目录结构

```text
src/
├── components/
│   ├── chat/                   # 会话、消息、引用、思考面板、输入框
│   ├── feedback/               # 通用空状态 / 错误状态
│   ├── rag/                    # 检索结果卡片
│   ├── AppBreadcrumb.vue
│   ├── AppSidebar.vue
│   ├── BrandMark.vue
│   ├── NcfDemoDialog.vue
│   └── PageHeader.vue
├── mock/
│   └── index.ts                # 课程、知识点、知识片段、图谱、NCF 全部模拟数据
├── layouts/
│   └── AppLayout.vue
├── router/
│   └── index.ts
├── services/
│   ├── agentService.ts         # Agent 流式事件入口
│   ├── mockAgentServer.ts      # Mock SSE 服务
│   ├── mockApi.ts              # 登录、知识库、检索、NCF Mock API
│   └── sse.ts                  # SSE 帧解析器
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
│   ├── rag.ts
│   ├── retrieval.ts
│   └── storage.ts
└── views/
    ├── LoginView.vue
    ├── WorkbenchView.vue
    ├── KnowledgeBaseView.vue
    ├── RagDebugView.vue
    └── KnowledgeGraphView.vue
```

## Mock SSE

`src/services/mockAgentServer.ts` 通过 `ReadableStream` 生成 `text/event-stream` 事件，`src/services/sse.ts` 完成客户端解析，`src/services/agentService.ts` 向上层派发：

- `step`：思考步骤状态
- `tool`：工具调用与入参 / 返回
- `retrieval`：召回知识片段
- `citations`：引用来源
- `delta`：单字符文本增量
- `done`：完成与耗时

对接真实后端时，将 Mock 流的创建替换为真实 `fetch` 返回的 `response.body`，事件协议保持不变即可。

## 团队信息

| 成员 | 角色 | 主要分工 |
| --- | --- | --- |
| Hua-Jian-Xiao | 项目负责人 / 前端开发 | 整体架构、Agent 对话工作台、RAG 检索调试、知识图谱、文档与部署 |

- 联系方式：1419955217@qq.com

## 状态覆盖

- 骨架屏：工作台初始化、知识库、RAG 检索、知识图谱、NCF 推理。
- 空状态：无会话、无搜索结果、无召回片段、NCF 未运行。
- 加载状态：登录、刷新索引、检索、流式生成、推荐推理。
- 错误状态：登录校验、流式中断、请求失败与重试。
