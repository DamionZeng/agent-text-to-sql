import json

from langgraph.runtime import Runtime

from app.agents.common_nodes.llm import llm
from app.agents.viz_agent.context import VizAgentContext
from app.agents.viz_agent.state import VizAgentState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt


async def parse_intent(state: VizAgentState, runtime: Runtime[VizAgentContext]):
    writer = runtime.stream_writer
    context = runtime.context

    try:
        writer({"type": "progress", "step": "parse_intent", "status": "running", "message": "正在解析大屏需求..."})

        query = state["query"]
        datasource_id = state["datasource_id"]

        meta_mysql_repository = context["meta_mysql_repository"]

        table_ids = await meta_mysql_repository.get_table_ids_by_datasource_id(datasource_id)
        metric_ids = await meta_mysql_repository.get_metric_ids_by_table_ids(table_ids)

        table_infos = []
        for table_id in table_ids:
            table_info = await meta_mysql_repository.get_table_info_by_id(table_id)
            if table_info:
                table_infos.append(table_info)

        metric_infos = []
        for metric_id in metric_ids:
            metric_info = await meta_mysql_repository.get_metric_by_id(metric_id)
            if metric_info:
                metric_infos.append(metric_info)

        tables_yaml = json.dumps([
            {
                "name": t.name,
                "role": t.role,
                "description": t.description,
            }
            for t in table_infos
        ], ensure_ascii=False, indent=2)

        metrics_yaml = json.dumps([
            {
                "name": m.name,
                "description": m.description,
                "relevant_columns": m.relevant_columns,
                "alias": m.alias,
            }
            for m in metric_infos
        ], ensure_ascii=False, indent=2)

        from app.clients.datasource import datasource_manager
        ds_config = datasource_manager.get_config(datasource_id) if datasource_manager.is_registered(datasource_id) else None
        db_info = json.dumps({
            "type": ds_config.db_type if ds_config else "mysql",
        }, ensure_ascii=False)

        prompt = load_prompt("parse_viz_intent")
        prompt = prompt.format(
            table_infos=tables_yaml,
            metric_infos=metrics_yaml,
            db_info=db_info,
            query=query,
        )

        response = await llm.ainvoke(prompt)
        content = response.content.strip()

        if content.startswith("```"):
            content = content.strip("`").strip()
            if content.startswith("json"):
                content = content[4:].strip()

        chart_configs = json.loads(content)
        if not isinstance(chart_configs, list):
            chart_configs = [chart_configs]

        for cc in chart_configs:
            if "description" not in cc:
                cc["description"] = cc.get("chart_name", "")

        writer({
            "type": "progress",
            "step": "parse_intent",
            "status": "success",
            "message": f"解析出 {len(chart_configs)} 个面板",
        })

        return {
            "chart_configs": chart_configs,
            "dashboard_name": query[:50],
        }

    except Exception as e:
        logger.error(f"解析大屏意图失败: {str(e)}")
        writer({"type": "progress", "step": "parse_intent", "status": "error", "message": str(e)})
        raise e