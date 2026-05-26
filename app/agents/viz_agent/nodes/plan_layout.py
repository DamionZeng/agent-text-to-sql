import json

from langgraph.runtime import Runtime

from app.agents.common_nodes.llm import llm
from app.agents.viz_agent.context import VizAgentContext
from app.agents.viz_agent.state import VizAgentState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt


async def plan_layout(state: VizAgentState, runtime: Runtime[VizAgentContext]):
    writer = runtime.stream_writer

    try:
        writer({"type": "progress", "step": "plan_layout", "status": "running", "message": "正在规划栅格布局..."})

        chart_configs = state.get("chart_configs", [])

        chart_infos = json.dumps([
            {
                "chart_name": c.get("chart_name", "未命名"),
                "chart_type": c.get("chart_type", "bar"),
            }
            for c in chart_configs
        ], ensure_ascii=False, indent=2)

        prompt = load_prompt("plan_layout")
        prompt = prompt.format(chart_infos=chart_infos)

        response = await llm.ainvoke(prompt)
        content = response.content.strip()

        if content.startswith("```"):
            content = content.strip("`").strip()
            if content.startswith("json"):
                content = content[4:].strip()

        layout_plan = json.loads(content)
        if not isinstance(layout_plan, list):
            layout_plan = []

        for i, layout_item in enumerate(layout_plan):
            if i < len(chart_configs):
                chart_configs[i]["layout_x"] = layout_item.get("layout_x", 0)
                chart_configs[i]["layout_y"] = layout_item.get("layout_y", 0)
                chart_configs[i]["layout_w"] = layout_item.get("layout_w", 6)
                chart_configs[i]["layout_h"] = layout_item.get("layout_h", 4)

        writer({
            "type": "progress",
            "step": "plan_layout",
            "status": "success",
            "message": f"为 {len(layout_plan)} 个面板规划了布局",
        })

        return {"layout_plan": layout_plan, "chart_configs": chart_configs}

    except Exception as e:
        logger.error(f"规划大屏布局失败: {str(e)}")
        writer({"type": "progress", "step": "plan_layout", "status": "error"})
        raise e