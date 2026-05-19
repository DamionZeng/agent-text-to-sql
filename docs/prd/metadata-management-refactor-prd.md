# 元数据管理系统重构 PRD

## 1. 项目背景与目标

### 1.1 现状
当前项目的元数据管理采用**静态配置文件**（`conf/meta_conf.yaml`）+ **命令行脚本**（`app/scripts/build_meta_knowledge.py`）的模式：
- 用户手动编写 YAML 文件描述表结构、字段语义、指标定义
- 运行脚本一次性将配置写入 MySQL 元数据库、Qdrant 向量库、ES 全文索引
- 后续修改需直接编辑 YAML 文件并重新执行脚本

### 1.2 痛点
- **配置门槛高**：需要理解 YAML 结构和字段含义
- **无数据源管理**：数据仓库连接硬编码，无法支持多数据源
- **无交互界面**：所有操作通过命令行完成，无法预览和增量修改
- **AI 能力未利用**：字段描述、别名、角色判断、指标推断等依赖人工编写

### 1.3 目标
构建一套**可视化的元数据管理系统**，核心能力包括：
1. **数据源管理**：在界面上动态添加、测试、管理多类型数据源（MySQL、PostgreSQL 等）
2. **AI 驱动的元数据生成**：引入 LangGraph Agent，自动分析数据库 Schema 并生成高质量的元数据配置（描述、别名、角色、指标）
3. **可视化编辑**：用户在界面上预览和编辑 Agent 生成的元数据
4. **一键同步**：用户确认后，调用现有服务将元数据写入 MySQL + Qdrant + ES
5. **零侵入**：不修改现有 Agent 查询链路，通过新增模块实现

---

## 2. 整体架构

### 2.1 架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              前端 (Vue3 + Ant Design Vue)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  数据源管理   │  │  元数据编辑器 │  │  指标管理     │  │  同步任务     │ │
│  │   页面       │  │   页面       │  │   页面       │  │   页面       │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              后端 (FastAPI)                              │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                     新增模块: metadata_mgmt                          │ │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────────────┐ │ │
│  │  │ datasource │ │   schema   │ │  metadata  │ │      sync        │ │ │
│  │  │  router    │ │  router    │ │  router    │ │    router        │ │ │
│  │  │  service   │ │  service   │ │  service   │ │    service       │ │ │
│  │  │  repo      │ │  repo      │ │  repo      │ │                  │ │ │
│  │  └────────────┘ └────────────┘ └────────────┘ └──────────────────┘ │ │
│  │                                                                    │ │
│  │  ┌──────────────────────────────────────────────────────────────┐  │ │
│  │  │              MetaAgent (LangGraph Agent)                      │  │ │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │  │ │
│  │  │  │ analyze_ │ │ infer_   │ │ infer_   │ │ infer_   │        │  │ │
│  │  │  │ schema   │ │ tables   │ │ columns  │ │ metrics  │        │  │ │
│  │  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │  │ │
│  │  │  ┌──────────┐ ┌──────────┐                                  │  │ │
│  │  │  │ validate │ │ build_   │                                  │  │ │
│  │  │  │ _config  │ │ knowledge│                                  │  │ │
│  │  │  └──────────┘ └──────────┘                                  │  │ │
│  │  └──────────────────────────────────────────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                     现有模块: agent (保持不变)                        │ │
│  │         query_router → query_service → agent graph                  │ │
│  │              ↑ 使用 meta_mysql / qdrant / es (同一份数据)            │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              数据层                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  meta_mysql  │  │    qdrant    │  │      es      │  │   各数据源    │ │
│  │ (元数据DB)    │  │  (向量索引)   │  │  (全文索引)   │  │ (MySQL/...)  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 设计原则
- **隔离性**：新增 `metadata_mgmt` 模块与现有 `agent` 模块完全隔离
- **复用性**：同步阶段复用现有的 `MetaKnowledgeService` 和 `build_meta_knowledge.py` 逻辑
- **扩展性**：数据源类型通过策略模式扩展，Agent 节点通过 LangGraph 编排
- **可追溯**：Agent 执行的每一步状态都通过 stream 返回前端，用户可实时看到进度

---

## 3. MetaAgent 设计（LangGraph Agent）

### 3.1 Agent 构建模式

参考现有 `DataAgent` 的构建模式：
- `state.py`：定义 `MetaAgentState` TypedDict
- `context.py`：定义 `MetaAgentContext` TypedDict（注入 Repository 和 LLM）
- `nodes/`：每个步骤一个独立的 async 函数文件
- `graph.py`：使用 `StateGraph` 编排节点和边
- `llm.py`：复用现有的 `llm` 实例

### 3.2 State 设计

```python
class MetaAgentState(TypedDict):
    # === 输入 ===
    datasource_id: str              # 数据源ID
    raw_schema: list[RawTableSchema]  # 原始Schema

    # === 中间产物 ===
    table_classifications: dict[str, str]   # {"table_name": "dim"|"fact"|"unknown"}
    table_configs: list[TableConfig]        # 表配置列表
    column_configs: list[ColumnConfig]      # 字段配置列表
    metric_configs: list[MetricConfig]      # 指标配置列表

    # === 输出 ===
    meta_config: MetaConfig | None          # 最终生成的配置
    validation_result: dict | None          # 校验结果
    sync_result: dict | None                # 同步结果

    # === 状态 ===
    error: str | None
    retry_count: int
```

### 3.3 Context 设计

```python
class MetaAgentContext(TypedDict):
    llm: BaseChatModel                       # 复用现有 llm
    datasource_repository: DatasourceRepository   # 数据源Repository
    schema_repository: SchemaRepository      # SchemaRepository（动态连接数据源）
```

