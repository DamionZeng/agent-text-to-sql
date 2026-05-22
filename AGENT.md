# AGENT.md — AI Agent 项目理解指南

## 项目概述

**agent-text2sql** 是一个基于 LangGraph 的 Text-to-SQL 智能体系统。用户通过自然语言提问，系统自动检索元数据知识库、生成 SQL、校验并执行，返回查询结果。同时提供元数据管理能力：数据源注册、AI 自动分析 Schema、配置校验、草稿版本管理、知识库发布同步。

## 技术栈

| 层面 | 技术 |
|------|------|
| Web 框架 | FastAPI (SSE 流式响应) |
| Agent 框架 | LangGraph (StateGraph + Context + Runtime) |
| LLM | LangChain + OpenAI 兼容接口 (默认 DeepSeek) |
| Embedding | HuggingFace Endpoint (BAAI/bge-large-zh-v1.5) |
| 元数据库 | MySQL (asyncmy + SQLAlchemy 2.0 async) |
| 向量库 | Qdrant (async client) |
| 全文检索 | Elasticsearch 8 (async, ik 分词) |
| 前端 | Vue 3 + Vite |
| 配置 | pydantic-settings (.env) + OmegaConf (YAML) |

## 项目结构

```
agent-text2sql/
├── main.py                          # FastAPI 入口，挂载路由、中间件
├── pyproject.toml                   # 依赖管理 (uv)
├── conf/
│   └── meta_conf.yaml               # 元数据配置示例 (表/字段/指标定义)
├── prompts/                         # LLM Prompt 模板 (.prompt 文件)
│   ├── classify_tables.prompt
│   ├── infer_tables.prompt
│   ├── infer_columns.prompt
│   ├── infer_metrics.prompt
│   ├── generate_sql.prompt
│   ├── correct_sql.prompt
│   └── ...                          # 其他 prompt
├── app/
│   ├── conf/                        # 配置层
│   │   ├── app_config.py            #   AppSettings (pydantic-settings, 读 .env)
│   │   └── meta_config.py           #   MetaConfig / TableConfig / ColumnConfig / MetricConfig
│   ├── core/                        # 核心基础设施
│   │   ├── lifespan.py              #   应用生命周期 (启动初始化、关闭清理、自动同步表结构)
│   │   ├── log.py                   #   Loguru 日志
│   │   └── context.py               #   request_id 上下文变量
│   ├── clients/                     # 外部客户端管理器 (单例)
│   │   ├── mysql_client_manager.py  #   元数据库 MySQL 连接池
│   │   ├── qdrant_client_manager.py #   Qdrant 异步客户端
│   │   ├── es_client_manager.py     #   Elasticsearch 异步客户端
│   │   ├── embedding_client_manager.py # HuggingFace Embedding 客户端
│   │   └── datasource/             #   动态数据源 (抽象工厂 + 单例缓存 + 建造者)
│   │       ├── config.py            #     DatasourceConfig 数据类
│   │       ├── builder.py           #     DatasourceConfigBuilder (建造者模式)
│   │       ├── factory.py           #     DatasourceFactory (抽象工厂, MySQL/PG)
│   │       └── manager.py           #     DatasourceManager (单例, 引擎缓存池)
│   ├── entities/                    # 领域实体 (dataclass, 与存储无关)
│   │   ├── datasource.py            #   Datasource
│   │   ├── table_info.py            #   TableInfo
│   │   ├── column_info.py           #   ColumnInfo
│   │   ├── metric_info.py           #   MetricInfo
│   │   ├── column_metric.py         #   ColumnMetric
│   │   ├── value_info.py            #   ValueInfo
│   │   └── meta_draft.py            #   MetaDraft
│   ├── models/                      # SQLAlchemy ORM 模型 (MySQL 表映射)
│   │   ├── base.py                  #   DeclarativeBase
│   │   ├── datasource.py            #   DatasourceMySQL
│   │   ├── table_info.py            #   TableInfoMySQL
│   │   ├── column_info.py           #   ColumnInfoMySQL
│   │   ├── metric_info.py           #   MetricInfoMySQL
│   │   ├── column_metric.py         #   ColumnMetricMySQL
│   │   └── meta_draft.py            #   MetaDraftMySQL
│   ├── repositories/                # 数据访问层
│   │   ├── mysql/meta/              #   元数据库 Repository
│   │   │   ├── meta_mysql_repository.py   # TableInfo/ColumnInfo/MetricInfo/ColumnMetric CRUD
│   │   │   ├── datasource_repository.py   # Datasource CRUD
│   │   │   ├── meta_draft_repository.py   # MetaDraft 版本管理
│   │   │   └── mappers/             #     Entity <-> Model 转换
│   │   ├── qdrant/                  #   向量库 Repository
│   │   │   ├── column_qdrant_repository.py # ColumnInfo 向量检索 (按 table_id 删)
│   │   │   └── metric_qdrant_repository.py # MetricInfo 向量检索 (按 metric_id 删)
│   │   ├── es/                      #   全文检索 Repository
│   │   │   └── value_es_respository.py     # ValueInfo 索引/检索 (按 column_id 删)
│   │   └── db_executor/             #   数据库查询适配器 (策略模式)
│   │       ├── base.py              #     DbQueryExecutor 抽象基类
│   │       ├── mysql_executor.py    #     MySQL 查询实现
│   │       ├── postgresql_executor.py #   PostgreSQL 查询实现
│   │       └── factory.py           #     get_executor(db_type) 工厂
│   ├── services/                    # 服务层 (编排 Repository + Agent)
│   │   ├── query_service.py         #   查询服务 (流式调用 Data Agent)
│   │   ├── metadata_service.py      #   元数据服务 (流式调用 Meta Agent)
│   │   └── meta_knowledge_service.py #  知识库构建服务 (写入 MySQL/Qdrant/ES)
│   ├── api/                         # API 层
│   │   ├── dependencies.py          #   FastAPI 依赖注入
│   │   ├── routers/
│   │   │   ├── query_router.py      #   POST /api/query
│   │   │   └── metadata_router.py   #   /api/metadata/* (数据源/草稿/发布/同步)
│   │   └── schemas/                 #   Pydantic 请求/响应模型
│   ├── agent/                       # Data Agent (Text-to-SQL 查询链路)
│   │   ├── state.py                 #   DataAgentState
│   │   ├── context.py               #   DataAgentContext
│   │   ├── graph.py                 #   Graph 定义
│   │   ├── llm.py                   #   LLM 实例 (init_chat_model)
│   │   └── nodes/                   #   各节点实现
│   │       ├── extract_keywords.py  #     提取关键词
│   │       ├── recall_column.py     #     向量召回字段
│   │       ├── recall_value.py      #     全文召回值
│   │       ├── recall_metric.py     #     向量召回指标
│   │       ├── merge_retrieved_info.py #  合并召回结果
│   │       ├── filter_table.py      #     LLM 筛选表
│   │       ├── filter_metric.py     #     LLM 筛选指标
│   │       ├── add_extra_context.py #     添加日期/DB版本上下文
│   │       ├── generate_sql.py      #     LLM 生成 SQL
│   │       ├── validate_sql.py      #     EXPLAIN 校验 SQL
│   │       ├── correct_sql.py       #     LLM 修正 SQL
│   │       └── run_sql.py           #     执行 SQL
│   ├── metadata_agent/              # Meta Agent (元数据分析/同步链路)
│   │   ├── state.py                 #   MetaAgentState
│   │   ├── context.py               #   MetaAgentContext
│   │   ├── graph.py                 #   两个 Graph: draft + publish
│   │   └── nodes/
│   │       ├── analyze_schema.py    #     连接数据源获取 Schema
│   │       ├── classify_tables.py   #     AI 分类维度表/事实表
│   │       ├── infer_tables.py      #     AI 推断表配置
│   │       ├── infer_columns.py     #     AI 推断字段配置
│   │       ├── infer_metrics.py     #     AI 推断指标配置
│   │       ├── assemble_config.py   #     组装 MetaConfig
│   │       ├── validate_config.py   #     校验配置完整性
│   │       └── build_knowledge.py   #     写入知识库
│   ├── prompt/
│   │   └── prompt_loader.py         #   加载 .prompt 文件
│   └── scripts/
│       └── build_meta_knowledge.py  #   CLI 脚本: 从 YAML 构建知识库
└── frontend/                        # Vue 3 前端
    └── src/
        ├── views/
        │   ├── chat/ChatPage.vue
        │   └── datasource/
        │       ├── DatasourceList.vue
        │       └── DatasourceDetail.vue
        └── ...
```

