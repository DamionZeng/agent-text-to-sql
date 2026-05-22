import datetime

from langgraph.runtime import Runtime

from app.agents.chat_agent.context import DataAgentContext
from app.agents.chat_agent.state import DataAgentState, DateInfoState, DBInfoState
from app.core.log import logger


async def add_extra_context(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "添加额外上下文", "status": "running"})

    try:
        datasource_id = state.get('datasource_id')

        from app.clients.datasource import datasource_manager
        from app.repositories.db_executor import get_executor

        ds_config = datasource_manager.get_config(datasource_id)
        executor = get_executor(ds_config.db_type)

        today = datetime.date.today()
        date_str = today.strftime("%Y-%m-%d")
        week_day = today.strftime("%A")
        quarter = f"Q{(today.month) // 3 + 1}"
        date_info = DateInfoState(date=date_str, weekday=week_day, quarter=quarter)

        async with datasource_manager.get_session(datasource_id) as session:
            version = await executor.get_version(session)

        db_info: DBInfoState = DBInfoState(dialect=ds_config.db_type, version=version)
        logger.info(f"日期信息:{date_info}; 数据库信息:{db_info}")
        writer({"type": "progress", "step": "添加额外上下文", "status": "success"})
        return {
            "date_info": date_info,
            "db_info": db_info
        }
    except Exception as e:
        logger.error(f"添加额外上下文失败: {str(e)}")
        writer({"type": "progress", "step": "添加额外上下文", "status": "error"})
        raise e