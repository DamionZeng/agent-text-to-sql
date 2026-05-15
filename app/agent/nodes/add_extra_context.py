import datetime

from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState, DateInfoState, DBInfoState
from app.core.log import logger


async def add_extra_context(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "添加额外上下文", "status": "running"})

    try:
        dw_mysql_repository = runtime.context['dw_mysql_repository']

        today = datetime.date.today()
        date_str = today.strftime("%Y-%m-%d")
        week_day = today.strftime("%A")
        quarter = f"Q{(today.month) // 3 + 1}"
        date_info = DateInfoState(date=date_str, weekday=week_day, quarter=quarter)

        db_info: DBInfoState = await dw_mysql_repository.get_db_info()
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



