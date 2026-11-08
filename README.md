# 智研知库 · Zhiyan Knowledge Agent

> 面向计算机学科的 RAG 智能学习 Agent 工作台

---

## 1. 项目简介

智研知库不是传统课程管理后台，而是一套围绕“课程知识库 + RAG 检索 + 流式 Agent”构建的计算机学科学习工作台。

当前版本完成了从纯前端 Mock 到真实前后端联通的升级：

- 真实 JWT 登录、注册与用户会话
- 文档上传、解析、语义切分、向量化落库
- 混合检索（向量 + 关键词）、阈值过滤、重排序
- 服务端持久化的 Agent 思考步骤、工具调用、引用来源
- DeepSeek 流式回答，可配置离线模板兜底
- ECharts 知识依赖图谱
- 检索日志与阶段耗时可观测

## 2. 技术栈

| 层 | 技术 |
| --- | --- |
| 前端 | Vue 3 · TypeScript · Vite · Pinia · Element Plus · TailwindCSS · markdown-it · highlight.js · ECharts |
| 后端 | Python 3.13 · Django 6 · Django REST Framework · SimpleJWT · PyMySQL / SQLite |
| AI | DeepSeek OpenAI-compatible Chat API（可关闭） |
| 检索 | 本地中文 n-gram 哈希向量 + BM25 + Hybrid Rerank |
| 数据库 | MySQL 8.0 主库 `zhiyan_zhiku`，支持 SQLite 开发兜底 |

## 3. 功能页面

| 路由 | 页面 | 功能 |
| --- | --- | --- |
| `/login` | 登录 | 真实账号密码校验、加载态、错误提示、实时知识库统计 |
| `/workspace` | Agent 工作台 | 三栏布局、会话新建/删除/恢复、流式问答、Markdown、引用卡片、思考面板 |
| `/knowledge` | 知识库管理 | 课程/知识点/文档库标签页、搜索、文档上传/重索引/删除、RAG 参数 |
| `/rag-debug` | RAG 检索调试 | query → 召回片段、原文、来源、知识点 ID、相似度、阶段耗时 |
| `/graph` | 知识图谱 | ECharts 力导向图、领域筛选、节点详情、客观先修依赖 |

## 4. 快速启动

### 4.1 环境要求

- Node.js >= 18
- Python >= 3.12
- MySQL 8（或在 `server/.env` 中切换 SQLite）

### 4.2 后端

```bash
cd server
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows；macOS/Linux 使用 cp
```

编辑 `server/.env`：

```env
DB_ENGINE=mysql
DB_NAME=zhiyan_zhiku
DB_USER=root
DB_PASSWORD=your-password
DB_HOST=127.0.0.1
DB_PORT=3306

DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
LLM_PROVIDER=deepseek
```

初始化数据库（二选一）：

**方式 A：使用 Django 迁移和种子数据（推荐开发时使用）**

```bash
python manage.py migrate
python manage.py seed_all --reset
```

**方式 B：导入交付 SQL**

```bash
mysql -uroot -p < ../sql/00_create_database.sql
mysql -uroot -p < ../sql/01_schema_mysql.sql
mysql -uroot -p < ../sql/02_seed_mysql.sql
mysql -uroot -p < ../sql/03_verify.sql
```

启动后端：

```bash
python manage.py runserver 127.0.0.1:8000
```

### 4.3 前端

在项目根目录新开终端：

```bash
npm install
npm run dev
```

浏览器打开：<http://127.0.0.1:5173>

Vite 已配置 `/api` 与 `/media` 代理到 `http://127.0.0.1:8000`。

### 4.4 演示账号

```text
student / student123
admin   / zhiyan123
```

### 4.5 无 MySQL 时的 SQLite 兜底

将 `server/.env` 改为：

```env
DB_ENGINE=sqlite
SQLITE_PATH=db.sqlite3
```

执行：

```bash
python manage.py migrate
python manage.py seed_all --reset
python manage.py runserver 127.0.0.1:8000
```

### 4.6 不配置 DeepSeek 时

