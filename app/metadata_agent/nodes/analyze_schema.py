import json

from langgraph.runtime import Runtime
from sqlalchemy import text

from app.metadata_agent.context import MetaAgentContext
from app.metadata_agent.state import MetaAgentState
from app.core.log import logger


async def analyze_schema(state: MetaAgentState, runtime: Runtime[MetaAgentContext]) -> dict:
    """连接数据源，获取原始 Schema"""
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "analyze_schema", "status": "running", "message": "正在连接数据源..."})

    datasource_id = state["datasource_id"]

    try:
        from app.clients.mysql_client_manager import dw_mysql_client_manager

        session_factory = dw_mysql_client_manager.session_factory
        async with session_factory() as session:
            writer({"type": "progress", "step": "analyze_schema", "status": "running", "message": "获取表列表..."})
            result = await session.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result.fetchall()]

            raw_schema = []
            for i, table_name in enumerate(tables):
                writer({"type": "progress", "step": "analyze_schema", "status": "running", "message": f"分析表 {table_name} ({i+1}/{len(tables)})"})
                
                result = await session.execute(text(f"SHOW COLUMNS FROM {table_name}"))
                columns = []
                for row in result.fetchall():
                    col_name = row[0]
                    col_type = row[1]
                    try:
                        sample_result = await session.execute(
                            text(f"SELECT DISTINCT `{col_name}` FROM {table_name} LIMIT 5")
                        )
                        examples = [str(r[0]) for r in sample_result.fetchall() if r[0] is not None]
                    except Exception:
                        examples = []

                    columns.append({
                        "name": col_name,
                        "type": col_type,
                        "examples": examples
                    })

                raw_schema.append({
                    "name": table_name,
                    "columns": columns
                })

        writer({"type": "progress", "step": "analyze_schema", "status": "success", "message": f"获取到 {len(raw_schema)} 张表"})
        logger.info(f"analyze_schema 完成，获取到 {len(raw_schema)} 张表")
        return {"raw_schema": raw_schema, "error": None}
    except Exception as e:
        logger.error(f"analyze_schema 失败: {str(e)}")
        writer({"type": "progress", "step": "analyze_schema", "status": "error", "message": str(e)})
        return {"error": f"分析 Schema 失败: {str(e)}"}