## 核心架构

### 双 Agent 架构

系统包含两条独立的 Agent 链路：

```
┌─────────────────────────────────────────────────────────────────┐
│  Data Agent (查询链路)                                           │
│  POST /api/query                                                │
│                                                                 │
│  extract_keywords                                               │
│       ├─→ recall_column ──→ merge_retrieved_info ──→ filter_table ──→ add_extra_context ──→ generate_sql ──→ validate_sql ──→ run_sql
│       ├─→ recall_value  ──→ merge_retrieved_info ──→ filter_metric ──┘
│       └─→ recall_metric ──→ merge_retrieved_info ──→ ...         │
│                                                                 │
│  校验失败 → correct_sql → validate_sql (最多重试 3 次)           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Meta Agent (元数据链路)                                         │
│                                                                 │
│  Graph 1: draft (AI 同步)                                       │
│  POST /api/metadata/datasources/{id}/sync                       │
│  analyze_schema → classify_tables → infer_tables                │
│      → infer_columns → infer_metrics → assemble_config          │
│      → validate_config ─→ (valid? END : infer_tables 重试)      │
│                                                                 │
│  Graph 2: publish (知识库发布)                                   │
│  POST /api/metadata/datasources/{id}/publish                    │
│  build_knowledge → END                                          │
└─────────────────────────────────────────────────────────────────┘
```

