import json
import uuid

from langgraph.runtime import Runtime

from app.agents.viz_agent.context import VizAgentContext
from app.agents.viz_agent.state import VizAgentState
from app.core.log import logger
from app.entities.chart_config import ChartConfig
from app.entities.dashboard import Dashboard
from app.entities.panel import Panel


async def assemble_dashboard(state: VizAgentState, runtime: Runtime[VizAgentContext]):
    writer = runtime.stream_writer
    context = runtime.context

    try:
        writer({"type": "progress", "step": "assemble_dashboard", "status": "running", "message": "正在保存大屏数据..."})

        datasource_id = state["datasource_id"]
        dashboard_name = state.get("dashboard_name", "AI生成的大屏")
        chart_configs = state.get("chart_configs", [])

        dashboard_repository = context["dashboard_repository"]
        panel_repository = context["panel_repository"]
        chart_config_repository = context["chart_config_repository"]

        dashboard_id = str(uuid.uuid4())
        dashboard = Dashboard(
            id=dashboard_id,
            name=dashboard_name,
            datasource_id=datasource_id,
            theme="dark",
            layout_config={"cols": 12, "row_height": 100, "gap": 12},
            auto_generated=True,
            status="draft",
        )
        await dashboard_repository.create(dashboard)

        saved_chart_ids = []
        saved_panels = []

        for i, cc in enumerate(chart_configs):
            chart_id = str(uuid.uuid4())
            chart_name = cc.get("chart_name", f"面板{i + 1}")
            chart_type = cc.get("chart_type", "bar")
            sql_text = cc.get("sql", "")
            echarts_option = cc.get("echarts_option", {})

            chart_entity = ChartConfig(
                id=chart_id,
                datasource_id=datasource_id,
                name=chart_name,
                chart_type=chart_type,
                sql_text=sql_text,
                echarts_option=echarts_option,
                auto_generated=True,
            )
            await chart_config_repository.create(chart_entity)
            saved_chart_ids.append(chart_id)

            panel = Panel(
                id=str(uuid.uuid4()),
                dashboard_id=dashboard_id,
                chart_config_id=chart_id,
                title=chart_name,
                layout_x=cc.get("layout_x", (i % 3) * 4),
                layout_y=cc.get("layout_y", (i // 3) * 4),
                layout_w=cc.get("layout_w", 4),
                layout_h=cc.get("layout_h", 4),
                sort_order=i,
            )
            await panel_repository.create(panel)
            saved_panels.append(panel)

        writer({"type": "progress", "step": "assemble_dashboard", "status": "success"})
        writer({
            "type": "dashboard_result",
            "dashboard_id": dashboard_id,
            "dashboard_name": dashboard_name,
            "panel_count": len(saved_panels),
            "chart_ids": saved_chart_ids,
        })

        return {"dashboard_id": dashboard_id}

    except Exception as e:
        logger.error(f"组装大屏失败: {str(e)}")
        writer({"type": "progress", "step": "assemble_dashboard", "status": "error"})
        raise e