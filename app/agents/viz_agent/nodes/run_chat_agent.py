from langgraph.runtime import Runtime

from app.agents.chat_agent.context import DataAgentContext
from app.agents.chat_agent.graph import graph as chat_agent_graph
from app.agents.chat_agent.state import DataAgentState
from app.agents.viz_agent.context import VizAgentContext
from app.agents.viz_agent.state import VizAgentState
from app.core.log import logger


async def run_chat_agent(state: VizAgentState, runtime: Runtime[VizAgentContext]):
    writer = runtime.stream_writer
    context = runtime.context
    query = state["query"]
    datasource_id = state["datasource_id"]

    writer({"type": "progress", "step": "生成SQL", "status": "running"})

    try:
        chat_context = DataAgentContext(
            embedding_client=context["embedding_client"],
            column_qdrant_repository=context["column_qdrant_repository"],
            value_es_repository=context["value_es_repository"],
            metric_qdrant_repository=context["metric_qdrant_repository"],
            meta_mysql_repository=context["meta_mysql_repository"],
            datasource_repository=context["datasource_repository"],
        )
        chat_state = DataAgentState(query=query, datasource_id=datasource_id)

        result = await chat_agent_graph.ainvoke(input=chat_state, context=chat_context)
        sql = result.get("sql", "")
        error = result.get("error")

        if error:
            logger.warning(f"chat_agent 生成SQL时出错: {error}")
            writer({"type": "progress", "step": "生成SQL", "status": "error"})
            return {"sql": sql, "query_result": []}

        logger.info(f"chat_agent 生成SQL: {sql}")

        from app.clients.datasource import datasource_manager
        from app.repositories.db_executor import get_executor

        config = datasource_manager.get_config(datasource_id)
        executor = get_executor(config.db_type)

        async with datasource_manager.get_session(datasource_id) as session:
            query_result = await executor.query(session, sql)

        logger.info(f"SQL执行完成，返回{len(query_result)}条记录")
        writer({"type": "progress", "step": "生成SQL", "status": "success"})

        return {"sql": sql, "query_result": query_result}

    except Exception as e:
        logger.error(f"run_chat_agent 执行失败: {str(e)}")
        writer({"type": "progress", "step": "生成SQL", "status": "error"})
        raise e