### 请求链路

```
Router → Service (流式编排) → Agent.astream(stream_mode="custom") → SSE 响应
```

- **Router**: 接收 HTTP 请求，依赖注入 Service
- **Service**: 构建 Agent State + Context，调用 `graph.astream()`，yield SSE 事件
- **Agent Node**: 通过 `runtime.stream_writer` 向前端推送进度/结果

### 数据流向

```
用户数据源 (MySQL/PG/...)
       │
       ▼ (analyze_schema: DbQueryExecutor)
  Raw Schema (表名/字段名/类型/样例值)
       │
       ▼ (AI 推断)
  MetaConfig (tables + metrics)
       │
       ▼ (build_knowledge: 先删后插)
  ┌────────────────────────────────────────────┐
  │  MySQL (元数据库)                           │
  │    ├── table_info                           │
  │    ├── column_info                          │
  │    ├── metric_info                          │
  │    └── column_metric                        │
  │                                             │
  │  Qdrant (向量检索)                           │
  │    ├── column_info_collection (按 table_id) │
  │    └── metric_collection (按 metric_id)     │
  │                                             │
  │  Elasticsearch (全文检索)                    │
  │    └── value_index (按 column_id)           │
  └────────────────────────────────────────────┘
       │
       ▼ (查询时: recall → filter → generate → validate → run)
  SQL 结果
```

### 动态数据源架构

```
DatasourceManager (单例 + 引擎缓存)
  │
  ├── register(datasource) → DatasourceConfigBuilder → DatasourceConfig → _configs[id]
  ├── get_session(id) → _get_or_create_engine(id) → AsyncSession
  ├── get_config(id) → DatasourceConfig
  ├── unregister(id) → dispose engine + remove config
  └── close_all() → 应用关闭时调用

DatasourceFactory (抽象工厂)
  ├── MySQLDatasourceFactory → mysql+asyncmy://
  └── PostgreSQLDatasourceFactory → postgresql+asyncpg://

DbQueryExecutor (策略模式)
  ├── MySQLQueryExecutor → SHOW TABLES / SHOW COLUMNS / EXPLAIN
  └── PostgreSQLQueryExecutor → information_schema / EXPLAIN
```

## 关键设计模式

