import jieba.analyse
from langgraph.runtime import Runtime

from app.agents.chat_agent.context import DataAgentContext
from app.agents.chat_agent.state import DataAgentState
from app.core.log import logger

async def extract_keywords(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "抽取关键词", "status": "running"})
    try:
        query = state["query"]

        allow_pos = (
            "n",
            "nr",
            "ns",
            "nt",
            "nz",
            "v",
            "vn",
            "a",
            "an",
            "eng",
            "i",
            "l",
        )

        keywords = jieba.analyse.extract_tags(query, allowPOS=allow_pos)

        keywords = list(set(keywords + [query]))
        logger.info(f"抽取关键词: {keywords}")
        writer({"type": "progress", "step": "抽取关键词", "status": "success"})
        return {"keywords": keywords}
    except Exception as e:
        logger.error(f"抽取关键词失败：{str(e)}")
        writer({"type": "progress", "step": "抽取关键词", "status": "error"})
        raise e