### 3.4 节点设计

| 节点 | 文件 | 职责 | 输入 State | 输出 State |
|------|------|------|-----------|-----------|
| `analyze_schema` | `nodes/analyze_schema.py` | 连接数据源，拉取原始 Schema（表名、字段名、字段类型、示例值） | `datasource_id` | `raw_schema` |
| `classify_tables` | `nodes/classify_tables.py` | 分析表结构，识别维度表/事实表 | `raw_schema` | `table_classifications` |
| `infer_tables` | `nodes/infer_tables.py` | 为每个表生成描述、确认角色 | `raw_schema`, `table_classifications` | `table_configs` |
| `infer_columns` | `nodes/infer_columns.py` | 为每个字段生成描述、别名、角色，判断是否需要同步取值 | `raw_schema`, `table_configs` | `column_configs` |
| `infer_metrics` | `nodes/infer_metrics.py` | 基于事实表和度量字段推断业务指标 | `table_configs`, `column_configs` | `metric_configs` |
| `assemble_config` | `nodes/assemble_config.py` | 组装成完整的 MetaConfig | `table_configs`, `column_configs`, `metric_configs` | `meta_config` |
| `validate_config` | `nodes/validate_config.py` | 校验配置完整性（必填字段、关联一致性） | `meta_config` | `validation_result` |
| `build_knowledge` | `nodes/build_knowledge.py` | 调用 MetaKnowledgeService 写入 DB + 向量库 + ES | `meta_config` | `sync_result` |

### 3.5 Graph 编排

```python
from langgraph.constants import START, END
from langgraph.graph import StateGraph

from app.metadata_agent.state import MetaAgentState
from app.metadata_agent.context import MetaAgentContext
from app.metadata_agent.nodes import (
    analyze_schema, classify_tables, infer_tables,
    infer_columns, infer_metrics, assemble_config,
    validate_config, build_knowledge
)

graph_builder = StateGraph(
    state_schema=MetaAgentState,
    context_schema=MetaAgentContext
)

# 添加节点
graph_builder.add_node("analyze_schema", analyze_schema)
graph_builder.add_node("classify_tables", classify_tables)
graph_builder.add_node("infer_tables", infer_tables)
graph_builder.add_node("infer_columns", infer_columns)
graph_builder.add_node("infer_metrics", infer_metrics)
graph_builder.add_node("assemble_config", assemble_config)
graph_builder.add_node("validate_config", validate_config)
graph_builder.add_node("build_knowledge", build_knowledge)

# 编排边
graph_builder.add_edge(START, "analyze_schema")
graph_builder.add_edge("analyze_schema", "classify_tables")
graph_builder.add_edge("classify_tables", "infer_tables")
graph_builder.add_edge("infer_tables", "infer_columns")
graph_builder.add_edge("infer_columns", "infer_metrics")
graph_builder.add_edge("infer_metrics", "assemble_config")
graph_builder.add_edge("assemble_config", "validate_config")

# 校验失败则重试推断
graph_builder.add_conditional_edges(
    "validate_config",
    path=lambda state: "build_knowledge" if state["validation_result"]["valid"] else "infer_tables",
    path_map={"build_knowledge": "build_knowledge", "infer_tables": "infer_tables"}
)

graph_builder.add_edge("build_knowledge", END)

meta_agent = graph_builder.compile()
```

### 3.6 节点详细设计

#### 3.6.1 analyze_schema

- **非 AI 节点**：直接查询数据源信息Schema
- **逻辑**：
  1. 从 `datasource_id` 获取数据源连接信息
  2. 动态创建数据库连接（根据数据源类型选择对应驱动）
  3. 执行 `SHOW TABLES` / `INFORMATION_SCHEMA.COLUMNS` 获取所有表和字段
  4. 对每个字段采样示例值（LIMIT 10）
  5. 组装 `raw_schema`

#### 3.6.2 classify_tables

- **AI 节点**：调用 LLM 分析表结构
- **Prompt 核心逻辑**：
  - 输入：所有表的字段列表
  - 任务：判断每个表是维度表（dim）、事实表（fact）还是未知（unknown）
  - 判断依据：是否包含度量字段（数值型）、是否包含外键、命名特征等
- **输出**：`{"table_name": "dim"|"fact"|"unknown"}`

#### 3.6.3 infer_tables

- **AI 节点**：为每个表生成描述和确认角色
- **Prompt 核心逻辑**：
  - 输入：表名 + 字段列表 + 分类结果
  - 任务：生成中文描述，确认/修正角色
- **输出**：`TableConfig` 列表

#### 3.6.4 infer_columns

- **AI 节点**：为每个字段生成描述、别名、角色
- **Prompt 核心逻辑**：
  - 输入：表名 + 字段名 + 字段类型 + 示例值 + 表角色
  - 任务：
    - 判断字段角色（primary_key / foreign_key / measure / dimension）
    - 生成中文描述
    - 生成中文别名列表（同义词）
    - 判断是否需要同步取值到 ES（`sync: true/false`）
- **输出**：`ColumnConfig` 列表

#### 3.6.5 infer_metrics

- **AI 节点**：基于事实表推断业务指标
- **Prompt 核心逻辑**：
  - 输入：所有表配置 + 字段配置
  - 任务：识别常见的业务指标（如 GMV、订单量、客单价等）
  - 每个指标包含：名称、描述、关联字段、别名
- **输出**：`MetricConfig` 列表

#### 3.6.6 validate_config

- **非 AI 节点**：程序校验
- **校验项**：
  - 所有表必须有描述和角色
  - 所有字段必须有描述和角色
  - 事实表必须至少有一个 measure 字段
  - 指标关联的字段必须存在
  - 外键字段的关联表必须存在

