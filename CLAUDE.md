# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

详见 AGENT.md 获取完整的项目架构、目录结构和设计模式说明。

## 项目简介

基于 LangGraph 的 Text-to-SQL 智能体系统。自然语言提问 → 自动检索元数据知识库 → 生成/校验/执行 SQL → 返回结果。同时支持数据源注册、AI 自动分析 Schema、草稿版本管理、知识库发布、数据大屏可视化。

## 常用命令

### 后端

```bash
# 启动 FastAPI 开发服务器
uv run python main.py

# 安装/同步依赖
uv sync

# 运行 CLI 脚本（从 YAML 构建知识库）
uv run python -m app.scripts.build_meta_knowledge
```

### 前端

```bash
cd frontend

# 开发服务器
npm run dev

# 生产构建
npm run build
```

## 技术栈

| 层面 | 技术 |
|------|------|
| Web 框架 | FastAPI (SSE 流式响应) |
| Agent 框架 | LangGraph (StateGraph + Context + Runtime) |
| LLM | LangChain + OpenAI 兼容接口 |
| 元数据库 | MySQL (asyncmy + SQLAlchemy 2.0 async) |
| 向量库 | Qdrant (async client) |
| 全文检索 | Elasticsearch 8 (async, ik 分词) |
| Embedding | HuggingFace Endpoint (BAAI/bge-large-zh-v1.5) |
| 前端 | Vue 3 + Vite + Ant Design Vue + Pinia |
| 包管理 | uv (Python) / npm (前端) |

## 核心架构

### 三 Agent 架构

- **Chat Agent** (`app/agents/chat_agent/`): Text-to-SQL 查询链路。关键词提取 → 向量/全文召回 → LLM 筛选 → SQL 生成 → EXPLAIN 校验 → 纠错重试(最多3次) → 执行
- **Metadata Agent** (`app/agents/metadata_agent/`): 元数据同步链路。analyze_schema → classify_tables → infer_tables → infer_columns → infer_metrics → assemble_config → validate_config → build_knowledge
- **Viz Agent** (`app/agents/viz_agent/`): 数据可视化链路。推荐图表(recommend_chart)、生成仪表盘(parse_intent → generate_sqls → generate_charts → plan_layout → assemble_dashboard)

### 分层架构（强制）

```
Router (HTTP 请求解析/响应格式化)
  → Service (业务编排，可调用多个 Repository/Agent)
    → Repository (纯数据读写，返回 Entity，不返回 ORM Model)
```

- Router 禁止直接 import Repository
- Service 抛 ValueError 表示业务异常，Router 统一转 HTTPException
- Repository 通过 Mapper 完成 Entity ↔ ORM Model 转换

### 请求链路

```
Router → Service (流式编排) → Agent.astream(stream_mode="custom") → SSE 响应
```

### 动态数据源

`app/clients/datasource/`: DatasourceManager 单例管理数据源引擎缓存池，DatasourceFactory 抽象工厂按 db_type 获取 MySQL/PostgreSQL 实现。

### 知识库存储

三元存储并行写入（先删后插策略）：
- MySQL (元数据库)：table_info, column_info, metric_info, column_metric
- Qdrant (向量检索)：column_info_collection (按 table_id 过滤), metric_collection (按 metric_id 过滤)
- Elasticsearch (全文检索)：value_index (按 column_id 过滤, ik_max_word 分词)

## 配置

- 环境变量：`.env` 文件，通过 `pydantic-settings` 加载，嵌套分隔符 `__`（如 `DB_META__HOST`）
- LLM 配置：`LLM__MODEL_NAME`, `LLM__API_KEY`, `LLM__BASE_URL`，使用 OpenAI 兼容接口
- 密码加密：数据源密码通过 `app.core.crypto` 模块 AES-256-GCM 加密存储

## 标识符安全

SQL 中表名/列名等标识符必须通过 `validate_identifier()` 校验后再拼接，禁止直接 f-string 拼接用户输入。

## 编码规范

- 所有 I/O 操作使用 async/await
- 通过 FastAPI Depends 进行依赖注入
- 代码注释使用英文
