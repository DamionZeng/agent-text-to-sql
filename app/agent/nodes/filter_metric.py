

import yaml
from dns.e164 import query
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.prompt.prompt_loader import load_prompt
from app.core.log import logger


async def filter_metric(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "过滤指标信息", "status": "running"})
    try:
        query = state["query"]
        metric_infos = state["metric_infos"]

        # 借助LLM 过滤信息
        prompt = PromptTemplate(template=load_prompt("filter_metric_info"), input_variables=['query', 'metric_infos'])
        output_parser_custom = JsonOutputParser()

        chain = prompt | llm | output_parser_custom
        metric_infos_yaml = yaml.dump(metric_infos, allow_unicode=True, sort_keys=False)
        result = await chain.ainvoke({"query": query, "metric_infos": metric_infos_yaml})
        filter_metric_infos = [metric_info for metric_info in metric_infos if metric_info['name'] in result]
        filter_metric_names = [filter_metric_info['name'] for filter_metric_info in filter_metric_infos]
        logger.info(f"过滤后的指标信息: {filter_metric_names}")
        writer({"type": "progress", "step": "过滤指标信息", "status": "success"})
        return {"metric_infos": filter_metric_infos}
    except Exception as e:
        logger.error(f"过滤指标信息失败: {str(e)}")
        writer({"type": "progress", "step": "过滤指标信息", "status": "error"})
        raise e