#### 3.6.7 build_knowledge

- **非 AI 节点**：复用现有逻辑
- **逻辑**：
  1. 将 `MetaConfig` 转换为与现有 `meta_conf.yaml` 相同的结构
  2. 调用 `MetaKnowledgeService.build_from_config(meta_config)`
  3. 依次执行：保存表/字段到 MySQL → 向量索引到 Qdrant → 全文索引到 ES → 保存指标到 MySQL → 指标向量索引

---

## 4. 后端模块设计

### 4.1 目录结构（新增）

```
app/
├── metadata_agent/              # MetaAgent（LangGraph Agent）
│   ├── __init__.py
│   ├── state.py                 # MetaAgentState
│   ├── context.py               # MetaAgentContext
│   ├── graph.py                 # Graph 编排
│   ├── llm.py                   # 复用或扩展 LLM 实例
│   └── nodes/
│       ├── __init__.py
│       ├── analyze_schema.py
│       ├── classify_tables.py
│       ├── infer_tables.py
│       ├── infer_columns.py
│       ├── infer_metrics.py
│       ├── assemble_config.py
│       ├── validate_config.py
│       └── build_knowledge.py
├── metadata_mgmt/               # 元数据管理业务模块
│   ├── __init__.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── datasource_router.py
│   │   ├── schema_router.py
│   │   ├── metadata_router.py
│   │   └── sync_router.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── datasource_schema.py
│   │   ├── schema_schema.py
│   │   ├── metadata_schema.py
│   │   └── sync_schema.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── datasource_service.py
│   │   ├── schema_service.py
│   │   ├── metadata_service.py
│   │   └── sync_service.py
│   └── repositories/
│       ├── __init__.py
│       ├── datasource_repository.py
│       ├── schema_repository.py
│       └── metadata_draft_repository.py
├── models/                      # SQLAlchemy Model（新增）
│   ├── datasource.py
│   └── meta_draft.py
└── entities/                    # Entity（新增）
    ├── datasource.py
    └── meta_draft.py
```

### 4.2 核心模块说明

#### 4.2.1 metadata_agent（Agent 层）
- 完全参考现有 `app/agent/` 的结构和模式
- `state.py` / `context.py` / `graph.py` / `nodes/` 一一对应
- 复用现有的 `llm.py` 中的 `llm` 实例
- 每个节点函数签名：`async def node_name(state: MetaAgentState, runtime: Runtime[MetaAgentContext]) -> dict:`
- 通过 `runtime.stream_writer` 向前端推送进度

#### 4.2.2 metadata_mgmt（业务层）
- **datasource**：数据源的 CRUD、连接测试
- **schema**：Schema 查询（从动态连接的数据源获取）
- **metadata**：元数据草稿的保存、查询、编辑
- **sync**：触发 Agent 执行、获取执行进度

### 4.3 数据库表设计（新增）

#### datasource 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | VARCHAR(64) | PK | 数据源ID（UUID） |
| name | VARCHAR(128) | NOT NULL | 数据源名称 |
| type | VARCHAR(32) | NOT NULL | 类型：mysql, postgresql, clickhouse, ... |
| host | VARCHAR(255) | NOT NULL | 主机地址 |
| port | INT | NOT NULL | 端口 |
| database | VARCHAR(128) | NOT NULL | 数据库名 |
| username | VARCHAR(128) | NOT NULL | 用户名 |
| password | VARCHAR(255) | NOT NULL | 密码（AES加密） |
| status | VARCHAR(32) | DEFAULT 'inactive' | 状态：active, inactive, error |
| created_at | DATETIME | DEFAULT NOW() | 创建时间 |
| updated_at | DATETIME | DEFAULT NOW() | 更新时间 |

#### meta_draft 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | VARCHAR(64) | PK | 草稿ID |
| datasource_id | VARCHAR(64) | FK | 关联数据源 |
| config_json | JSON | NOT NULL | 完整的 MetaConfig JSON |
| status | VARCHAR(32) | DEFAULT 'draft' | 状态：draft, published |
| created_at | DATETIME | DEFAULT NOW() | 创建时间 |
| updated_at | DATETIME | DEFAULT NOW() | 更新时间 |

### 4.4 API 接口设计

#### 数据源管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/metadata/datasources` | 创建数据源 |
| GET | `/api/metadata/datasources` | 数据源列表 |
| GET | `/api/metadata/datasources/{id}` | 数据源详情 |
| PUT | `/api/metadata/datasources/{id}` | 更新数据源 |
| DELETE | `/api/metadata/datasources/{id}` | 删除数据源 |
| POST | `/api/metadata/datasources/{id}/test` | 测试连接 |

#### Schema 查询

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/metadata/datasources/{id}/schema` | 获取原始 Schema |
| GET | `/api/metadata/datasources/{id}/schema/{table_name}` | 获取指定表 Schema |

#### 元数据草稿

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/metadata/datasources/{id}/draft` | 获取当前草稿 |
| PUT | `/api/metadata/datasources/{id}/draft` | 保存草稿 |
| DELETE | `/api/metadata/datasources/{id}/draft` | 删除草稿 |

