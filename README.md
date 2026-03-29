- TraceRAG

  一个强调工程化、可观测、可测试、可扩展的 RAG 项目。

  TraceRAG 的目标不是只把答案"生成出来"，而是把文档导入、切块、向量化、检索、带来源回答、评估与后续 tracing 拆成可独立验证的阶段，逐步演进成一个可维护、可解释、可复盘的生产级 RAG。

  > 核心闭环：文档导入 → 切块 → Embedding → 向量检索 → 带 `sources` 的回答 → Eval 驱动迭代

  ## 项目目标

  - 先把 RAG 主链路跑通，再逐步补齐评估、可观测性和工程分层。
  - 先独立验证 retrieval，再接入 LLM，降低排错成本。
  - 所有优化尽量有数据支撑，不靠"回答看起来像对了"的主观感觉。
  - 在保留学习友好度的前提下，采用更贴近 2026 工程实践的方案：`pgvector`、Alembic、Eval、Hybrid Search、Tracing。

  ## 当前实现

  - [x] `POST /import`：导入文档并完成切块，写入 `documents` 和 `chunks`
  - [x] `POST /embed/{document_id}`：为指定文档的所有 chunk 生成向量并写入 pgvector
  - [x] `GET /retrieve`：支持向量检索、Top-K 返回、按 `source` 过滤
  - [x] `GET /ask`：LangGraph 编排 retrieve → generate，返回 `answer + sources + duration_ms`，Redis 缓存重复 query
  - [x] `GET /retrieve_hybrid`：向量检索 + BM25 + RRF 融合 + 关键词 rerank
  - [x] Alembic 迁移、`vector` 扩展初始化、HNSW 索引迁移
  - [x] Langfuse 全链路 tracing + prompt 版本管理
  - [x] LLM-as-a-judge 评估：faithfulness 0.97、answer_relevance 1.00
  - [x] API Key 认证

  ## 架构概览

  ```mermaid
  flowchart LR
      A["POST /import"] --> B["Document"]
      A --> C["split_text()"]
      C --> D["Chunk"]
      E["POST /embed/{document_id}"] --> F["text-embedding-v3"]
      F --> D
      G["GET /retrieve"] --> H["Query Embedding"]
      H --> D
      D --> I["Vector Top-K"]
      J["GET /retrieve_hybrid"] --> K["BM25 + Vector + RRF + rerank"]
      K --> I
      L["GET /ask"] --> M["Redis Cache"]
      M -->|cache miss| N["LangGraph"]
      N --> H
      I --> O["build_prompt()"]
      O --> P["qwen-plus"]
      P --> Q["answer + sources + duration_ms"]
      L -.->|trace| R["Langfuse"]
      Q -.->|eval| S["LLM-as-a-judge\nfaithfulness · answer_relevance"]
  ```

  `eval/` 目录包含固定问题集（`questions.json`）和 LLM-as-a-judge 评估脚本（`eval_llm.py`），对每条回答从 faithfulness（忠实度）和 answer_relevance（相关性）两个维度自动打分，平均分分别为 0.97 和 1.00。

  ## 技术栈

  | 模块            | 当前选择                                   | 用途                                        |
  | --------------- | ------------------------------------------ | ------------------------------------------- |
  | API 框架        | FastAPI                                    | 提供接口与自动文档                          |
  | 数据库          | PostgreSQL + pgvector                      | 统一存储文档、chunk、embedding 和元数据     |
  | ORM / 迁移      | SQLAlchemy + Alembic                       | 模型定义与 schema 演进                      |
  | 切块            | LangChain `RecursiveCharacterTextSplitter` | 中文友好的基础切块                          |
  | Embedding / LLM | DashScope 兼容 OpenAI SDK                  | 当前使用 `text-embedding-v3` 和 `qwen-plus` |
  | 工作流编排      | LangGraph                                  | retrieve → generate 节点，支持条件分支      |
  | 检索            | pgvector cosine + PostgreSQL FTS           | 向量检索、BM25 风格全文检索、Hybrid Search  |
  | 缓存            | Redis                                      | query cache，相同问题第二次响应 <5ms        |
  | 可观测性        | Langfuse                                   | 全链路 trace、prompt 版本管理               |
  | 依赖管理        | uv                                         | Python 环境与依赖管理                       |
  | 本地依赖服务    | Docker Compose                             | 启动 PostgreSQL / Redis                     |
  | 评估            | LLM-as-a-judge                             | faithfulness + answer_relevance 自动打分    |

  ## 目录结构

  ```text
  TraceRAG/
  ├── app/
  │   ├── api/          # 路由层
  │   ├── core/         # 配置、认证
  │   ├── db/           # 数据库连接与 session
  │   ├── models/       # SQLAlchemy 模型
  │   ├── repositories/ # 数据访问层（SQL 封装）
  │   ├── schemas/      # Pydantic 请求模型
  │   ├── services/     # 切块、embedding、retrieval、LLM、hybrid、graph 逻辑
  │   ├── prompts/      # Prompt 模板
  │   └── main.py
  ├── alembic/          # 数据库迁移
  ├── eval/             # 评估问题集、脚本与结果
  ├── docker-compose.yml
  ├── pyproject.toml
  ├── .env.example
  └── README.md
  ```

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

  `docker-compose.yml` 会启动：

  - PostgreSQL（镜像：`ankane/pgvector`）
  - Redis

  ### 4. 配置环境变量

  ```bash
  cp .env.example .env
  # 填入 DASHSCOPE_API_KEY、LANGFUSE_* 和 API_KEY
  ```

  ### 5. 初始化数据库

  ```bash
  uv run alembic upgrade head
  ```

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

  ## API 认证

  所有接口需在请求头携带 API Key：

  ```
  x-api-key: <your-key>
  ```

  ## API 使用示例

  ### 1. 导入文档

  ```bash
  curl -X POST "http://127.0.0.1:8000/import" \
    -H "Content-Type: application/json" \
    -H "x-api-key: <your-key>" \
    -d '{
      "title": "RAG 切块实验",
      "content": "RAG 系统的第一步通常不是直接把整篇文档拿去做检索，而是先把文档拆成多个更小的文本块。",
      "source": "day5-demo"
    }'
  ```

  ### 2. 为文档生成向量

  ```bash
  curl -X POST "http://127.0.0.1:8000/embed/1" -H "x-api-key: <your-key>"
  ```

  ### 3. 向量检索

  ```bash
  curl -H "x-api-key: <your-key>" \
    "http://127.0.0.1:8000/retrieve?q=为什么要先独立验证 retrieval&top_k=5"
  ```

  按来源过滤：

  ```bash
  curl -H "x-api-key: <your-key>" \
    "http://127.0.0.1:8000/retrieve?q=chunk_size 和 chunk_overlap&top_k=5&source=day7-long-demo"
  ```

  ### 4. 提问并生成带来源回答

  ```bash
  curl -H "x-api-key: <your-key>" \
    "http://127.0.0.1:8000/ask?q=为什么 embedding 的输入单位是 chunk，不是 document&top_k=3"
  ```

  返回结果中包含：

  - `answer`
  - `sources`
  - `duration_ms`
  - `is_cached`（命中缓存时为 `true`）

  ### 5. Hybrid Search

  ```bash
  curl -H "x-api-key: <your-key>" \
    "http://127.0.0.1:8000/retrieve_hybrid?q=为什么要先验证 retrieval&top_k=5"
  ```

  Hybrid Search 由三部分组成：向量检索、PostgreSQL 全文检索、RRF 融合 + 简单关键词重排。

  ## 评估

  ```bash
  # 先启动服务，再运行评估
  uv run python eval/run_eval.py   # 调用 /ask，结果写入 eval/results.json
  uv run python eval/eval_llm.py   # LLM-as-a-judge 打分
  ```
