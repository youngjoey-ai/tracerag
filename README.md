# TraceRAG

一个强调工程化、可观测、可测试、可扩展的 RAG 项目。TraceRAG 的目标不是只把答案“生成出来”，而是把文档导入、切块、向量化、检索、带来源回答、评估与后续 tracing 拆成可独立验证的阶段，逐步演进成一个可维护、可解释、可复盘的生产级 RAG。

> 核心闭环：文档导入 -> 切块 -> Embedding -> 向量检索 -> 带 `sources` 的回答 -> Eval 驱动迭代

## 项目目标

- 先把 RAG 主链路跑通，再逐步补齐评估、可观测性和工程分层。
- 先独立验证 retrieval，再接入 LLM，降低排错成本。
- 所有优化尽量有数据支撑，不靠“回答看起来像对了”的主观感觉。
- 在保留学习友好度的前提下，采用更贴近 2026 工程实践的方案：`pgvector`、Alembic、Eval、Hybrid Search、Tracing。

## 当前实现

- [x] `POST /import`：导入文档并完成切块，写入 `documents` 和 `chunks`
- [x] `POST /embed/{document_id}`：为指定文档的所有 chunk 生成向量并写入 pgvector
- [x] `GET /retrieve`：支持向量检索、Top-K 返回、按 `source` 过滤
- [x] `GET /ask`：返回 `answer + sources + duration_ms`
- [x] `GET /retrieve_hybrid`：支持向量检索 + BM25 + RRF 融合 + 简单 rerank
- [x] Alembic 迁移、`vector` 扩展初始化、HNSW 索引迁移
- [x] 基础评估脚本与样例结果：`eval/questions.json`、`eval/run_eval.py`、`eval/results.json`

## 架构概览

```mermaid
flowchart LR
    A["POST /import"] --> B["Document"]
    A --> C["split_text()"]
    C --> D["Chunk"]
    E["POST /embed/{document_id}"] --> F["text-embedding-v4"]
    F --> D
    G["GET /retrieve"] --> H["Query Embedding"]
    H --> D
    D --> I["Vector Top-K"]
    J["GET /retrieve_hybrid"] --> K["BM25 + Vector + RRF + rerank"]
    K --> I
    L["GET /ask"] --> H
    I --> M["build_prompt()"]
    M --> N["qwen-plus"]
    N --> O["answer + sources + duration_ms"]
```

当前代码把 RAG 链路拆成了几个容易单独验证的层：

- API 层：`/import`、`/embed/{document_id}`、`/retrieve`、`/ask`、`/retrieve_hybrid`
- 数据层：`documents`、`chunks`、`qa_logs`
- 检索层：向量检索、元数据过滤、HNSW 索引、Hybrid Search
- 生成层：基于检索结果拼接 prompt，再调用 LLM 生成最终回答
- 评估层：用固定问题集跑通基础问答回归

## 技术栈

| 模块 | 当前选择 | 用途 |
| --- | --- | --- |
| API 框架 | FastAPI | 提供接口与自动文档 |
| 数据库 | PostgreSQL + pgvector | 统一存储文档、chunk、embedding 和元数据 |
| ORM / 迁移 | SQLAlchemy + Alembic | 模型定义与 schema 演进 |
| 切块 | LangChain `RecursiveCharacterTextSplitter` | 中文友好的基础切块 |
| Embedding / LLM | DashScope 兼容 OpenAI SDK | 当前使用 `text-embedding-v4` 和 `qwen-plus` |
| 检索 | pgvector cosine + PostgreSQL FTS | 向量检索、BM25 风格全文检索、Hybrid Search |
| 依赖管理 | uv | Python 环境与依赖管理 |
| 本地依赖服务 | Docker Compose | 启动 PostgreSQL / Redis |
| 评估 | 自定义脚本 | 基础问答回归，后续扩展 recall@k / Ragas |

## 目录结构