#### 同步任务

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/metadata/datasources/{id}/sync` | 启动 Agent 同步（SSE 流式返回） |
| POST | `/api/metadata/datasources/{id}/publish` | 发布草稿到正式环境 |

### 4.5 同步任务流式返回格式

参考现有 `query_router.py` 的 `StreamingResponse`，同步接口同样使用 SSE：

```json
{"type": "progress", "step": "analyze_schema", "status": "running", "message": "正在连接数据源..."}
{"type": "progress", "step": "analyze_schema", "status": "success", "message": "获取到 5 张表"}
{"type": "progress", "step": "classify_tables", "status": "running", "message": "AI 正在分析表类型..."}
{"type": "progress", "step": "classify_tables", "status": "success", "message": "识别到 3 张维度表，2 张事实表"}
...
{"type": "result", "step": "build_knowledge", "status": "success", "data": {"tables": 5, "columns": 32, "metrics": 4}}
```

---

## 5. 前端设计

### 5.1 技术栈
- Vue 3 + Vite（复用现有）
- Ant Design Vue 4.x（新增）
- Vue Router（新增，单页应用路由）
- Pinia（新增，状态管理）

### 5.2 页面结构

```
/                          # 首页/仪表盘
├── /datasources           # 数据源列表页
│   └── /datasources/:id   # 数据源详情页（元数据编辑器）
├── /metrics               # 指标管理页
└── /sync-tasks            # 同步任务历史页
```

### 5.3 数据源详情页（核心页面）

```
┌─────────────────────────────────────────────────────────────────────┐
│  [返回] 数据源: MySQL-生产库                              [测试连接] │
├─────────────────────────────────────────────────────────────────────┤
│  基本信息                                                            │
│  名称: MySQL-生产库    类型: MySQL    主机: 192.168.1.100:3306      │
├─────────────────────────────────────────────────────────────────────┤
│  [Tab: 元数据编辑器]  [Tab: 指标管理]  [Tab: 同步历史]              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  操作栏: [AI 初始化/同步]  [保存草稿]  [发布同步]              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  表列表（左侧树形）              字段详情（右侧表格）           │ │
│  │  ▼ dim_region                   ┌────────┬────────┬──────┐    │ │
│  │  ▶ dim_customer                 │ 字段名  │ 类型    │ 角色  │    │ │
│  │  ▶ fact_order                   ├────────┼────────┼──────┤    │ │
│  │                                 │region_id│ int   │ PK   │    │ │
│  │                                 │province │ varchar│ dim │    │ │
│  │                                 │...     │ ...    │ ... │    │ │
│  │                                 └────────┴────────┴──────┘    │ │
│  │                                                                 │ │
│  │  选中字段编辑面板:                                               │ │
│  │  描述: [订单所属的省份名称              ]                       │ │
│  │  别名: [省份, 省, 所在省份            ]                         │ │
│  │  同步到ES: [√]                                                   │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  同步进度面板（点击同步后显示）                                   │ │
│  │  [✓] 分析 Schema        [✓] 识别表类型    [⟳] AI 推断字段...   │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.4 关键交互流程

1. **添加数据源**
   - 用户填写表单（名称、类型、连接信息）
   - 点击"测试连接"验证
   - 保存后进入详情页

2. **AI 初始化/同步**
   - 用户点击"AI 初始化"按钮
   - 前端建立 SSE 连接，实时显示 Agent 执行进度
   - Agent 完成后，前端展示生成的元数据
   - 用户可在界面上编辑描述、别名、角色等
   - 点击"保存草稿"暂存修改
   - 点击"发布同步"将最终配置写入 DB + 向量库 + ES

3. **增量修改**
   - 用户直接编辑已有元数据
   - 点击"保存草稿"
   - 确认无误后点击"发布同步"

---

## 6. Prompt 设计

### 6.1 设计原则

- **结构化输出**：所有 Prompt 要求 LLM 返回 JSON 格式，便于程序解析
- **上下文充分**：提供表名、字段名、字段类型、示例值等完整上下文
- **角色明确**：通过 System Prompt 明确 LLM 的角色为"数据仓库元数据专家"
- **可迭代**：Prompt 预留 few-shot 示例位置，便于后续优化

### 6.2 Prompt 文件清单

| Prompt 文件 | 用途 | 调用节点 | 输出格式 |
|------------|------|---------|---------|
| `classify_tables.prompt` | 识别维度表/事实表 | `classify_tables` | JSON dict |
| `infer_tables.prompt` | 生成表描述和角色 | `infer_tables` | JSON list |
| `infer_columns.prompt` | 生成字段描述、别名、角色 | `infer_columns` | JSON list |
| `infer_metrics.prompt` | 推断业务指标 | `infer_metrics` | JSON list |

Prompt 统一使用 `app/prompt/prompt_loader.py` 加载。

### 6.3 classify_tables.prompt

**目标**：根据表结构特征，将每个表分类为维度表（dim）、事实表（fact）或未知（unknown）。

**输入变量**：
- `tables`：表结构列表，每项包含表名和字段列表

**Prompt 模板**：

```
你是一位资深数据仓库架构师，擅长维度建模。请根据以下数据库表结构，判断每个表是维度表（dim）、事实表（fact）还是无法判断（unknown）。

判断标准：
- 维度表（dim）：描述业务实体，包含大量文本型属性字段，通常有唯一标识（主键），不含可累加的数值度量。例如：用户表、商品表、地区表。
- 事实表（fact）：记录业务过程，包含外键关联维度表，以及可累加的数值型度量字段（如金额、数量、次数）。例如：订单表、交易流水表。
- unknown：无法明确判断，或表结构过于简单（如只有id和name的映射表）。

请分析以下表结构：

{% for table in tables %}
表名：{{ table.name }}
字段：
{% for col in table.columns %}
  - {{ col.name }} ({{ col.type }}){% if col.is_primary %} [PK]{% endif %}{% if col.is_foreign %} [FK]{% endif %}
{% endfor %}

{% endfor %}

请返回 JSON 格式，不要包含任何其他说明文字：
{
  "table_name_1": "dim|fact|unknown",
  "table_name_2": "dim|fact|unknown",
  ...
}
```

