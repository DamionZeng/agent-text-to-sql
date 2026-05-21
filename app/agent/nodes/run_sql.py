from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def run_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "运行SQL", "status": "running"})
    try:
        sql = state.get('sql')
        datasource_id = state.get('datasource_id')

        from app.clients.datasource import datasource_manager
        from app.repositories.db_executor import get_executor

        config = datasource_manager.get_config(datasource_id)
        executor = get_executor(config.db_type)

        async with datasource_manager.get_session(datasource_id) as session:
            data = await executor.query(session, sql)

        logger.info(f"运行结果: {data}")
        writer({"type": "progress", "step": "运行SQL", "status": "success"})
        writer({"type": "result", "data": data})
    except Exception as e:
        logger.error(f"运行SQL失败: {str(e)}")
        writer({"type": "progress", "step": "运行SQL", "status": "error"})
        raise e