```text
TraceRAG/
├── app/
│   ├── api/         # 路由层
│   ├── db/          # 数据库连接与 session
│   ├── models/      # SQLAlchemy 模型
│   ├── schemas/     # Pydantic 请求模型
│   ├── services/    # 切块、embedding、retrieval、LLM、hybrid 逻辑
│   └── main.py
├── alembic/         # 数据库迁移
├── eval/            # 评估问题集、脚本与结果
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

执行手册中的目标结构还包括 `core/`、`repositories/`、`prompts/`、`tests/` 等目录，当前仓库还在从 MVP 向更完整工程分层演进的过程中。

## 快速开始

### 1. 准备环境

- Python 3.12+
- `uv`
- Docker / Docker Compose

### 2. 安装依赖

```bash
uv sync
```

### 3. 启动基础服务

```bash
docker compose up -d
```

当前 `docker-compose.yml` 会启动：

- PostgreSQL（镜像：`ankane/pgvector`）
- Redis（已预留，当前主链路尚未接入缓存）

### 4. 配置 API Key

当前代码会在模块导入阶段初始化 LLM / Embedding 客户端，所以启动前必须先提供 `DASHSCOPE_API_KEY`：

```bash
export DASHSCOPE_API_KEY=your_dashscope_api_key
```

如果你使用 `.env`，需要先手动加载，因为当前代码还没有自动执行 `python-dotenv`：

```bash
set -a
source .env
set +a
```

### 5. 初始化数据库

```bash
uv run alembic upgrade head
```

默认数据库地址已经和 `docker-compose.yml` 对齐：

```text
postgresql+psycopg://tracerag:tracerag@localhost:5432/tracerag
```

这个地址当前分别写在 `app/db/session.py` 和 `alembic.ini` 中。

### 6. 启动服务

```bash
uv run uvicorn app.main:app --reload
```

启动后可以访问：

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### 7. 健康检查

```bash
curl http://127.0.0.1:8000/health
```

返回：

```json
{"status":"ok"}
```

## API 使用示例

### 1. 导入文档

```bash
curl -X POST "http://127.0.0.1:8000/import" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "RAG 切块实验",
    "content": "RAG 系统的第一步通常不是直接把整篇文档拿去做检索，而是先把文档拆成多个更小的文本块。",
    "source": "day5-demo"
  }'
```

### 2. 为文档生成向量

```bash
curl -X POST "http://127.0.0.1:8000/embed/1"
```

### 3. 向量检索

```bash
curl "http://127.0.0.1:8000/retrieve?q=为什么要先独立验证 retrieval&top_k=5"
```

按来源过滤：

```bash
curl "http://127.0.0.1:8000/retrieve?q=chunk_size 和 chunk_overlap&top_k=5&source=day7-long-demo"
```

### 4. 提问并生成带来源回答

```bash
curl "http://127.0.0.1:8000/ask?q=为什么 embedding 的输入单位是 chunk，不是 document&top_k=3"
```

返回结果中会包含：

- `answer`
- `sources`
- `duration_ms`

### 5. Hybrid Search

```bash
curl "http://127.0.0.1:8000/retrieve_hybrid?q=为什么要先验证 retrieval&top_k=5"
```

当前 Hybrid Search 由三部分组成：

- 向量检索
- PostgreSQL 全文检索
- RRF 融合 + 简单关键词重排

## 评估

仓库已经包含一个最小可用的评估脚本：

```bash
uv run python eval/run_eval.py
```

当前评估流程会：

1. 读取 `eval/questions.json`
2. 逐个调用 `/ask`
3. 将结果写入 `eval/results.json`

这一步适合做最基础的问答回归。根据执行手册，后续会继续补齐：

- `pytest` 自动化测试
- recall@k / precision 等检索指标
- faithfulness / answer relevance / context precision
- Ragas 自动化打分

接下来的优先级建议：

1. 先把 `pytest` 和回归评估补起来，形成稳定基线。
2. 再做 chunking 参数实验和 retrieval 指标对比，避免盲调 prompt。
3. 然后接入 Langfuse，看 trace、耗时和上下文质量。
4. 最后再推进 Redis、LangGraph、Ragas 和更完整的工程分层。

## 这个项目适合什么场景

- 学习一个更接近真实工程实践的 RAG 项目怎么逐步搭起来
- 面试时讲清楚“为什么先验证 retrieval，再去优化生成”
- 把单纯的 RAG Demo 升级成一个有数据层、评估层和可扩展路径的项目
- 作为后续接 Langfuse、LangGraph、Ragas、缓存和权限控制的基础骨架