**输出示例**：
```json
{
  "dim_region": "dim",
  "dim_product": "dim",
  "fact_order": "fact",
  "fact_transaction": "fact"
}
```

### 6.4 infer_tables.prompt

**目标**：为每个表生成中文描述，并确认/修正表角色。

**输入变量**：
- `tables`：表结构列表
- `classifications`：上一步的分类结果

**Prompt 模板**：

```
你是一位数据仓库元数据专家。请为以下数据库表生成准确的中文业务描述，并确认表的角色。

要求：
1. description：用一句话描述该表存储什么业务数据（20-100字）
2. role：确认表角色，可选值 dim（维度表）/ fact（事实表）
3. 如果分类明显错误，可以修正角色，但需要在备注中说明原因

表信息：

{% for table in tables %}
表名：{{ table.name }}
当前分类：{{ classifications[table.name] }}
字段列表：
{% for col in table.columns %}
  - {{ col.name }} ({{ col.type }})
{% endfor %}

{% endfor %}

请返回 JSON 数组格式，不要包含任何其他说明文字：
[
  {
    "name": "表名",
    "role": "dim|fact",
    "description": "中文描述"
  }
]
```

**输出示例**：
```json
[
  {
    "name": "dim_region",
    "role": "dim",
    "description": "地区维度表，存储省市区等地理层级信息"
  },
  {
    "name": "fact_order",
    "role": "fact",
    "description": "订单事实表，记录每笔订单的成交金额、数量、时间等度量数据"
  }
]
```

### 6.5 infer_columns.prompt

**目标**：为每个字段生成描述、别名、角色，并判断是否需要同步取值到 ES。

**输入变量**：
- `table`：当前表信息（表名、角色、描述）
- `columns`：字段列表（含名称、类型、示例值）

**Prompt 模板**：

```
你是一位数据仓库元数据专家。请为以下表的每个字段生成元数据信息。

表名：{{ table.name }}
表角色：{{ table.role }}
表描述：{{ table.description }}

字段信息：

{% for col in columns %}
字段名：{{ col.name }}
数据类型：{{ col.type }}
示例值：{{ col.sample_values | join(', ') }}

{% endfor %}

请为每个字段生成以下信息：
1. role：字段角色，可选值
   - primary_key：主键（唯一标识一条记录）
   - foreign_key：外键（关联其他表的主键）
   - measure：度量字段（可累加的数值，如金额、数量）
   - dimension：维度字段（用于分组筛选，如状态、类型、名称）
2. description：中文业务描述（10-50字）
3. alias：中文别名列表（2-5个同义词，用于自然语言匹配）
4. sync：是否同步该字段的取值到全文搜索引擎（true/false）
   - 建议同步：状态、类型、名称、标签等枚举值或文本值
   - 不建议同步：ID、金额、时间戳、数值度量

请返回 JSON 数组格式，不要包含任何其他说明文字：
[
  {
    "name": "字段名",
    "role": "primary_key|foreign_key|measure|dimension",
    "description": "中文描述",
    "alias": ["别名1", "别名2"],
    "sync": true|false
  }
]
```

**输出示例**：
```json
[
  {
    "name": "order_id",
    "role": "primary_key",
    "description": "订单唯一标识",
    "alias": ["订单号", "订单ID"],
    "sync": false
  },
  {
    "name": "order_amount",
    "role": "measure",
    "description": "订单成交金额",
    "alias": ["订单金额", "成交金额", "实付金额"],
    "sync": false
  },
  {
    "name": "order_status",
    "role": "dimension",
    "description": "订单当前状态",
    "alias": ["订单状态", "状态"],
    "sync": true
  }
]
```

### 6.6 infer_metrics.prompt

**目标**：基于事实表和度量字段，推断常见的业务指标。

**输入变量**：
- `tables`：所有表配置（含表角色、描述）
- `columns`：所有字段配置（含字段角色）

**Prompt 模板**：

```
你是一位数据分析师，擅长从数据仓库模型中识别业务指标。请根据以下表结构，推断常见的业务指标（KPI）。

要求：
1. 指标必须基于事实表（fact）的 measure 字段推导
2. 指标可以是：
   - 基础指标：直接使用单个 measure 字段（如订单金额 → 成交金额）
   - 复合指标：通过 measure 字段计算得到（如 成交金额 / 订单数 → 客单价）
3. 每个指标需要明确关联的字段（格式：表名.字段名）
4. 只推断常见、通用的业务指标，不要生造不常见的指标

表和字段信息：

{% for table in tables %}
{% if table.role == 'fact' %}
事实表：{{ table.name }} - {{ table.description }}
度量字段：
{% for col in columns %}
{% if col.table_name == table.name and col.role == 'measure' %}
  - {{ col.name }} ({{ col.type }}) - {{ col.description }}
{% endif %}
{% endfor %}
维度字段：
{% for col in columns %}
{% if col.table_name == table.name and col.role == 'dimension' %}
  - {{ col.name }} - {{ col.description }}
{% endif %}
{% endfor %}

{% endif %}
{% endfor %}

请返回 JSON 数组格式，不要包含任何其他说明文字：
[
  {
    "name": "指标名称（中文）",
    "description": "指标业务含义（20-80字）",
    "relevant_columns": ["表名.字段名"],
    "alias": ["别名1", "别名2"]
  }
]
```

