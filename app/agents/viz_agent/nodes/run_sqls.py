from langgraph.runtime import Runtime

from app.agents.viz_agent.context import VizAgentContext
from app.agents.viz_agent.state import VizAgentState
from app.core.log import logger


async def run_sqls(state: VizAgentState, runtime: Runtime[VizAgentContext]):
    writer = runtime.stream_writer
    chart_configs = state.get("chart_configs", [])
    total = len(chart_configs)
    query_results = []

    from app.clients.datasource import datasource_manager
    from app.repositories.db_executor import get_executor

    datasource_id = state.get("datasource_id", "")
    config = datasource_manager.get_config(datasource_id)
    executor = get_executor(config.db_type)

    for i, cc in enumerate(chart_configs):
        sql = cc.get("sql", "")
        chart_name = cc.get("chart_name", f"面板{i + 1}")
        try:
            writer({"type": "progress", "step": f"执行SQL ({i + 1}/{total})", "status": "running", "message": chart_name})

            async with datasource_manager.get_session(datasource_id) as session:
                data = await executor.query(session, sql)

            query_results.append(data)
            writer({"type": "progress", "step": f"执行SQL ({i + 1}/{total})", "status": "success", "message": chart_name})
        except Exception as e:
            logger.error(f"执行SQL失败 [{chart_name}]: {str(e)}")
            writer({"type": "progress", "step": f"执行SQL ({i + 1}/{total})", "status": "error", "message": str(e)})
            query_results.append([])

    return {"query_results": query_results}