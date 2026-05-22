from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agents.chat_agent.context import DataAgentContext
from app.agents.common_nodes.llm import llm
from app.agents.chat_agent.state import DataAgentState
from app.entities.column_info import ColumnInfo
from app.prompt.prompt_loader import load_prompt
from app.core.log import logger


async def recall_column(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "召回字段", "status": "running"})
    try:
        keywords = state["keywords"]
        query =state["query"]
        column_qdrant_repository = runtime.context["column_qdrant_repository"]
        embedding_client = runtime.context["embedding_client"]

        prompt = PromptTemplate(template=load_prompt("extend_keywords_for_column_recall"), input_variables=['query'])
        output_parser_custom = JsonOutputParser()

        chain = prompt | llm | output_parser_custom

        result = await chain.ainvoke({"query": query})

        keywords = set(keywords + result)

        column_infos_map: dict[str, ColumnInfo] = {}

        for keyword in keywords:
            embedding = await embedding_client.aembed_query(keyword)
            current_column_infos: list[ColumnInfo] = await column_qdrant_repository.search(embedding)
            for column_info in current_column_infos:
                if column_info.id not in column_infos_map:
                    column_infos_map[column_info.id] = column_info

        retrieved_column_infos:list[ColumnInfo] = list(column_infos_map.values())
        logger.info(f"检索检索到的字段信息: {list(column_infos_map.keys())}")
        writer({"type": "progress", "step": "召回字段", "status": "success"})
        return {"retrieved_column_infos": retrieved_column_infos}
    except Exception as e:
        logger.error(f"召回字段失败: {str(e)}")
        writer({"type": "progress", "step": "召回字段", "status": "error"})
        raise e