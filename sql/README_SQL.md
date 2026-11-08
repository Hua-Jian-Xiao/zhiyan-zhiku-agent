# 数据库 SQL 使用说明

本目录是“智研知库”的完整 MySQL 8 数据库交付物。

## 文件

| 文件 | 用途 |
| --- | --- |
| `00_create_database.sql` | 创建 `zhiyan_zhiku` 数据库 |
| `01_schema_mysql.sql` | 全部业务表、索引、外键、Django 基础表与 `django_migrations` |
| `02_seed_mysql.sql` | 8 门课程、50 个知识点、8 份种子文档、50 个向量片段、23 个图谱节点、33 条依赖、演示账号、RAG 配置 |
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

## 数据表

- `documents` / `document_chunks` / `embedding` JSON：课程文档入库和轻量向量知识库。
- `conversations` / `messages` / `citations`：服务端会话与可追溯引用。
- `agent_runs` / `agent_steps` / `agent_tool_calls`：思考步骤、工具调用与耗时。
- `retrieval_logs` / `retrieval_log_items`：召回、阈值过滤、重排序和分数可观测性。
- `rag_settings`：按用户保存 Top-K、阈值和检索模式。

> 数据库种子不包含 DeepSeek API Key。密钥只允许存在于 `server/.env`，且 `.env` 已被 `.gitignore` 排除。