| 模式 | 应用位置 | 说明 |
|------|---------|------|
| 单例 + 缓存 | DatasourceManager | 全局唯一实例，缓存数据源引擎 |
| 抽象工厂 | DatasourceFactory / DbQueryExecutor | 按 db_type 获取对应实现 |
| 建造者 | DatasourceConfigBuilder | 链式构建 DatasourceConfig |
| 策略 + 路由 | DbQueryExecutor + get_executor() | 统一查询接口，消除 if-else |
| 依赖注入 | FastAPI Depends | Service/Repository 自动注入 |
| 先删后插 | Qdrant/ES/MySQL 知识库写入 | 按 ID 过滤删除旧数据再插入新数据，避免重复 |

## API 接口

### 查询

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/query` | 自然语言查询 (SSE 流式) |

### 数据源管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/metadata/datasources` | 创建数据源 |
| GET | `/api/metadata/datasources` | 列表 |
| GET | `/api/metadata/datasources/{id}` | 详情 |
| PUT | `/api/metadata/datasources/{id}` | 更新 |
| DELETE | `/api/metadata/datasources/{id}` | 删除 |
| POST | `/api/metadata/datasources/test` | 测试连接 (传参数) |
| POST | `/api/metadata/datasources/{id}/test` | 测试连接 (已保存) |

### 草稿管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/metadata/datasources/{id}/draft` | 获取最新草稿 |
| GET | `/api/metadata/datasources/{id}/draft/versions` | 版本列表 |
| GET | `/api/metadata/datasources/{id}/draft/versions/{draft_id}` | 指定版本 |
| POST | `/api/metadata/datasources/{id}/draft` | 保存草稿 |
| POST | `/api/metadata/datasources/{id}/draft/{draft_id}/rollback` | 回滚到指定版本 |
| DELETE | `/api/metadata/datasources/{id}/draft` | 删除所有草稿 |

### 发布与同步

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/metadata/datasources/{id}/publish` | 发布草稿到知识库 |
| POST | `/api/metadata/datasources/{id}/sync` | AI 自动分析并同步 (SSE 流式) |

## 数据库表

### 元数据库 (MySQL)

| 表名 | 说明 | 关键字段 |
|------|------|---------|
| datasource | 数据源配置 | id, type, host, port, database, username, password |
| table_info | 表元数据 | id (含前缀), name, role, description, datasource_id |
| column_info | 字段元数据 | id (table_id.col_name), name, type, role, table_id |
| metric_info | 指标元数据 | id (含前缀), name, description, relevant_columns |
| column_metric | 指标-字段关联 | metric_id, column_id |
| meta_draft | 草稿版本 | id, datasource_id, config_json, version, status |

### 向量库 (Qdrant)

| Collection | 过滤字段 | 说明 |
|------------|---------|------|
| column_info_collection | table_id | 字段名/别名 → 向量，payload 含完整 ColumnInfo |
| metric_collection | metric_id | 指标名/别名 → 向量，payload 含完整 MetricInfo + metric_id |

> **注意**: `metric_id` 是写入 Qdrant payload 时额外添加的辅助过滤字段，不属于 MetricInfo 实体。原因是 Qdrant 的 `id` 是 point 保留字段名，`FieldCondition(key="id")` 会与 point ID 冲突导致过滤失效。

### 全文检索 (Elasticsearch)

| Index | 过滤字段 | 说明 |
|-------|---------|------|
| value_index | column_id | 字段值全文检索，使用 ik_max_word 分词 |

## 配置

### 环境变量 (.env)

通过 `pydantic-settings` 加载，支持嵌套分隔符 `__`：

```
DB_META__HOST=localhost
DB_META__PORT=3306
DB_META__USER=root
DB_META__PASSWORD=xxx
DB_META__DATABASE=agent_text2sql

QDRANT__HOST=localhost
QDRANT__PORT=6333
QDRANT__EMBEDDING_SIZE=1024

EMBEDDING__HOST=localhost
EMBEDDING__PORT=8081
EMBEDDING__MODEL=BAAI/bge-large-zh-v1.5

ES__HOST=localhost
ES__PORT=9200

LLM__MODEL_NAME=gpt-5.2-codex
LLM__API_KEY=DASHSCOPE_API_KEY
LLM__BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

### YAML 元数据配置 (conf/meta_conf.yaml)

定义表结构、字段角色、指标等，用于 CLI 脚本 `build_meta_knowledge.py` 构建。

