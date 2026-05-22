from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agents.chat_agent.context import DataAgentContext
from app.agents.common_nodes.llm import llm
from app.agents.chat_agent.state import DataAgentState
from app.entities.metric_info import MetricInfo
from app.prompt.prompt_loader import load_prompt
from app.core.log import logger

async def recall_metric(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "召回指标", "status": "running"})
    try:
        query = state['query']
        keywords = state['keywords']
        embedding_client = runtime.context['embedding_client']
        metric_qdrant_repository = runtime.context['metric_qdrant_repository']

        prompt = PromptTemplate(template=load_prompt("extend_keywords_for_metric_recall"), input_variables=['query'])
        output_parser_custom = JsonOutputParser()
        chain = prompt | llm | output_parser_custom
        result = await chain.ainvoke({"query": query})
        keywords = set(keywords + result)

        metric_infos_map: dict[str, MetricInfo] = {}

        for keyword in keywords:
            embedding = await embedding_client.aembed_query(keyword)
            current_column_infos: list[MetricInfo] = await metric_qdrant_repository.search(embedding)
            for column_info in current_column_infos:
                if column_info.id not in metric_infos_map:
                    metric_infos_map[column_info.id] = column_info

        retrieved_column_infos:list[MetricInfo] = list(metric_infos_map.values())
        logger.info(f"检索检索到的指标信息: {list(metric_infos_map.keys())}")
        writer({"type": "progress", "step": "召回指标", "status": "success"})
        return {"retrieved_metric_infos": retrieved_column_infos}
    except Exception as e:
        logger.error(f"召回指标失败: {str(e)}")
        writer({"type": "progress", "step": "召回指标", "status": "error"})
        raise e