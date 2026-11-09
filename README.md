# 智研知库 · Zhiyan Knowledge Agent

> 面向计算机学科的 RAG 智能学习 Agent 工作台

---

## 1. 项目简介

智研知库是一套围绕“课程知识库 + RAG 检索 + 流式 Agent”构建的计算机学科学习工作台。

当前版本完成了从纯前端 Mock 到真实前后端联通的升级：

- 真实 JWT 登录、注册与用户会话
- 文档上传、解析、语义切分、向量化落库
- 混合检索（向量 + 关键词）、阈值过滤、重排序
- 服务端持久化的 Agent 思考步骤、工具调用、引用来源
- DeepSeek 流式回答，可配置离线模板兜底
- ECharts 知识依赖图谱
- 检索日志与阶段耗时可观测
- 个人中心与安全问题找回密码

## 2. 技术架构

### 2.1 技术栈

| 层 | 技术 |
| --- | --- |
| 前端 | Vue 3 · TypeScript · Vite · Pinia · Element Plus · TailwindCSS · markdown-it · highlight.js · ECharts |
| 后端 | Python 3.13 · Django 6 · Django REST Framework · SimpleJWT · PyMySQL / SQLite |
| AI | DeepSeek OpenAI-compatible Chat API（可关闭） |
| 检索 | 本地中文 n-gram 哈希向量 + BM25 + Hybrid Rerank |
| 数据库 | MySQL 8.0 主库 `zhiyan_zhiku`，支持 SQLite 开发兜底 |

### 2.2 分层设计

- **视图层**：Vue 3 组合式 API + Element Plus，页面组件按路由拆分。
- **状态层**：Pinia 管理登录态、会话、RAG 参数与系统状态，并通过 localStorage 持久化。
- **服务层**：`src/services/` 封装 JWT、REST API、Agent SSE 与流式解析，视图不直接依赖接口细节。
- **业务层**：Django app 按账号、知识库、检索、Agent 拆分，服务逻辑集中于 `services/`。
- **数据层**：MySQL 持久化课程、知识点、文档分块、会话轨迹与引用；SQLite 用于本地兜底。

## 3. 功能页面

| 路由 | 页面 | 功能 |
| --- | --- | --- |
| `/login` | 登录 | 真实账号密码校验、加载态、错误提示、实时知识库统计 |
| `/workspace` | Agent 工作台 | 三栏布局、会话新建/删除/恢复、流式问答、Markdown、引用卡片、思考面板 |
| `/knowledge` | 知识库管理 | 课程/知识点/文档库标签页、搜索、文档上传/重索引/删除、RAG 参数 |
| `/rag-debug` | RAG 检索调试 | query → 召回片段、原文、来源、知识点 ID、相似度、阶段耗时 |
| `/graph` | 知识图谱 | ECharts 力导向图、领域筛选、节点详情、客观先修依赖 |
| `/profile` | 个人中心 | 头像上传、昵称/邮箱/专业/简介、安全问题、修改密码 |
| `/forgot-password` | 找回密码 | 通过安全问题验证并重置密码 |

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

安全问题找回密码演示：

```text
student → 我最喜欢的课程是？ / 机器学习
admin   → 我的管理口令是？ / zhiyan
```

用户资料与安全问题哈希保存在 MySQL `users` 表；头像文件保存在 `server/media/avatars/`。

### 4.5 导入课程数据集到知识库管理

项目内置 132 门课程数据集，可全量导入项目数据库，并在「知识库管理 → 课程」中直接显示。命令默认读取本机数据集数据库，连接参数使用 `server/.env` 的 MySQL 配置：

```bash
cd server
python manage.py import_legacy_courses --dry-run          # 先预览课程数量
python manage.py import_legacy_courses                    # 正式导入课程
python manage.py import_legacy_knowledge_points           # 为课程补齐知识点
python manage.py generate_legacy_documents                # 为每门课程生成知识纲要文档并建立向量索引
```

如需单独指定数据集数据库连接，可使用 `LEGACY_DB_NAME`、`LEGACY_DB_HOST`、`LEGACY_DB_PORT`、`LEGACY_DB_USER`、`LEGACY_DB_PASSWORD` 环境变量。

导入规则：

- 已存在的 5 门精选核心课程保留原名、简介和排序，只补全封面/链接等空字段；
- 其余课程使用稳定 UID，重复执行只更新、不重复创建；
- 数据集课程先展示在核心课程之后，按学习人数排序；
- 课程卡片使用数据集海报；没有同名课程海报时使用最接近的课程海报，海报加载失败时自动生成课程封面；点击任意卡片会在新标签页打开对应「学堂在线」课程；
- `import_legacy_knowledge_points` 基于数据集的 `knowledge_nodes` / `course_knowledge` 为课程补齐知识点；没有关联节点的课程会生成「课程导论」兜底，保证 135 门课程全部有知识点；
- `generate_legacy_documents` 为每门课程生成一份「课程知识纲要」Markdown，并走正常解析、切分、向量化流程；文档库达到 135 份，覆盖 135 门课程；
- 当前规模：135 门课程、221 个知识点、135 份文档、600 个向量片段；
- 生成文档后卡片显示「已索引」，知识点详情中的关联片段也会自动填充；
- `seed_all --reset` 会清空课程表、知识点表和文档表，重置种子后请重新执行上面四条命令。

