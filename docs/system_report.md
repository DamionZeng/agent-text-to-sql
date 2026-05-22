## 系统现状审查报告
### 🔴 高优先级（安全/稳定性）
1. SQL 注入风险

- mysql_executor.py:18 ： SHOW COLUMNS FROM {table_name} 使用 f-string 拼接
- mysql_executor.py:21 ： SELECT DISTINCT ... FROM {table_name} 同样
- postgresql_executor.py:25 ： SELECT DISTINCT "{column_name}" FROM {table_name}
- meta_mysql_repository.py:76 ： f"select * from column_info where table_id='{table_id}'" — 直接拼接用户可控的 table_id
- explain_sql 和 run_sql 中的 SQL 都是直接执行，虽然 SQL 是 AI 生成的，但 explain_sql 中 f"EXPLAIN {sql}" 仍存在风险
2. 密码明文存储

- datasource_mapper.py ：数据库模型注释写了"密码(AES加密)"，但实际存储和读取都是明文，没有任何加密/解密逻辑
- DatasourceResponseSchema ：响应中虽然没返回 password 字段，但更新接口可以传 password
3. 删除数据源不级联清理

- metadata_router.py:92 ： delete_datasource 只删除数据库记录，不清理：
  - Qdrant 中的 column_info / metric 数据
  - ES 中的 value 数据
  - MySQL 中的 table_info / column_info / metric_info / column_metric
  - DatasourceManager 中的引擎缓存（ unregister 从未被调用）
### 🟡 中优先级（架构/设计）
4. MetaKnowledgeService 的 build_from_config_with_session 设计不优雅

- meta_knowledge_service.py:241-253 ：临时替换 dw_session 、 datasource_type 、 _executor ，用 try/finally 恢复。这不是线程安全的，并发时会出问题
5. 数据源注册分散，无启动时自动注册

- datasource_manager.register(datasource) 散落在 5 个地方（analyze_schema、metadata_service、query_service、metadata_router、build_knowledge）
- 应用重启后 DatasourceManager 内存缓存清空，必须等到第一次请求才注册，应考虑在 lifespan 启动时从数据库加载所有 active 数据源
6. publish 接口与 sync 接口逻辑重复

- metadata_router.py:256-311 ： publish_metadata 中手动解析 draft JSON 为 MetaConfig，和 build_knowledge.py:20-55 中完全重复
7. build_meta_knowledge.py 脚本传了错误的 dw_session

- build_meta_knowledge.py:31 ： dw_session=meta_session ，把 meta 库的 session 当作数据仓库的 session 传入了，这会导致查询的是 meta 库的表而不是目标数据仓库的表
### 🟢 低优先级（完善/优化）
8. 缺少 CORS 中间件

- main.py 没有配置 CORS，前端跨域请求会被浏览器拦截
9. 缺少全局异常处理

- 没有统一的 exception_handler，未捕获异常会直接返回 FastAPI 默认的 500 错误格式，不利于前端统一处理
10. Qdrant 缺少 Payload 索引

- column_info_collection 和 metric_collection 都没有创建 payload 索引（如 table_id 、 metric_id ），数据量大时过滤查询会很慢
11. DatasourceManager._dispose_engine 的异步处理

- manager.py:51-58 ：用 asyncio.get_event_loop() + create_task 的方式 dispose 引擎，在 FastAPI 的异步环境中可能不可靠，应改为纯异步方式
12. MySQL Executor 的 SHOW TABLES 不限定数据库

- mysql_executor.py:15 ： SHOW TABLES 依赖连接时选择的数据库，如果连接 URL 中没指定数据库或指定错误，会返回错误结果
13. 缺少健康检查接口

- 没有 /health 或 /ready 端点，不利于容器化部署时的探针检测
14. 缺少分页查询

- list_datasources 、 list_draft_versions 没有分页参数，数据量大时性能差