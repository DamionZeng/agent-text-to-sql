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

新增以下 Prompt 文件（放置于 `prompts/` 目录）：

| Prompt 文件 | 用途 | 调用节点 |
|------------|------|---------|
| `classify_tables.prompt` | 识别维度表/事实表 | `classify_tables` |
| `infer_tables.prompt` | 生成表描述和角色 | `infer_tables` |
| `infer_columns.prompt` | 生成字段描述、别名、角色 | `infer_columns` |
| `infer_metrics.prompt` | 推断业务指标 | `infer_metrics` |

Prompt 统一使用 `app/prompt/prompt_loader.py` 加载。

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
- [ ] 搭建 `app/metadata_agent/` 框架（state, context, graph）
- [ ] 实现 `analyze_schema` 节点（非 AI）
- [ ] 实现 `classify_tables`、`infer_tables`、`infer_columns`、`infer_metrics` 节点（AI）
- [ ] 实现 `validate_config`、`assemble_config`、`build_knowledge` 节点
- [ ] 编写 Prompt 文件
- [ ] Graph 编排和流式输出

### Phase 4：元数据编辑器（第 3-4 周）
- [ ] 元数据草稿 API
- [ ] 前端元数据编辑器页面（表/字段/指标编辑）
- [ ] 同步任务页面和 SSE 进度展示

### Phase 5：集成测试（第 4 周）
- [ ] 端到端测试：添加数据源 → AI 同步 → 编辑 → 发布 → 查询验证
- [ ] 确保现有 Agent 查询链路不受影响

---

## 10. 附录

### 10.1 现有 meta_conf.yaml 格式参考

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

### 10.2 MetaConfig 数据结构（现有）

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

### 10.3 现有 Agent 节点参考

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