保持 `DEEPSEEK_API_KEY` 为空，或设置 `LLM_PROVIDER=local`。后端会使用基于真实检索证据的本地模板生成流式回答，引用、思考步骤、工具调用和检索日志仍正常工作，方便离线评审。

## 5. 系统结构

```text
.
├─ src/                              # Vue 前端
│  ├─ components/
│  │  ├─ chat/                       # 会话、消息、引用、思考面板、输入框
│  │  ├─ knowledge/                  # 文档上传与知识库文档管理
│  │  ├─ rag/                        # RAG 召回结果卡片
│  │  └─ feedback/                   # 空/错误状态
│  ├─ constants/                     # 快捷问题、默认 RAG 参数
│  ├─ services/
│  │  ├─ http.ts                     # JWT、刷新、错误归一化、SSE fetch
│  │  ├─ api.ts                      # REST API 类型化封装
│  │  ├─ agentService.ts             # Agent SSE 客户端
│  │  └─ sse.ts                      # SSE 帧解析器
│  ├─ stores/                        # auth / chat / rag / system
│  ├─ types/                         # 前后端共享数据形状
│  └─ views/                         # 5 个业务页面
├─ server/                           # Django 后端
│  ├─ apps/accounts/                 # 自定义用户与 JWT
│  ├─ apps/knowledge/                # 课程、知识点、图谱、文档、分块
│  ├─ apps/retrieval/                # embedding、BM25、混合检索、RAG 配置、日志
│  ├─ apps/agent/                    # 会话、消息、Agent SSE、引用、运行轨迹
│  ├─ apps/core/                     # health、public stats、seed 命令
│  ├─ seed/content/                  # 8 门课程的真实讲义 Markdown
│  ├─ seed/manifest.py               # 课程、知识点与图谱种子数据
│  └─ tests/                         # API / SSE / 检索 / 上传测试
└─ sql/                              # MySQL 建库、建表、种子、校验 SQL
```

种子规模：8 门核心课程、50 个知识点、8 份课程讲义、50 个向量片段、23 个图谱节点、33 条客观先修边。

## 6. 数据库设计

### 6.1 RAG 数据表

| 表 | 作用 |
| --- | --- |
| `documents` | 课程文档元数据、解析状态、chunk 数、上传人 |
| `document_chunks` | 原文、章节、标签、tokens、embedding JSON、向量模型信息 |
| `conversations` / `messages` | 服务端会话与消息 |
| `citations` | 消息级引用快照（课程、知识点、来源、分数） |
| `agent_runs` / `agent_steps` / `agent_tool_calls` | Agent 运行、思考步骤、工具调用与耗时 |
| `retrieval_logs` / `retrieval_log_items` | 每次检索的参数、候选数、召回分数、阶段耗时 |
| `rag_settings` | 每用户 Top-K / 阈值 / 检索模式 |

## 7. API 摘要

