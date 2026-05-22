# 可视化模块 PRD

## 1. 项目背景与目标

### 1.1 现状

当前 agent-text2sql 系统包含两大核心模块：

- **Chat 模块（查询对话）**：用户通过自然语言提问，Data Agent 自动检索元数据知识库、生成 SQL、校验并执行，最终以 SSE 流式返回查询结果表格。
- **Metadata 模块（元数据管理）**：数据源注册、AI 自动分析 Schema、配置校验、草稿版本管理、知识库发布同步。

系统在 `run_sql` 节点执行完毕后直接将原始表格数据返回前端渲染为 `a-table`，缺乏数据可视化能力。用户面对冰冷的数字表格，难以快速洞察趋势、占比、异常等数据模式。

### 1.2 痛点

- **只有表格没有图**：查询结果无法自动生成图表，决策效率低
- **无大屏展示能力**：无法将多个关键指标组合成运营监控大屏
- **无图表复用机制**：每次可视化都需从零开始，无法沉淀为模板
- **AI 能力未延伸到可视化层**：已具备 SQL 生成能力，但未利用 AI 自动选择合适的图表类型、生成图表配置

### 1.3 目标

构建系统第三个核心模块——**可视化模块（Visualization）**，与 Chat、Metadata 两大模块平级，核心能力包括：

1. **A - SQL 结果一键成图**：查询完成后，AI 自动推荐图表类型并生成 ECharts 配置，Chat 内嵌渲染
2. **B - 一句话生成图表**：用户通过 `/chart` 命令或编辑器内 AI 按钮，端到端从意图到图表
3. **C - 自定义数据大屏**：拖拽式栅格布局编辑器，支持多图表自由组合、全局筛选器联动、定时刷新
4. **D - AI 一句话生成大屏**：用户描述大屏需求，AI 自动规划布局、生成 SQL、生成图表、组装大屏
5. **F - 图表模板市场**：行业化预设模板 + 用户自定义模板的发布与复用，应用时 AI 自动映射 Schema

### 1.4 参考标杆

| 产品 | 学习要点 |
|------|---------|
| 阿里 DataV | 大屏视觉设计语言：深色主题、科技感边框、数据动效、行业模板体系 |
| Grafana | 面板编排体验：自由拖拽、栅格吸附、全局变量联动、面板热切换 |
| Tableau | 图表自定义深度：双轴/多轴、颜色映射、参考线/趋势线、标注系统 |
| Superset | 数据探索流：字段拖拽到维度/度量区、Filter Box、SQL Lab → Chart 流转 |

---

## 2. 整体架构

### 2.1 模块定位

