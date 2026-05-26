import asyncio

from langgraph.runtime import Runtime

from app.agents.chat_agent.context import DataAgentContext
from app.agents.chat_agent.graph import graph as chat_graph
from app.agents.chat_agent.state import DataAgentState
from app.agents.viz_agent.context import VizAgentContext
from app.agents.viz_agent.state import VizAgentState
from app.core.log import logger


def _build_data_agent_context(viz_context: VizAgentContext) -> DataAgentContext:
    return DataAgentContext(
        column_qdrant_repository=viz_context["column_qdrant_repository"],
        embedding_client=viz_context["embedding_client"],
        metric_qdrant_repository=viz_context["metric_qdrant_repository"],
        value_es_repository=viz_context["value_es_repository"],
        meta_mysql_repository=viz_context["meta_mysql_repository"],
        datasource_repository=viz_context["datasource_repository"],
    )


async def _process_one_panel(
    index: int,
    total: int,
    cc: dict,
    datasource_id: str,
    data_agent_context: DataAgentContext,
    writer,
):
    chart_name = cc.get("chart_name", f"面板{index + 1}")
    description = cc.get("description", chart_name)

    try:
        writer({
            "type": "progress",
            "step": "generate_sqls",
            "panel_index": index,
            "panel_name": chart_name,
            "status": "running",
            "message": f"({index + 1}/{total}) {chart_name}",
        })

        state = DataAgentState(query=description, datasource_id=datasource_id)
        result = await chat_graph.ainvoke(input=state, context=data_agent_context)

        sql = result.get("sql", "")
        query_result = result.get("query_result", [])

        cc["sql"] = sql
        cc["query_result"] = query_result

        writer({
            "type": "progress",
            "step": "generate_sqls",
            "panel_index": index,
            "panel_name": chart_name,
            "status": "success",
            "message": f"({index + 1}/{total}) {chart_name} - {len(query_result)} 条数据",
        })

        return index, cc, query_result

    except Exception as e:
        logger.error(f"面板 [{chart_name}] SQL 生成失败: {str(e)}")
        writer({
            "type": "progress",
            "step": "generate_sqls",
            "panel_index": index,
            "panel_name": chart_name,
            "status": "error",
            "message": f"({index + 1}/{total}) {chart_name} - {str(e)}",
        })
        cc["sql"] = ""
        cc["query_result"] = []
        return index, cc, []


async def generate_sqls_via_chat_agent(state: VizAgentState, runtime: Runtime[VizAgentContext]):
    writer = runtime.stream_writer
    context = runtime.context

    chart_configs = state.get("chart_configs", [])
    datasource_id = state["datasource_id"]
    total = len(chart_configs)

    if total == 0:
        return {"chart_configs": chart_configs, "query_results": []}

    from app.clients.datasource import datasource_manager
    from app.repositories.mysql.meta.datasource_repository import DatasourceRepository

    if datasource_id and not datasource_manager.is_registered(datasource_id):
        datasource_repository = context["datasource_repository"]
        datasource = await datasource_repository.get_by_id(datasource_id)
        if datasource:
            datasource_manager.register(datasource)

    data_agent_context = _build_data_agent_context(context)

    writer({
        "type": "progress",
        "step": "generate_sqls",
        "status": "running",
        "message": f"开始并行生成 {total} 个面板的 SQL...",
    })

    tasks = [
        _process_one_panel(i, total, cc.copy(), datasource_id, data_agent_context, writer)
        for i, cc in enumerate(chart_configs)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    updated_configs = [chart_configs.copy() for _ in range(total)]
    query_results = [[] for _ in range(total)]

    for result in results:
        if isinstance(result, Exception):
            logger.error(f"并行处理面板异常: {str(result)}")
            continue
        index, updated_cc, qr = result
        updated_configs[index] = updated_cc
        query_results[index] = qr

    writer({
        "type": "progress",
        "step": "generate_sqls",
        "status": "success",
        "message": f"完成 {total} 个面板的 SQL 生成与执行",
    })

    return {"chart_configs": updated_configs, "query_results": query_results}