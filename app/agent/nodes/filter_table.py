import yaml
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState, TableInfoState, ColumnInfoState
from app.prompt.prompt_loader import load_prompt
from app.core.log import logger

async def filter_table(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "过滤表信息", "status": "running"})
    try:
        query = state['query']
        table_infos: list[TableInfoState] = state['table_infos']
        # 借助LLM 过滤信息
        prompt = PromptTemplate(template=load_prompt("filter_table_info"), input_variables=['query', 'table_infos'])
        output_parser_custom = JsonOutputParser()

        chain = prompt | llm | output_parser_custom
        table_infos_yaml = yaml.dump(table_infos, allow_unicode=True, sort_keys=False)
        result = await chain.ainvoke({"query": query, "table_infos": table_infos_yaml})

        filtered_table_infos: list[TableInfoState] = []
        for table_info in table_infos:
            if table_info["name"] in result:
                table_info['columns'] = [column_info_state for column_info_state in table_info['columns']
                                         if column_info_state['name'] in result[table_info["name"]]]
                filtered_table_infos.append(table_info)
        filtered_table_names: list[str] = [filtered_table_info['name'] for filtered_table_info in filtered_table_infos]
        logger.info(f"过滤后的表信息: {filtered_table_names}")
        writer({"type": "progress", "step": "过滤表信息", "status": "success"})
        return {"table_infos": filtered_table_infos}
    except Exception as e:
        logger.error(f"过滤表信息失败: {str(e)}")
        writer({"type": "progress", "step": "过滤表信息", "status": "error"})
        raise e