基础路径：`/api/v1`。除登录、刷新、health 和 public stats 外均需 `Authorization: Bearer <token>`。

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/auth/login/` | 登录，返回 access token、refresh、用户信息 |
| POST | `/auth/register/` | 注册账号并自动登录 |
| POST | `/auth/refresh/` | 刷新 access token |
| GET | `/auth/me/` | 当前用户 |
| POST | `/auth/logout/` | 登出 |
| GET | `/public/stats/` | 公开知识库统计 |
| GET | `/health/` | API、数据库、LLM、Embedding 健康信息 |
| GET | `/knowledge-base/overview/` | 课程、知识点、文档、向量片段统计 |
| GET | `/courses/` | 课程列表 |
| GET | `/knowledge-points/` | 知识点列表与搜索 |
| GET | `/graph/` | 知识图谱节点、边和分类 |
| GET / POST | `/documents/` | 文档列表 / 上传入库 |
| DELETE | `/documents/{uid}/` | 删除文档和其向量片段 |
| POST | `/documents/{uid}/reindex/` | 重新解析和向量化 |
| POST | `/retrieval/query/` | RAG 检索调试 |
| GET / PUT | `/rag/config/` | 用户 RAG 参数 |
| GET / POST | `/conversations/` | 会话列表 / 新建会话 |
| GET / DELETE | `/conversations/{id}/` | 会话详情 / 删除 |
| DELETE | `/conversations/{id}/messages/` | 清空会话 |
| DELETE | `/messages/{id}/` | 删除单条消息 |
| POST | `/conversations/{id}/stream/` | Agent SSE 流式问答 |

### SSE 事件

`POST /conversations/{id}/stream/` 返回 `text/event-stream`：

| event | data |
| --- | --- |
| `step` | 思考步骤状态 |
| `tool` | 工具名、入参、返回、耗时 |
| `retrieval` | 召回知识片段 |
| `citations` | 引用来源 |
| `delta` | 文本增量 |
| `done` | 引用数量、耗时、消息/运行/会话 ID |
| `error` | 错误信息与可重试标记 |

## 8. RAG-Agent 核心机制

1. **文档入库**：服务端解析 TXT / Markdown / PDF / DOCX，按标题和段落切分，生成 tokens 与 384 维本地哈希向量。
2. **混合召回**：查询向量余弦相似度 + BM25 词法分数，按 vector / keyword / hybrid 模式加权。
3. **阈值与重排**：低于用户阈值的片段被过滤；候选按标题、标签、知识点覆盖率和语义相关度重排。
4. **可追溯生成**：仅将召回片段作为证据加入 Prompt；DeepSeek 流式生成，无 Key 时使用真实证据模板兜底。
5. **可观测**：思考步骤、工具调用、召回片段、引用、阶段耗时与检索日志全部入库，刷新页面后可恢复。
6. **客观图谱**：知识图谱只展示课程先修关系，不包含学习进度、画像或推荐数据。

## 9. 评审演示路径

1. 使用 `student / student123` 登录，首页统计直接来自 MySQL。
2. 在工作台点击「生成AI工程师学习路线」，展开思考面板查看意图识别、混合检索、重排序、工具调用与召回片段。
3. 回答完成后查看带课程、知识点 ID 与相似度的引用卡片；刷新页面验证服务端会话与轨迹恢复。
4. 在知识库管理上传一份 TXT/Markdown 课程文档，观察 chunk 数和统计实时变化。
5. 在 RAG 检索调试切换 Top-K、阈值和三种检索模式，查看真实召回分数与阶段耗时。
6. 打开知识图谱，点击节点查看客观前置知识、后继方向与关联课程。
7. 清空 `DEEPSEEK_API_KEY` 或设置 `LLM_PROVIDER=local` 后重新提问，验证离线证据模板仍可流式输出。

## 10. 测试

后端：

```bash
cd server
python manage.py test tests -v 2
```

测试覆盖登录、概览、图谱、三种检索模式、RAG 配置、会话 CRUD、SSE 事件顺序、离线兜底、文档上传/召回/级联删除。

前端：

```bash
npm run type-check
npm run build
```

已验证：

- SQLite 与 MySQL 8 均可迁移、种子、测试和启动
- MySQL SQL 文件可在独立数据库完整恢复
- 浏览器端登录、流式回答、引用、刷新后会话恢复
- 文档上传、列表更新、删除
- RAG 调试与图谱渲染正常

## 11. 已知边界

- MySQL 8 没有原生向量类型，当前使用 JSON 持久化 embedding + Python 精确余弦检索，适合省赛 Demo 与千级片段；更大规模可替换为 pgvector / Milvus / Qdrant，API 不需要变化。
- PDF/DOCX 依赖 `pypdf` / `python-docx`；TXT / Markdown 无需额外组件。
- 上传是同步解析，适合现场演示；生产环境可将 `ingest_document` 放入 Celery/RQ 任务。
- DeepSeek Key 仅存放在 `server/.env`，已被 `.gitignore` 排除；请勿提交或写入数据库/SQL/README。

## 12. 团队信息

| 成员 | 角色 | 主要分工 |
| --- | --- | --- |
| Hua-Jian-Xiao | 项目负责人 / 全栈开发 | 架构设计、Vue 前端工作台、Django 后端、RAG 检索与 Agent 链路、文档与部署 |

- 联系方式：1419955217@qq.com