**输出示例**：
```json
[
  {
    "name": "GMV",
    "description": "成交总额，统计时间范围内所有订单的成交金额总和",
    "relevant_columns": ["fact_order.order_amount"],
    "alias": ["成交总额", "订单总额", "交易额"]
  },
  {
    "name": "订单量",
    "description": "统计时间范围内的订单总笔数",
    "relevant_columns": ["fact_order.order_id"],
    "alias": ["订单数", "下单量", "笔数"]
  },
  {
    "name": "客单价",
    "description": "平均每笔订单的成交金额",
    "relevant_columns": ["fact_order.order_amount", "fact_order.order_id"],
    "alias": ["人均消费", "平均客单价"]
  }
]
```

### 6.7 Prompt 加载与调用方式

```python
from app.prompt.prompt_loader import PromptLoader

# 加载 prompt
prompt_loader = PromptLoader()
classify_prompt = prompt_loader.load("classify_tables.prompt")

# 渲染变量
rendered = classify_prompt.render(tables=raw_schema)

# 调用 LLM
response = await llm.ainvoke(rendered)
result = json.loads(response.content)
```

---

## 7. 与现有系统的集成点

### 7.1 复用的组件

| 组件 | 位置 | 复用方式 |
|------|------|---------|
| LLM 实例 | `app/agent/llm.py` | 直接 import |
| Prompt 加载器 | `app/prompt/prompt_loader.py` | 直接 import |
| MetaKnowledgeService | `app/services/meta_knowledge_service.py` | 直接 import |
| MySQL Model | `app/models/*.py` | 新增 Model 继承 Base |
| Mapper | `app/repositories/mysql/meta/mappers/*.py` | 参考现有模式新增 |

### 7.2 新增但不影响现有的组件

- `app/metadata_agent/`：全新的 Agent，与现有 `app/agent/` 并行
- `app/metadata_mgmt/`：全新的业务模块
- `app/models/datasource.py` / `app/models/meta_draft.py`：新增表
- `main.py`：新增 router include，不影响现有路由

### 7.3 数据流

```
MetaAgent 生成 MetaConfig
        │
        ▼
用户编辑确认
        │
        ▼
MetaKnowledgeService.build_from_config(meta_config)
        │
        ├──→ MySQL (table_info, column_info, metric_info)
        ├──→ Qdrant (column 向量索引, metric 向量索引)
        └──→ ES (value 全文索引)
        │
        ▼
现有 Agent 查询链路使用同一份数据（保持不变）
```

---

## 8. 安全与异常处理

### 8.1 数据源密码
- 使用 AES 加密存储于数据库
- 仅服务端解密，不返回给前端

### 8.2 数据库连接
- 动态连接使用连接池，操作完成后立即释放
- 避免长时间占用连接

### 8.3 Agent 异常
- 每个节点包裹 try-except，错误信息写入 `state["error"]`
- 前端通过 SSE 接收错误事件，展示友好提示
- 支持重试机制（`retry_count` 控制）

### 8.4 校验失败
- `validate_config` 节点发现配置不完整时，返回 `infer_tables` 重试
- 最多重试 3 次，超过则返回错误

---

## 9. 实施计划

### Phase 1：基础设施（第 1 周）
- [ ] 新增数据库表：`datasource`、`meta_draft`
- [ ] 新增 SQLAlchemy Model 和 Entity
- [ ] 新增 Repository 层
- [ ] 配置 Ant Design Vue 前端框架

### Phase 2：数据源管理（第 1-2 周）
- [ ] 数据源 CRUD API
- [ ] 连接测试功能
- [ ] 前端数据源列表和表单页面

### Phase 3：MetaAgent 开发（第 2-3 周）

#### Phase 3.1 框架搭建（第 2 周第 1-2 天）

**任务清单**：
- [ ] 创建 `app/metadata_agent/` 目录结构
- [ ] 实现 `state.py`：定义 `MetaAgentState` TypedDict
- [ ] 实现 `context.py`：定义 `MetaAgentContext` TypedDict
- [ ] 实现 `graph.py`：StateGraph 编排框架（先空节点占位）
- [ ] 实现 `llm.py`：复用现有 LLM 实例的适配器
- [ ] 创建 `nodes/__init__.py` 导出所有节点

**技术要点**：
- 参考 `app/agent/` 的目录结构和编码风格
- `state.py` 中所有字段使用 `Annotated` + `Reducer` 处理列表追加逻辑
- `context.py` 中注入的 Repository 需要通过依赖注入提供，避免循环导入

**验收标准**：
- 框架代码能通过 `python -c "from app.metadata_agent.graph import meta_agent"` 导入不报错
- 空节点 graph 能正常编译

#### Phase 3.2 非 AI 节点实现（第 2 周第 2-3 天）

**任务清单**：
- [ ] 实现 `analyze_schema` 节点
  - 支持 MySQL / PostgreSQL / ClickHouse 的动态连接
  - 查询 `INFORMATION_SCHEMA.COLUMNS` 获取字段信息
  - 对每个字段采样示例值（`SELECT DISTINCT col FROM table LIMIT 10`）
  - 输出 `RawTableSchema` 列表
- [ ] 实现 `assemble_config` 节点
  - 将 `table_configs` + `column_configs` + `metric_configs` 组装为 `MetaConfig`
  - 处理字段归属关系（将 column 按 table_name 分组）
- [ ] 实现 `validate_config` 节点
  - 校验所有表有描述和角色
  - 校验所有字段有描述和角色
  - 校验事实表至少有一个 measure 字段
  - 校验指标关联的字段存在
  - 输出 `{"valid": bool, "errors": list[str]}`
- [ ] 实现 `build_knowledge` 节点
  - 调用 `MetaKnowledgeService.build_from_config()`
  - 捕获异常并转换为 `sync_result`