可视化模块作为与 Chat、Metadata 平级的独立模块，三者共享底层基础设施（MySQL 元数据库、Qdrant 向量库、ES 全文检索、动态数据源管理）。

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Chat 模块   │  │  Viz 模块    │  │ Metadata 模块│
│  (已有)      │  │  (新增)      │  │  (已有)      │
│              │  │              │  │              │
│ POST /api/   │  │ /api/viz/*   │  │ /api/metadata│
│ query        │  │              │  │ /*           │
│ Data Agent   │  │ VizAgent     │  │ Meta Agent   │
│ 链路         │  │ 链路         │  │ 链路         │
└──────────────┘  └──────────────┘  └──────────────┘
       │                │                 │
       └────────────────┼─────────────────┘
                        ▼
┌─────────────────────────────────────────────────┐
│  共享基础设施                                     │
│  MySQL (元数据) | Qdrant (向量) | ES (全文)       │
│  DatasourceManager (动态数据源引擎缓存)            │
└─────────────────────────────────────────────────┘
```

### 2.2 Chat → Viz 桥接机制

Chat 与 Viz 模块通过以下方式桥接：
- Chat 查询结果每条消息下方增加 **"一键成图"**、**"加入大屏"**、**"保存为模板"** 三个操作按钮
- "一键成图"：将当前 SQL + 结果传递给 Chart API，在 Chat 内嵌渲染图表
- "加入大屏"：弹出大屏选择器（已有大屏列表 + 新建大屏），将当前图表配置注入到目标大屏
- "保存为模板"：将图表配置 + 数据源信息保存为可复用模板

### 2.3 设计原则

- **模块独立性**：Viz 模块拥有独立的路由、Service、Repository、Agent，不耦合 Chat/Metadata 内部逻辑
- **复用共享基础设施**：复用 embedding_client、Qdrant/ES/MySQL 客户端、数据源管理器，不重复创建连接
- **零侵入**：不改动现有 Data Agent 链路，Viz Agent 作为独立 Agent，在需要时通过 API 调用 Data Agent 或复用其节点
- **AI 优先**：图表配置生成、大屏布局规划、Schema 映射等关键环节均由 AI 驱动

---

## 3. 数据模型

所有新增表建在现有元数据库（MySQL）中。

### 3.1 chart_config — 图表配置表

存储单个图表的完整配置（SQL + ECharts option），独立于大屏面板存在，可被多个大屏复用。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(36) PK | UUID |
| datasource_id | VARCHAR(36) FK | 数据源ID，关联 datasource 表 |
| name | VARCHAR(255) NOT NULL | 图表名称 |
| chart_type | VARCHAR(64) NOT NULL | line / bar / pie / scatter / heatmap / radar / gauge / funnel / map / table / number_card / text |
| sql_text | TEXT NOT NULL | 数据查询 SQL，支持 `{{变量}}` 模板语法 |
| echarts_option | JSON NOT NULL | ECharts 完整 option 配置对象 |
| auto_generated | TINYINT DEFAULT 0 | 是否 AI 自动生成 |
| query_params | JSON | SQL 模板参数定义，如 `{"date_range": {"type": "date_range", "default": "last_30_days"}}` |
| width | INT DEFAULT 6 | 默认栅格宽度 (1-12) |
| height | INT DEFAULT 400 | 默认像素高度 |
| refresh_interval | INT DEFAULT 0 | 自动刷新间隔（秒），0 表示不刷新 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 3.2 dashboard — 大屏表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(36) PK | UUID |
| name | VARCHAR(255) NOT NULL | 大屏名称 |
| description | TEXT | 描述 |
| datasource_id | VARCHAR(36) FK | 默认数据源ID |
| theme | VARCHAR(64) DEFAULT 'dark' | dark / light / custom |
| theme_config | JSON | 自定义主题配置（背景色、边框色、字体等） |
| layout_config | JSON | 栅格设置：`{"cols": 12, "row_height": 100, "gap": 12}` |
| global_filters | JSON | 全局筛选器定义数组 |
| refresh_enabled | TINYINT DEFAULT 0 | 启用自动刷新 |
| refresh_interval | INT DEFAULT 60 | 全局刷新间隔（秒） |
| thumbnail | TEXT | 缩略图 base64 |
| auto_generated | TINYINT DEFAULT 0 | 是否 AI 生成 |
| status | VARCHAR(32) DEFAULT 'draft' | draft / published / archived |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 3.3 panel — 大屏面板表

每个面板对应大屏上的一个图表容器，通过栅格坐标定位。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(36) PK | UUID |
| dashboard_id | VARCHAR(36) FK | 所属大屏ID |
| chart_config_id | VARCHAR(36) FK | 关联图表配置ID |
| title | VARCHAR(255) | 面板标题（覆盖 chart_config.name 的大屏展示名） |
| layout_x | INT NOT NULL | 栅格 x 坐标 (0-based) |
| layout_y | INT NOT NULL | 栅格 y 坐标 (0-based) |
| layout_w | INT DEFAULT 6 | 栅格宽度 |
| layout_h | INT DEFAULT 4 | 栅格高度 |
| sort_order | INT DEFAULT 0 | 排序 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 3.4 dashboard_filter — 大屏全局筛选器表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(36) PK | UUID |
| dashboard_id | VARCHAR(36) FK | 所属大屏ID |
| name | VARCHAR(128) NOT NULL | 筛选器名称（对应 SQL 模板变量名） |
| label | VARCHAR(255) NOT NULL | 显示标签 |
| filter_type | VARCHAR(32) NOT NULL | date_range / select / multi_select / input / cascader |
| config | JSON NOT NULL | 筛选器配置（选项来源 SQL、默认值、样式等） |
| target_panels | JSON | 联动目标面板ID列表，空表示全局 |
| sort_order | INT DEFAULT 0 | 排序 |
| created_at | DATETIME | 创建时间 |

### 3.5 template — 模板市场表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(36) PK | UUID |
| name | VARCHAR(255) NOT NULL | 模板名称 |
| description | TEXT | 描述 |
| category | VARCHAR(64) | 分类：电商 / 金融 / 物流 / 医疗 / 教育 / SaaS / 通用 |
| industry | VARCHAR(64) | 行业标签 |
| theme | VARCHAR(64) DEFAULT 'dark' | 主题 |
| thumbnail | TEXT | 缩略图 base64 |
| dashboard_json | JSON NOT NULL | 大屏完整配置快照（含所有 panel + chart_config） |
| source_datasource_id | VARCHAR(36) | 模板来源数据源ID（用于 Schema 映射参考） |
| use_count | INT DEFAULT 0 | 使用次数 |
| is_system | TINYINT DEFAULT 0 | 是否系统预置 |
| is_premium | TINYINT DEFAULT 0 | 是否精选 |
| created_by | VARCHAR(36) | 创建者（预留用户系统） |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

---

## 4. API 设计

### 4.1 图表 API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/viz/charts/recommend` | 给定 SQL + 查询结果，AI 推荐图表类型并生成 ECharts 配置 |
| POST | `/api/viz/charts/generate` | 一句话生成完整图表（意图解析 → SQL → 执行 → 图表配置） |
| GET | `/api/viz/charts/{id}` | 获取图表详情 |
| PUT | `/api/viz/charts/{id}` | 更新图表配置 |
| DELETE | `/api/viz/charts/{id}` | 删除图表配置 |
| POST | `/api/viz/charts/{id}/execute` | 执行图表 SQL 并返回数据 |

#### POST /api/viz/charts/recommend

```json
// Request
{
  "datasource_id": "uuid",
  "query": "最近30天各品类销售额",  // 原始用户问题（可选，用于语义理解）
  "sql": "SELECT category, SUM(amount) ...",
  "result_data": {
    "columns": ["category", "total_sales"],
    "rows": [["手机", 1250000], ["电脑", 980000], ...]
  }
}

// Response
{
  "chart_type": "bar",
  "echarts_option": { ... },
  "reason": "柱状图适合对比不同品类的销售额..."
}
```

#### POST /api/viz/charts/generate

```json
// Request
{
  "datasource_id": "uuid",
  "prompt": "最近30天各品类销售额对比柱状图"
}

// Response (SSE 流式)
// {"type": "progress", "step": "生成SQL", "status": "running"}
// {"type": "progress", "step": "生成SQL", "status": "success"}
// {"type": "progress", "step": "执行SQL", "status": "running"}
// {"type": "progress", "step": "执行SQL", "status": "success"}
// {"type": "progress", "step": "生成图表", "status": "running"}
// {"type": "progress", "step": "生成图表", "status": "success"}
// {"type": "result", "chart_config": {...}}
```

### 4.2 大屏 API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/viz/dashboards` | 创建大屏 |
| GET | `/api/viz/dashboards` | 大屏列表（支持分页、筛选） |
| GET | `/api/viz/dashboards/{id}` | 获取大屏完整配置（含所有 panel + chart_config） |
| PUT | `/api/viz/dashboards/{id}` | 更新大屏基本信息 |
| DELETE | `/api/viz/dashboards/{id}` | 删除大屏（级联删除 panel、dashboard_filter） |
| POST | `/api/viz/dashboards/generate` | AI 一句话生成大屏（SSE 流式） |
| POST | `/api/viz/dashboards/{id}/panels` | 向大屏添加面板 |
| PUT | `/api/viz/dashboards/{id}/panels/{panel_id}` | 更新面板（布局/配置） |
| DELETE | `/api/viz/dashboards/{id}/panels/{panel_id}` | 删除面板 |
| PUT | `/api/viz/dashboards/{id}/panels/reorder` | 批量更新面板排序和布局 |
| GET | `/api/viz/dashboards/{id}/filters` | 获取大屏全局筛选器列表 |
| POST | `/api/viz/dashboards/{id}/filters` | 添加全局筛选器 |
| PUT | `/api/viz/dashboards/{id}/filters/{filter_id}` | 更新筛选器 |
| DELETE | `/api/viz/dashboards/{id}/filters/{filter_id}` | 删除筛选器 |
| GET | `/api/viz/dashboards/{id}/view` | 获取大屏完整渲染数据（执行所有 SQL 返回数据） |

#### POST /api/viz/dashboards/generate

```json
// Request
{
  "datasource_id": "uuid",
  "prompt": "做一个电商运营看板，包含：总销售额、月趋势图、品类占比、Top10品类、地区分布地图"
}

// Response (SSE 流式)
// {"type": "progress", "step": "解析意图", "status": "running"}
// {"type": "progress", "step": "解析意图", "status": "success", "result": {"panels": 5}}
// {"type": "progress", "step": "规划布局", "status": "running"}
// {"type": "progress", "step": "规划布局", "status": "success"}
// {"type": "progress", "step": "生成SQL (1/5)", "status": "running"}
// ...
// {"type": "progress", "step": "生成图表配置 (1/5)", "status": "running"}
// ...
// {"type": "progress", "step": "组装大屏", "status": "success"}
// {"type": "result", "dashboard": {...}}
```

### 4.3 模板 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/viz/templates` | 模板列表（按分类/行业筛选，分页） |
| GET | `/api/viz/templates/{id}` | 模板详情 |
| POST | `/api/viz/templates` | 发布为大屏模板（从已有大屏创建） |
| DELETE | `/api/viz/templates/{id}` | 删除模板（仅创建者可删） |
| POST | `/api/viz/templates/{id}/apply` | 应用模板创建新大屏（含 AI Schema 映射） |

#### POST /api/viz/templates/{id}/apply

```json
// Request
{
  "datasource_id": "uuid",  // 目标数据源
  "name": "我的电商看板"
}

// Response (SSE 流式)
// {"type": "progress", "step": "分析模板Schema", "status": "success"}
// {"type": "progress", "step": "映射表名 (3/5)", "status": "running"}
// {"type": "progress", "step": "映射字段 (12/18)", "status": "running"}
// {"type": "progress", "step": "生成适配SQL", "status": "success"}
// {"type": "progress", "step": "创建大屏", "status": "success"}
// {"type": "result", "dashboard_id": "uuid", "unmapped_fields": ["orders.status", ...]}
```

---

## 5. VizAgent 设计

### 5.1 概述

VizAgent 是新增的 LangGraph Agent，专门负责 AI 驱动的图表和大屏生成。复用现有 Data Agent 的 SQL 生成能力，通过 API 调用而非代码耦合。

### 5.2 State 设计

```python
class VizAgentState(TypedDict):
    # 输入
    datasource_id: str
    prompt: str                      # 用户意图（生成图表/大屏的描述）
    query_result: dict | None        # 已有查询结果（一键成图场景）

    # 中间产物
    parsed_intent: dict | None       # 解析后的意图：面板列表
    layout_plan: list | None         # 栅格布局规划
    chart_configs: list[dict]        # 图表配置列表 [{sql, echarts_option, ...}]

    # 输出
    dashboard: dict | None           # 最终大屏配置
    chart_config: dict | None        # 单图表配置（非大屏场景）

    # 状态
    error: str | None
    retry_count: int
```

### 5.3 节点设计

| 节点 | 职责 | 对应能力 |
|------|------|---------|
| `parse_intent` | LLM 解析用户意图，拆解为大屏面板需求列表或单个图表需求 | B, D |
| `plan_layout` | LLM 规划每个面板的栅格位置和尺寸 | D |
| `generate_sqls` | 调用 Data Agent 或直接 LLM 为每个面板生成 SQL | B, D |
| `run_sqls` | 并行执行所有面板的 SQL | B, D |
| `generate_charts` | LLM 为每组数据生成 ECharts option 配置 | B, D |
| `recommend_chart` | 给定数据，LLM 推荐最佳图表类型和配置 | A |
| `assemble_dashboard` | 组装 Dashboard + Panel + ChartConfig 数据 | D |

### 5.4 一键成图链路（能力A）

在 Chat 查询完成后触发，不走 VizAgent 完整链路，而是：

```
已有 SQL + 查询结果 → recommend_chart 节点 → 返回 {chart_type, echarts_option}
```

这是一个轻量级调用，不需要生成新 SQL，只做数据 → 图表的映射。

### 5.5 一句话生成图表链路（能力B）

```
parse_intent → generate_sqls → run_sqls → generate_charts → 返回 chart_config
```

### 5.6 AI 生成大屏链路（能力D）

```
parse_intent → plan_layout → generate_sqls (并行) → run_sqls (并行) → generate_charts (并行) → assemble_dashboard → 返回 dashboard
```

---

## 6. 前端设计

### 6.1 路由扩展

在现有 LeftMenu 导航中增加可视化分组：

```
/chat                              → ChatPage (已有，增强)
/viz/dashboards                    → DashboardListPage (新增)
/viz/dashboards/:id/edit           → DashboardEditor (新增)
/viz/dashboards/:id/view           → DashboardView (新增)
/viz/templates                     → TemplateMarket (新增)
```

### 6.2 ChatPage 增强

在现有 ChatPage 中，每个 `run_sql` 结果消息下方增加操作栏：

```
┌──────────────────────────────────────────────┐
│  📊 查询结果 (表格)                           │
│  ┌──────────────────────────────────────┐    │
│  │ a-table 渲染...                       │    │
│  └──────────────────────────────────────┘    │
│  [📊 一键成图] [➕ 加入大屏] [💾 保存为模板]   │
└──────────────────────────────────────────────┘
```

- **一键成图**：在当前消息气泡下方展开嵌入式图表（ECharts），支持切换图表类型
- **加入大屏**：弹出 Modal 列出已有大屏 + "创建新大屏" 选项
- **保存为模板**：弹出 Modal 填写模板名称/分类，保存 chart_config

Chat 输入框支持 `/chart` 命令：输入 `/chart 最近30天各品类销售额对比柱状图` 触发能力B。

### 6.3 DashboardListPage — 大屏列表

- 卡片式网格布局，每个卡片展示大屏缩略图 + 名称 + 状态 + 更新时间
- 顶部操作栏：搜索框、"新建大屏"按钮、"AI 创建大屏"按钮
- "AI 创建大屏"：弹出输入框，输入一句话描述，跳转能力D 流程
- 卡片 hover 显示操作按钮：编辑 / 预览 / 删除
- 右上角筛选：状态（草稿/已发布/已归档）

### 6.4 DashboardEditor — 大屏编辑器（核心页面）

对标 Grafana + DataV 的体验，采用经典三栏布局 + 顶部操作栏。

#### 顶部操作栏

```
⬅ 返回列表  [大屏名称输入框]       [💾 保存] [👁 预览] [📋 另存为模板] [🚀 发布]
```

#### 左侧面板（240px）— 组件库 + 图层管理

| 区域 | 内容 |
|------|------|
| 面板组件 | 可拖拽的图表类型列表：数字卡、折线图、柱状图、饼图、面积图、散点图、雷达图、仪表盘、漏斗图、热力图、地图、表格、文本、图片、分割线、筛选器 |
| 图层管理 | 大屏内所有面板的列表，支持拖拽排序、显示/隐藏、锁定 |
| 全局设置 | 大屏主题切换、背景设置、栅格密度 |

#### 中央画布 — 12 列栅格布局

- 使用 vue-grid-layout 实现自由拖拽和缩放
- 栅格吸附 + 碰撞检测
- 每个面板显示实时数据（编辑模式下执行 SQL 返回模拟数据或缓存数据）
- 选中面板显示蓝色边框 + 8 个拖拽手柄（四角 + 四边中点）
- 右键菜单：复制 / 删除 / 上移一层 / 下移一层 / 锁定 / 刷新数据
- 支持框选多个面板批量操作
- 支持 Undo/Redo（Ctrl+Z / Ctrl+Y）

#### 右侧配置面板（320px）— 四段式 Tab

| Tab | 配置项 |
|-----|-------|
| **基础** | 面板标题、描述、图表类型切换（切换时保留数据重新渲染） |
| **数据** | 数据源选择、SQL 编辑器（语法高亮 + 自动补全）、`🤖 AI 生成` 按钮、参数绑定（`{{变量}}` 语法提示）、数据预览表格 |
| **样式** | 颜色主题（预设色板）、图表标题/图例/坐标轴配置、字体大小/颜色、背景色/边框/圆角/阴影、Tooltip 格式、动画效果开关 |
| **高级** | 自动刷新间隔、下钻配置（点击跳转另一个大屏）、告警阈值（值超出范围变色）、面板间联动配置 |

#### 全局筛选器栏

位于画布上方，水平排列所有全局筛选器：
- 时间范围选择器（预设：今天/昨天/本周/本月/上月/近7天/近30天/自定义）
- 下拉选择器（从 SQL 动态获取选项）
- 多选下拉
- 文本输入
- 筛选器变化 → 触发所有含对应 `{{变量}}` 的面板重新查询

### 6.5 DashboardView — 大屏全屏展示

- 全屏深色背景，隐藏所有编辑 UI
- 按配置的刷新间隔自动轮询数据
- 右上角悬浮操作：退出全屏(ESC) / 刷新 / 编辑
- 适配多分辨率（1920x1080 / 3840x1080 超宽屏）
- 数字卡支持数字滚动动画
- 图表支持数据更新动画（ECharts 动态更新）

### 6.6 TemplateMarket — 模板市场

- 顶部分类 Tab：全部 / 电商 / 金融 / 物流 / 医疗 / 教育 / SaaS / 通用
- 卡片式网格，每个卡片展示：缩略图、模板名称、描述、使用次数
- 点击卡片 → 弹出预览 Modal（全屏展示大屏布局，只读）
- "使用此模板"按钮 → 选择目标数据源 → AI 自动映射 Schema → 创建新大屏 → 跳转编辑器
- 用户发布的模板在右上角标注"我的"，支持删除

---

## 7. 技术选型

| 层面 | 技术 | 说明 |
|------|------|------|
| 图表渲染 | ECharts 5 | 30+ 图表类型，WebGL 渲染，JSON option 驱动，AI 生成友好 |
| 拖拽布局 | vue-grid-layout | Vue 3 栅格拖拽组件，兼容 12 列栅格系统 |
| 代码编辑器 | Monaco Editor | SQL 编辑语法高亮 + 自动补全 |
| 颜色处理 | chroma.js | 色板生成、颜色映射 |
| 大屏动效 | ECharts 动画 + CSS transition | 数字滚动、渐变闪烁、数据更新动画 |

> **为什么选 ECharts：** LLM 天然擅长生成 JSON，ECharts 的 option 对象本身就是纯 JSON 配置，AI 可以直接输出完整图表配置。同时 ECharts 具备最全面的图表类型和最佳的大屏性能。

---

## 8. 新增文件清单

### 8.1 后端新增

```
app/
├── agent/
│   └── viz/                              # 新增 VizAgent
│       ├── __init__.py
│       ├── state.py                      # VizAgentState
│       ├── graph.py                      # StateGraph 编排
│       ├── llm.py                        # 复用现有 LLM
│       └── nodes/
│           ├── __init__.py
│           ├── parse_intent.py           # 解析意图
│           ├── plan_layout.py            # 规划布局
│           ├── generate_sqls.py          # 生成SQL（复用DataAgent）
│           ├── run_sqls.py               # 执行SQL
│           ├── generate_charts.py        # 生成图表配置
│           ├── recommend_chart.py        # 推荐图表类型
│           └── assemble_dashboard.py     # 组装大屏
├── api/
│   └── routers/
│       └── viz_router.py                 # 新增路由
├── services/
│   └── viz_service.py                    # 新增服务层
├── models/
│   ├── chart_config.py                   # 新增 ORM 模型
│   ├── dashboard.py                      # 新增 ORM 模型
│   ├── panel.py                          # 新增 ORM 模型
│   ├── dashboard_filter.py               # 新增 ORM 模型
│   └── viz_template.py                   # 新增 ORM 模型
├── repositories/
│   └── mysql/
│       └── viz/                           # 新增 Repository
│           ├── __init__.py
│           ├── chart_config_repository.py
│           ├── dashboard_repository.py
│           ├── panel_repository.py
│           ├── dashboard_filter_repository.py
│           └── template_repository.py
├── entities/
│   ├── chart_config.py                   # 新增 Entity
│   ├── dashboard.py                      # 新增 Entity
│   ├── panel.py                          # 新增 Entity
│   ├── dashboard_filter.py               # 新增 Entity
│   └── viz_template.py                   # 新增 Entity
└── prompt/
    ├── generate_chart.prompt             # 新增 Prompt
    ├── recommend_chart.prompt            # 新增 Prompt
    ├── parse_viz_intent.prompt           # 新增 Prompt
    ├── plan_layout.prompt                # 新增 Prompt
    └── map_schema.prompt                 # 新增 Prompt（模板 Schema 映射）
```

### 8.2 前端新增

```
frontend/src/
├── router/
│   └── index.js                          # 扩展路由
├── views/
│   └── viz/
│       ├── DashboardList.vue             # 大屏列表页
│       ├── DashboardEditor.vue           # 大屏编辑器
│       ├── DashboardView.vue             # 大屏全屏展示
│       └── TemplateMarket.vue            # 模板市场
├── components/
│   └── viz/
│       ├── ChartRenderer.vue             # ECharts 通用渲染组件
│       ├── ChartTypeIcon.vue             # 图表类型图标
│       ├── PanelCard.vue                 # 画布中的面板卡片
│       ├── ComponentPalette.vue          # 左侧组件库面板
│       ├── LayerManager.vue              # 左侧图层管理
│       ├── PanelConfigPanel.vue          # 右侧配置面板
│       ├── SqlEditor.vue                 # Monaco SQL 编辑器（带 AI 按钮）
│       ├── GlobalFilterBar.vue           # 全局筛选器栏
│       ├── FilterConfigModal.vue         # 筛选器配置弹窗
│       ├── DashboardCard.vue             # 大屏列表卡片
│       ├── TemplateCard.vue              # 模板市场卡片
│       ├── AiGenerateModal.vue           # AI 生成弹窗
│       └── AddToDashboardModal.vue       # 加入大屏弹窗
├── composables/
│   └── viz/
│       ├── useChartGenerate.js           # 图表生成逻辑
│       ├── useDashboard.js               # 大屏 CRUD 逻辑
│       └── useGridLayout.js              # 栅格布局状态管理
└── stores/
    └── viz.js                            # Pinia Store (大屏编辑状态)
```

### 8.3 Prompt 文件

```
prompts/
├── generate_chart.prompt                 # 生成 ECharts option
├── recommend_chart.prompt                # 推荐图表类型
├── parse_viz_intent.prompt               # 解析大屏意图
├── plan_layout.prompt                    # 规划栅格布局
└── map_schema.prompt                     # 模板 Schema 映射
```

---

## 9. 实施计划

### 阶段一：基础图表能力（能力A + B）

**目标**：Chat 内可以一键成图和 `/chart` 命令生成图表

- [ ] 新增 `chart_config` 表 ORM + Entity + Repository
- [ ] 实现 `POST /api/viz/charts/recommend`（一键成图）
- [ ] 实现 `POST /api/viz/charts/generate`（一句话生成图，SSE 流式）
- [ ] 新增 VizAgent 单图表链路节点：`recommend_chart`、`parse_intent`、`generate_sqls`、`run_sqls`、`generate_charts`
- [ ] 前端 ChatPage 增加操作按钮 + 嵌入式图表渲染组件 `ChartRenderer.vue`
- [ ] 前端 ChatPage 增加 `/chart` 命令识别

### 阶段二：大屏编辑器（能力C）

**目标**：完整的可拖拽大屏编辑器

- [ ] 新增 `dashboard`、`panel`、`dashboard_filter` 表 ORM + Entity + Repository
- [ ] 实现大屏 CRUD API + 面板 CRUD API + 筛选器 API
- [ ] 前端 `DashboardList.vue` 大屏列表页
- [ ] 前端 `DashboardEditor.vue` 编辑器（三栏布局）
- [ ] 实现 vue-grid-layout 拖拽编排
- [ ] 实现全局筛选器联动（变量替换 + SQL 重新执行）
- [ ] 前端 `DashboardView.vue` 全屏展示页
- [ ] "加入大屏"桥接功能

### 阶段三：AI 大屏生成（能力D）

**目标**：一句话生成完整大屏

- [ ] 新增 VizAgent 大屏链路节点：`parse_intent`（大屏版）、`plan_layout`、`assemble_dashboard`
- [ ] 实现 `POST /api/viz/dashboards/generate`（SSE 流式）
- [ ] 前端 `AiGenerateModal.vue` + 大屏列表页"AI 创建大屏"入口

### 阶段四：模板市场（能力F）

**目标**：模板发布、浏览、应用（含 AI Schema 映射）

- [ ] 新增 `template` 表 ORM + Entity + Repository
- [ ] 实现模板 CRUD API + 应用模板 API
- [ ] 新增 `map_schema` 节点（AI Schema 映射）
- [ ] 前端 `TemplateMarket.vue` 模板市场页面
- [ ] 系统预置 5-10 套行业模板
- [ ] 大屏编辑器内"另存为模板"功能

---

## 10. 风险与挑战

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| AI 生成 ECharts option 不准确 | 图表渲染错误或不符合预期 | 提供丰富的 few-shot 示例；前端支持用户手动调整 |
| 大屏多面板 SQL 并发执行压力 | 数据源负载过高 | 连接池限制并发数；支持缓存；面板逐个加载而非一次性全部 |
| 模板 Schema 映射准确率不足 | 用户需要大量手动调整 | 明确标注"未映射字段"；支持用户手动映射；持续优化 prompt |
| 大屏编辑器状态管理复杂 | 开发周期长、Bug 多 | 使用 Pinia 统一状态管理；参考 Grafana 开源代码的编排逻辑 |
| vue-grid-layout 与 ECharts 渲染冲突 | 拖拽时图表重绘闪烁 | 拖拽期间使用缩略图占位；拖拽结束后才重新渲染 ECharts |