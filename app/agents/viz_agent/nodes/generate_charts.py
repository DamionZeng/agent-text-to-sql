import json

from langgraph.runtime import Runtime

from app.agents.common_nodes.llm import llm
from app.agents.viz_agent.context import VizAgentContext
from app.agents.viz_agent.state import VizAgentState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt


async def generate_charts(state: VizAgentState, runtime: Runtime[VizAgentContext]):
    writer = runtime.stream_writer
    chart_configs = state.get("chart_configs", [])
    query_results = state.get("query_results", [])
    total = len(chart_configs)

    updated_configs = []

    for i, cc in enumerate(chart_configs):
        chart_name = cc.get("chart_name", f"面板{i + 1}")
        sql = cc.get("sql", "")
        result_data = query_results[i] if i < len(query_results) else []

        try:
            writer({"type": "progress", "step": "generate_charts", "panel_index": i, "panel_name": chart_name, "status": "running", "message": f"({i + 1}/{total}) {chart_name}"})

            result_sample = result_data[:20] if len(result_data) > 20 else result_data
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

            updated_config = {
                **cc,
                "echarts_option": chart_data.get("echarts_option", {}),
                "chart_type": chart_data.get("chart_type", cc.get("chart_type", "bar")),
            }
            updated_configs.append(updated_config)

            writer({"type": "progress", "step": "generate_charts", "panel_index": i, "panel_name": chart_name, "status": "success", "message": f"({i + 1}/{total}) {chart_name}"})
        except Exception as e:
            logger.error(f"生成图表配置失败 [{chart_name}]: {str(e)}")
            writer({"type": "progress", "step": "generate_charts", "panel_index": i, "panel_name": chart_name, "status": "error", "message": f"({i + 1}/{total}) {chart_name} - {str(e)}"})
            updated_configs.append(cc)

    return {"chart_configs": updated_configs}