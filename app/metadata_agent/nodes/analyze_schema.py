import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.metadata_agent.state import MetaAgentState


async def analyze_schema(state: MetaAgentState) -> dict:
    """连接数据源，获取原始 Schema"""
    datasource_id = state["datasource_id"]

    try:
        # 这里简化处理，实际应该从 datasource_repository 获取连接信息
        # 为了演示，使用默认的 dw 连接
        from app.clients.mysql_client_manager import dw_mysql_client_manager

        session_factory = dw_mysql_client_manager.session_factory
        async with session_factory() as session:
            # 获取所有表名
            result = await session.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result.fetchall()]

            raw_schema = []
            for table_name in tables:
                # 获取表字段信息
                result = await session.execute(text(f"SHOW COLUMNS FROM {table_name}"))
                columns = []
                for row in result.fetchall():
                    col_name = row[0]
                    col_type = row[1]
                    # 获取示例值
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

        return {"raw_schema": raw_schema, "error": None}
    except Exception as e:
        return {"error": f"分析 Schema 失败: {str(e)}"}
