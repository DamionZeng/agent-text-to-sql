from langgraph.runtime import Runtime

from app.metadata_agent.context import MetaAgentContext
from app.metadata_agent.state import MetaAgentState
from app.core.log import logger


async def analyze_schema(state: MetaAgentState, runtime: Runtime[MetaAgentContext]) -> dict:
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "分析数据库结构", "status": "running", "message": "正在连接数据源..."})

    datasource_id = state["datasource_id"]

    try:
        from app.clients.datasource import datasource_manager
        from app.repositories.db_executor import get_executor

        datasource_repository = runtime.context["datasource_repository"]
        datasource = await datasource_repository.get_by_id(datasource_id)
        if not datasource:
            raise ValueError(f"数据源不存在: {datasource_id}")

        datasource_manager.register(datasource)
        config = datasource_manager.get_config(datasource_id)
        executor = get_executor(config.db_type)

        async with datasource_manager.get_session(datasource_id) as session:
            writer({"type": "progress", "step": "分析数据库结构", "status": "running", "message": "获取表列表..."})

            tables = await executor.list_tables(session, datasource.database)

            raw_schema = []
            for i, table_name in enumerate(tables):
                writer({"type": "progress", "step": "分析数据库结构", "status": "running", "message": f"分析表 {table_name} ({i+1}/{len(tables)})"})

                columns_meta = await executor.get_columns(session, table_name, datasource.database)
                columns = []
                for col in columns_meta:
                    try:
                        examples = await executor.get_column_values(session, table_name, col.name, 5)
                        examples = [str(v) for v in examples if v is not None]
                    except Exception:
                        examples = []
                    columns.append({"name": col.name, "type": col.type, "examples": examples})

                raw_schema.append({"name": table_name, "columns": columns})

        writer({"type": "progress", "step": "分析数据库结构", "status": "success", "message": f"获取到 {len(raw_schema)} 张表"})
        logger.info(f"analyze_schema 完成，获取到 {len(raw_schema)} 张表")
        return {"raw_schema": raw_schema, "error": None}
    except Exception as e:
        logger.error(f"analyze_schema 失败: {str(e)}")
        writer({"type": "progress", "step": "分析数据库结构", "status": "error", "message": str(e)})
        return {"error": f"分析 Schema 失败: {str(e)}"}
