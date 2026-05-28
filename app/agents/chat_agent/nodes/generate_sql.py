import yaml
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agents.chat_agent.context import DataAgentContext
from app.agents.common_nodes.llm import llm
from app.agents.chat_agent.state import DataAgentState
from app.prompt.prompt_loader import load_prompt
from app.core.log import logger


async def generate_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "生成SQL", "status": "running"})
    try:
        query = state['query']
        db_info = state['db_info']
        date_info = state['date_info']
        table_infos = state['table_infos']
        metric_infos = state['metric_infos']

        prompt = PromptTemplate(template=load_prompt("generate_sql"), input_variables=['table_infos', 'metric_infos',
                                                                                       'date_info', 'db_info', 'query'])
        output_parser_custom = StrOutputParser()

        chain = prompt | llm | output_parser_custom

        result = await chain.ainvoke({
            'table_infos': yaml.dump(table_infos, allow_unicode=True, sort_keys=False),
            'metric_infos': yaml.dump(metric_infos, allow_unicode=True, sort_keys=False),
            'date_info': yaml.dump(date_info, allow_unicode=True, sort_keys=False),
            'db_info': yaml.dump(db_info, allow_unicode=True, sort_keys=False),
            'query': query
        })

        logger.info(f"生成的sql: {result}")
        writer({"type": "progress", "step": "生成SQL", "status": "success"})
        writer({"type": "sql", "sql": result})
        return {'sql': result, 'retry_count': 0}
    except Exception as e:
        logger.error(f"生成SQL失败: {str(e)}")
        writer({"type": "progress", "step": "生成SQL", "status": "error"})
        raise e