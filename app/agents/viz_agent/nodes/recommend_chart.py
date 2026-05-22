import json
import uuid

from langgraph.runtime import Runtime

from app.agents.common_nodes.llm import llm
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt
from app.agents.viz_agent.context import VizAgentContext
from app.agents.viz_agent.state import VizAgentState
from app.entities.chart_config import ChartConfig


async def recommend_chart(state: VizAgentState, runtime: Runtime[VizAgentContext]):
    writer = runtime.stream_writer
    context = runtime.context

    try:
        writer({"type": "progress", "step": "分析数据并生成图表配置", "status": "running"})

        sql = state.get("sql", "")
        query_result = state.get("query_result", [])
        datasource_id = state.get("datasource_id", "")

        result_sample = query_result[:20] if len(query_result) > 20 else query_result
        result_str = json.dumps(result_sample, ensure_ascii=False, indent=2)

        prompt = load_prompt("recommend_chart")
        prompt = prompt.format(sql=sql, query_result=result_str)

        response = await llm.ainvoke(prompt)
        content = response.content.strip()

        if content.startswith("```"):
            content = content.strip("`").strip()
            if content.startswith("json"):
                content = content[4:].strip()

        chart_data = json.loads(content)

        chart_id = str(uuid.uuid4())
        chart_entity = ChartConfig(
            id=chart_id,
            datasource_id=datasource_id,
            name=chart_data.get("name", "未命名图表"),
            chart_type=chart_data.get("chart_type", "bar"),
            sql_text=sql,
            echarts_option=chart_data.get("echarts_option", {}),
            auto_generated=True,
        )

        saved = await context["chart_config_repository"].create(chart_entity)

        writer({"type": "progress", "step": "分析数据并生成图表配置", "status": "success"})
        writer({
            "type": "chart_result",
            "chart_id": saved.id,
            "chart_name": saved.name,
            "chart_type": saved.chart_type,
            "echarts_option": saved.echarts_option,
        })

        return {"chart_config": chart_data, "chart_ids": [saved.id]}

    except Exception as e:
        logger.error(f"生成图表配置失败: {str(e)}")
        writer({"type": "progress", "step": "分析数据并生成图表配置", "status": "error"})
        raise e