## 编码规范

### 分层架构（强制）

严格遵循 **Router → Service → Repository** 三层调用链，禁止跨层调用：

```
Router (HTTP 层)          → 只做请求解析/响应格式化，不包含业务逻辑
  │                         - 参数校验由 Pydantic Schema 完成
  │                         - 业务异常由 Service 抛出 ValueError，Router 统一转 HTTPException
  │                         - 禁止 Router 直接 import 或注入 Repository
  ▼
Service (业务层)          → 编排业务逻辑，可调用多个 Repository/Agent
  │                         - 所有业务校验在此完成，抛出 ValueError 表示业务异常
  │                         - 事务边界由 Service 控制
  │                         - 可调用 Repository、Agent、外部 Client
  ▼
Repository (数据访问层)   → 纯数据读写，不包含业务判断
                              - 每个 Repository 只操作单一数据源（MySQL/Qdrant/ES）
                              - 返回 Entity 对象，不返回 ORM Model
                              - 通过 Mapper 完成 Entity ↔ Model 转换
```

**关键规则**：

| 规则 | 说明 |
|------|------|
| Router 禁止直接调用 Repository | 所有数据访问必须通过 Service 层代理 |
| Router 禁止 import Repository | Router 只能 import Service 和 Schema |
| Service 抛 ValueError | 业务校验失败统一抛 ValueError，Router catch 后转 HTTPException |
| Repository 只做 CRUD | 不包含业务判断逻辑，返回 Entity |
| 依赖注入方向 | Router 依赖 Service，Service 依赖 Repository，通过 FastAPI Depends 注入 |

### 其他规范

- **异步优先**: 所有 I/O 操作使用 async/await
- **依赖注入**: 通过 FastAPI Depends 管理 Service/Repository 生命周期
- **标识符安全**: SQL 中表名/列名等标识符必须通过 `validate_identifier()` 校验后再拼接，禁止直接 f-string 拼接用户输入
- **密码加密**: 数据源密码必须 AES-256-GCM 加密后存储，通过 `app.core.crypto` 模块加解密

## 应用生命周期

```
启动:
  1. embedding_client_manager.init()
  2. qdrant_client_manager.init()
  3. es_client_manager.init()
  4. meta_mysql_client_manager.init()
  5. _init_meta_tables() → create_all + _sync_missing_columns (自动补列)

关闭:
  1. datasource_manager.close_all()
  2. qdrant_client_manager.close()
  3. es_client_manager.close()
  4. meta_mysql_client_manager.close()
```

## 已知待完善项

| 优先级 | 问题 | 位置 | 状态 |
|--------|------|------|------|
| 🔴 高 | SQL 注入风险 (f-string 拼接表名/列名) | db_executor/mysql_executor.py, postgresql_executor.py, meta_mysql_repository.py | ✅ 已修复 |
| 🔴 高 | 密码明文存储 (注释标注 AES 但未实现) | models/datasource.py, datasource_mapper.py | ✅ 已修复 |
| 🔴 高 | 删除数据源不级联清理 (Qdrant/ES/MySQL/DatasourceManager) | metadata_router.py delete_datasource | ✅ 已修复 |
| 🟡 中 | build_from_config_with_session 临时替换字段非线程安全 | meta_knowledge_service.py | ✅ 已修复 |
| 🟡 中 | 数据源注册分散，应用重启后需首次请求才注册 | 多处 register() 调用 | ✅ 已修复 |
| 🟡 中 | publish 与 build_knowledge 中 JSON→MetaConfig 解析重复 | metadata_router.py, build_knowledge.py | ✅ 已修复 |
| 🟢 低 | 缺少 CORS 中间件 | main.py | ✅ 已修复 |
| 🟢 低 | 缺少全局异常处理 | main.py | ✅ 已修复 |
| 🟢 低 | Qdrant 缺少 Payload 索引 | column_qdrant_repository.py, metric_qdrant_repository.py | ✅ 已修复 |
| 🟢 低 | 缺少健康检查接口 | - | ✅ 已修复 |
| 🟢 低 | 列表接口缺少分页 | metadata_router.py | ✅ 已修复 |