**技术要点**：
- `analyze_schema` 使用 SQLAlchemy 创建动态引擎：`create_engine(connection_string)`
- 连接字符串中的密码需要解密
- 采样示例值时设置查询超时（5秒），避免大表全表扫描
- `validate_config` 的错误信息需要中文友好，用于前端展示

**验收标准**：
- `analyze_schema` 能正确连接测试数据库并返回 Schema 结构
- `validate_config` 能识别缺失描述的表/字段
- `build_knowledge` 能复用现有服务完成同步

#### Phase 3.3 AI 节点实现（第 2 周第 3-5 天）

**任务清单**：
- [ ] 实现 `classify_tables` 节点
  - 调用 LLM，输入所有表的字段结构
  - 解析 JSON 输出，写入 `table_classifications`
  - 处理 LLM 返回格式异常（fallback 为 unknown）
- [ ] 实现 `infer_tables` 节点
  - 调用 LLM，输入表结构 + 分类结果
  - 解析并输出 `TableConfig` 列表（不含 columns）
- [ ] 实现 `infer_columns` 节点
  - 按表分批调用 LLM（避免 prompt 过长）
  - 输入：表信息 + 该表所有字段（含示例值）
  - 输出：`ColumnConfig` 列表
- [ ] 实现 `infer_metrics` 节点
  - 调用 LLM，输入所有事实表 + measure 字段
  - 输出：`MetricConfig` 列表

**技术要点**：
- 每个 AI 节点需要包裹 try-except，LLM 调用失败时写入 `state["error"]`
- 使用 `runtime.stream_writer` 推送进度事件
- LLM 输出使用 `json.loads()` 解析，失败时尝试正则提取 JSON
- 考虑并发优化：`infer_columns` 可以按表并行调用 LLM（使用 `asyncio.gather`）
- 设置 LLM 调用超时（30秒）

**验收标准**：
- 每个 AI 节点能独立运行并返回正确格式的数据
- LLM 返回异常时有友好的错误处理，不导致 Agent 崩溃
- 流式输出能实时展示每个节点的执行状态

#### Phase 3.4 Prompt 文件编写（第 2 周第 5 天 - 第 3 周第 1 天）

**任务清单**：
- [ ] 编写 `classify_tables.prompt`
- [ ] 编写 `infer_tables.prompt`
- [ ] 编写 `infer_columns.prompt`
- [ ] 编写 `infer_metrics.prompt`
- [ ] 将 Prompt 文件放入 `prompts/` 目录
- [ ] 验证 Prompt 加载和渲染正常

**技术要点**：
- Prompt 使用 Jinja2 模板语法
- 预留 few-shot 示例位置（注释标记），便于后续优化
- 每个 Prompt 包含明确的输出格式要求和示例

**验收标准**：
- Prompt 文件能被 `PromptLoader` 正确加载
- 渲染后的 Prompt 包含完整的上下文信息
- LLM 能按照要求的 JSON 格式返回结果（测试准确率 > 80%）

#### Phase 3.5 Graph 编排与流式输出（第 3 周第 1-2 天）

**任务清单**：
- [ ] 完善 `graph.py`，连接所有节点和边
- [ ] 实现条件边：`validate_config` → `build_knowledge`（成功）/ `infer_tables`（失败重试）
- [ ] 实现重试机制：`retry_count` 超过 3 次则走向 END 并返回错误
- [ ] 实现 `sync_router.py` 的 SSE 流式接口
- [ ] 对接前端 SSE 连接

**技术要点**：
- 重试逻辑：校验失败时回到 `infer_tables`，保留已生成的部分数据
- SSE 接口使用 `StreamingResponse`，`media_type="text/event-stream"`
- 每个节点开始时推送 `{"type": "progress", "status": "running"}`
- 节点完成推送 `{"type": "progress", "status": "success"}`
- 最终结果推送 `{"type": "result", "data": {...}}`

**验收标准**：
- 完整 Graph 能从 START 运行到 END
- 校验失败时能正确重试，最多 3 次
- SSE 接口能在浏览器中接收完整的事件流
- 前端能正确展示进度和最终结果

#### Phase 3.6 单元测试（第 3 周第 2-3 天）

**任务清单**：
- [ ] 编写 `analyze_schema` 节点的单元测试（使用内存 SQLite 模拟数据源）
- [ ] 编写 `validate_config` 节点的单元测试
- [ ] 编写 `assemble_config` 节点的单元测试
- [ ] 编写 Graph 整体流程的集成测试（Mock LLM 响应）
- [ ] 测试重试逻辑和异常处理

**验收标准**：
- 非 AI 节点单元测试覆盖率 > 80%
- Mock LLM 的集成测试能验证完整流程
- 所有测试通过

### Phase 4：元数据编辑器（第 3-4 周）
- [ ] 元数据草稿 API
- [ ] 前端元数据编辑器页面（表/字段/指标编辑）
- [ ] 同步任务页面和 SSE 进度展示

### Phase 5：集成测试（第 4 周）
- [ ] 端到端测试：添加数据源 → AI 同步 → 编辑 → 发布 → 查询验证
- [ ] 确保现有 Agent 查询链路不受影响

---

## 11. 附录

### 11.1 现有 meta_conf.yaml 格式参考

```yaml
tables:
  - name: dim_region
    role: dim
    description: 地区维度表
    columns:
      - name: region_id
        role: primary_key
        description: 地区唯一标识
        alias: [地区ID, 区域ID]
        sync: false
      - name: province
        role: dimension
        description: 订单所属的省份名称
        alias: [省份, 省]
        sync: true

metrics:
  - name: GMV
    description: 成交总额
    relevant_columns:
      - fact_order.order_amount
    alias: [成交总额, 订单总额]
```

### 11.2 MetaConfig 数据结构（现有）