#### 导入数据存储位置

| 数据 | 存储位置 |
| --- | --- |
| 课程 | MySQL `zhiyan_zhiku.courses` |
| 知识点 | MySQL `zhiyan_zhiku.knowledge_points` |
| 文档元数据 | MySQL `zhiyan_zhiku.documents` |
| 文档片段与向量 | MySQL `zhiyan_zhiku.document_chunks`，`embedding` 字段为 JSON 向量 |
| 数据集 ID → 项目 UID 映射 | MySQL `zhiyan_zhiku.legacy_import_map` |
| 数据集课程生成的知识纲要原文 | `server/media/generated/legacy_docs/*.md` |
| 8 门核心课程讲义原文 | `server/seed/content/*.md` |

### 4.6 无 MySQL 时的 SQLite 兜底

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

### 4.7 不配置 DeepSeek 时

保持 `DEEPSEEK_API_KEY` 为空，或设置 `LLM_PROVIDER=local`。后端会使用基于真实检索证据的本地模板生成流式回答，引用、思考步骤、工具调用和检索日志仍正常工作，方便离线评审。

### 4.8 环境变量与依赖清单

环境变量模板：

- 前端：`.env.example`（`VITE_API_BASE_URL`，默认 `/api/v1`）
- 后端：`server/.env.example`（数据库、DeepSeek、Embedding 等配置）

本地分别复制为 `.env.local` 与 `server/.env` 后填写。所有 `.env` 文件均已被 `.gitignore` 忽略，仓库中只保留模板；**请勿提交真实 API Key 或数据库密码**。

依赖清单：

- 前端：`package.json`（Vue 3、Vite、Pinia、Element Plus、ECharts、markdown-it 等）
- 后端：`server/requirements.txt`（Django 6、DRF、SimpleJWT、PyMySQL、openai、pypdf、python-docx 等）

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
│  ├─ seed/manifest.py               # 课程、图谱、数据集字段映射
│  └─ tests/                         # API / SSE / 检索 / 上传测试
└─ sql/                              # MySQL 建库、建表、种子、校验 SQL
```

种子规模：8 门核心课程、50 个知识点、8 份课程讲义、50 个向量片段、23 个图谱节点、33 条客观先修边。课程数据集包含 132 门课程元数据、58 个保留知识点、37 条先修边和 126 条课程—知识点关系；核心 RAG 课程仍为 8 门。执行数据集导入链路后，数据库达到 135 门课程、221 个知识点、135 份文档、600 个向量片段，覆盖 135 门课程。

## 6. 数据库设计

### 6.1 课程数据集字段映射

| 数据集字段 | 本项目字段 | 处理 |
| --- | --- | --- |
| `courses` | `courses` | 保留课程编号、名称、教师、学校、简介、类型、封面、课程链接、视频链接；新增 uid、short_name、color、数值 popularity、排序和时间戳 |
| `knowledge_nodes` | `knowledge_points` | 保留名称、描述、难度；新增课程、章节、序号、标签、稳定知识点 ID、源节点 ID |
| `knowledge_edges` | `graph_nodes` + `graph_edges` | 保留先修边结构；补充 Transformer、LLM、RAG、向量数据库等节点；新增可读 reason |
| `course_knowledge` | 课程与知识点关联 | 重组为课程索引和知识点章节关系 |

### 6.2 数据范围说明

本项目只使用课程、知识点、先修关系和课程知识结构数据；推荐、选课、收藏、学习历史、学习画像等业务不在本项目范围内。

### 6.3 新增 RAG 表

| 表 | 作用 |
| --- | --- |
| `documents` | 课程文档元数据、解析状态、chunk 数、上传人 |
| `document_chunks` | 原文、章节、标签、tokens、embedding JSON、向量模型信息 |
| `conversations` / `messages` | 服务端会话与消息 |
| `citations` | 消息级引用快照（课程、知识点、来源、分数） |
| `agent_runs` / `agent_steps` / `agent_tool_calls` | Agent 运行、思考步骤、工具调用与耗时 |
| `retrieval_logs` / `retrieval_log_items` | 每次检索的参数、候选数、召回分数、阶段耗时 |
| `rag_settings` | 每用户 Top-K / 阈值 / 检索模式 |
| `legacy_import_map` | 数据集 ID → 项目 UID 溯源映射 |

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
- 本项目不包含推荐系统；问答与检索由 RAG-Agent 完成。
- 上传是同步解析，适合现场演示；生产环境可将 `ingest_document` 放入 Celery/RQ 任务。
- 课程数据集没有完整的课程讲义内容，因此 RAG 课程内容由 8 份课程讲义种子重新建设，并通过知识点与文档索引补充检索证据。
- DeepSeek Key 仅存放在 `server/.env`，已被 `.gitignore` 排除；请勿提交或写入数据库/SQL/README。

## 12. 团队信息

| 成员 | 角色 | 主要分工 |
| --- | --- | --- |
| Hua-Jian-Xiao | 项目负责人 / 全栈开发 | 架构设计、Vue 前端工作台、Django 后端、RAG 检索与 Agent 链路、文档与部署 |

- 联系方式：1419955217@qq.com
