from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def validate_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "校验SQL", "status": "running"})
    try:
        sql = state['sql']
        datasource_id = state.get('datasource_id')

        from app.clients.datasource import datasource_manager
        from app.repositories.db_executor import get_executor

        config = datasource_manager.get_config(datasource_id)
        executor = get_executor(config.db_type)

        try:
            async with datasource_manager.get_session(datasource_id) as session:
                await executor.explain_sql(session, sql)
            logger.info("SQL语法正确")
            writer({"type": "progress", "step": "校验SQL", "status": "success"})
            return {"error": None}
        except Exception as e:
            logger.info(f"SQL语法错误: {str(e)}")
            writer({"type": "progress", "step": "校验SQL", "status": "success"})
            return {"error": str(e)}
    except Exception as e:
        logger.error(f"校验SQL失败: {str(e)}")
        writer({"type": "progress", "step": "校验SQL", "status": "error"})
        raise e
