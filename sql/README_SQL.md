# 数据库 SQL 使用说明

本目录是“智研知库”的 MySQL 8 数据库交付物，包含建库、业务表结构、种子数据和完整性校验脚本。

## 文件

| 文件 | 用途 |
| --- | --- |
| `00_create_database.sql` | 创建 `zhiyan_zhiku` 数据库 |
| `01_schema_mysql.sql` | 全部业务表、索引、外键、Django 基础表与 `django_migrations` |
| `02_seed_mysql.sql` | 8 门核心课程、50 个知识点、8 份种子文档、50 个向量片段、23 个图谱节点、33 条依赖、演示账号、RAG 配置 |
| `03_verify.sql` | 数据量、空向量、引用表和日志表完整性检查 |

## 导入

```bash
mysql -uroot -p < 00_create_database.sql
mysql -uroot -p < 01_schema_mysql.sql
mysql -uroot -p < 02_seed_mysql.sql
mysql -uroot -p < 03_verify.sql
```

也可以直接使用后端命令重建种子：

```bash
cd server
python manage.py migrate
python manage.py seed_all --reset
```

## 数据模型

- `courses`：课程编号、名称、教师、学校、简介、分类、封面、课程链接、数值热度与稳定 UID。
- `knowledge_points`：知识点名称、描述、难度、课程、章节、标签与稳定 UID。
- `graph_nodes` / `graph_edges`：知识图谱节点、分类和客观先修关系。
- `documents` / `document_chunks`：课程文档元数据、原文切分、tokens、标签与 embedding JSON 向量。
- `conversations` / `messages` / `citations`：服务端会话、消息与可追溯引用。
- `agent_runs` / `agent_steps` / `agent_tool_calls`：Agent 运行、思考步骤、工具调用与耗时。
- `retrieval_logs` / `retrieval_log_items`：召回参数、候选数、过滤结果、分数和阶段耗时。
- `rag_settings`：按用户保存 Top-K、阈值和检索模式。
- `legacy_import_map`：数据集 ID → 项目 UID 溯源映射。

## 数据范围

本项目只使用课程、知识点、先修关系和课程知识结构数据；推荐、选课、收藏、学习历史、学习画像等业务不在本项目范围内。

> 数据库种子不包含 DeepSeek API Key。密钥只允许存在于 `server/.env`，且 `.env` 已被 `.gitignore` 排除。