```python
@dataclass
class ColumnConfig:
    name: str
    role: str          # primary_key | foreign_key | measure | dimension
    description: str
    alias: list[str]
    sync: bool         # 是否同步取值到 ES

@dataclass
class TableConfig:
    name: str
    role: str          # dim | fact
    description: str
    columns: list[ColumnConfig]

@dataclass
class MetricConfig:
    name: str
    description: str
    relevant_columns: list[str]
    alias: list[str]

@dataclass
class MetaConfig:
    tables: list[TableConfig]
    metrics: list[MetricConfig]
```

### 11.3 现有 Agent 节点参考

现有 `DataAgent` 节点模式：
```python
async def node_name(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "节点名", "status": "running"})
    try:
        # 业务逻辑
        writer({"type": "progress", "step": "节点名", "status": "success"})
        return {"key": "value"}  # 返回 state 更新
    except Exception as e:
        writer({"type": "progress", "step": "节点名", "status": "error"})
        raise e
```

MetaAgent 节点遵循完全相同的模式。

---

## 10. 风险与对策

### 10.1 技术风险

| 风险 | 影响 | 可能性 | 对策 |
|------|------|--------|------|
| **LLM 输出格式不稳定** | AI 节点解析 JSON 失败，Agent 流程中断 | 中 | 1. Prompt 中明确要求 JSON 格式<br>2. 实现 JSON 修复逻辑（正则提取、去除 markdown 代码块）<br>3. 解析失败时 fallback 到默认值（如 unknown）<br>4. 记录原始输出便于人工排查 |
| **LLM 调用超时或失败** | 同步任务卡住或失败 | 中 | 1. 设置 LLM 调用超时（30秒）<br>2. 实现重试机制（最多 3 次）<br>3. 超时后返回错误，前端展示友好提示<br>4. 支持用户手动重试 |
| **数据库连接泄漏** | 服务端连接数耗尽，影响现有查询链路 | 低 | 1. 使用连接池，设置 max_overflow 和 pool_timeout<br>2. 确保每个连接在使用后显式 close<br>3. 使用 context manager 管理连接生命周期<br>4. 监控连接池使用率 |
| **Prompt 注入攻击** | 恶意表名/字段名通过 Prompt 影响 LLM 输出 | 低 | 1. 对用户输入的表名、字段名进行校验（只允许字母数字下划线）<br>2. Prompt 模板中使用 Jinja2 的 autoescape<br>3. 不将用户自定义描述直接传入 LLM（经过人工确认后才进入 Agent 流程） |
| **数据源密码泄露** | 数据库凭证被窃取 | 低 | 1. 使用 AES-256 加密存储密码<br>2. 密钥通过环境变量注入，不提交到代码仓库<br>3. API 不返回密码字段<br>4. 连接字符串中的密码在日志中脱敏 |

### 10.2 业务风险

| 风险 | 影响 | 可能性 | 对策 |
|------|------|--------|------|
| **AI 生成的元数据不准确** | 用户查询时语义匹配错误，影响查询准确率 | 高 | 1. AI 生成后必须人工确认才能发布<br>2. 提供可视化编辑器，方便用户修改<br>3. 保存草稿机制，支持多次迭代<br>4. 发布后保留历史版本，支持回滚 |
| **同步过程破坏现有索引** | 发布新配置后，现有查询链路异常 | 中 | 1. 发布前进行配置校验<br>2. 支持灰度发布（先同步到测试环境验证）<br>3. 保留上一版本的配置快照<br>4. 提供一键回滚功能 |
| **大表 Schema 分析性能差** | 表数量过多或字段过多时，Agent 执行缓慢 | 中 | 1. `analyze_schema` 限制最大分析表数（如 50 张）<br>2. 示例值采样使用 `LIMIT 10`，避免全表扫描<br>3. `infer_columns` 按表并行调用 LLM<br>4. 提供"选择需要分析的表"功能，减少不必要的分析 |
| **多数据源类型兼容性** | 新数据源类型（如 Oracle、SQLServer）无法连接 | 低 | 1. 数据源连接使用 SQLAlchemy + 方言驱动，保证通用性<br>2. Schema 查询使用 ANSI SQL 标准的 `INFORMATION_SCHEMA`<br>3. 新增数据源类型只需添加驱动依赖和连接字符串模板<br>4. 提供数据源类型扩展接口 |

### 10.3 项目风险

| 风险 | 影响 | 可能性 | 对策 |
|------|------|--------|------|
| **Phase 3 延期影响整体进度** | Phase 4/5 被迫压缩，质量下降 | 中 | 1. Phase 3 的 AI 节点和非 AI 节点可以并行开发<br>2. Prompt 调优可以独立进行，不阻塞工程开发<br>3. 预留 2 天缓冲时间<br>4. 如时间不足，优先保证非 AI 节点和基础流程，AI 节点可后续迭代优化 |
| **与现有系统耦合意外增加** | 修改影响现有 Agent 查询链路 | 低 | 1. 严格遵守隔离原则，新增模块不修改现有代码<br>2. 代码评审时重点检查是否修改了 `app/agent/` 目录<br>3. Phase 5 的集成测试必须包含现有链路回归测试<br>4. 使用 feature flag 控制新功能上线，便于快速回退 |

### 10.4 风险监控清单

- [ ] LLM 调用成功率监控（目标 > 95%）
- [ ] LLM 平均响应时间监控（目标 < 10s）
- [ ] JSON 解析失败率监控（目标 < 5%）
- [ ] 数据库连接池使用率监控（目标 < 80%）
- [ ] 同步任务成功率监控（目标 > 98%）
- [ ] 现有 Agent 查询成功率监控（目标不下降）
