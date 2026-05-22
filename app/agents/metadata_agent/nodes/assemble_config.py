from langgraph.runtime import Runtime

from app.agents.metadata_agent.context import MetaAgentContext
from app.agents.metadata_agent.state import MetaAgentState
from app.core.log import logger


async def assemble_config(state: MetaAgentState, runtime: Runtime[MetaAgentContext]) -> dict:
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "组装元数据配置", "status": "running", "message": "组装元数据配置..."})

    table_configs = state["table_configs"]
    column_configs = state["column_configs"]
    metric_configs = state["metric_configs"]

    tables = []
    for tc in table_configs:
        table_name = tc["name"]
        cols = [c for c in column_configs if c.get("table_name") == table_name]
        tables.append({
            "name": table_name,
            "role": tc.get("role", "dim"),
            "description": tc.get("description", ""),
            "columns": [
                {
                    "name": c["name"],
                    "type": c.get("type", "varchar"),
                    "role": c.get("role", "dimension"),
                    "description": c.get("description", ""),
                    "alias": c.get("alias", []),
                    "sync": c.get("sync", False)
                }
                for c in cols
            ]
        })

    metrics = [
        {
            "name": m["name"],
            "description": m.get("description", ""),
            "relevant_columns": m.get("relevant_columns", []),
            "alias": m.get("alias", [])
        }
        for m in metric_configs
    ]

    meta_config = {
        "tables": tables,
        "metrics": metrics
    }

    total_columns = sum(len(t["columns"]) for t in tables)
    writer({"type": "progress", "step": "组装元数据配置", "status": "success", "message": f"组装完成: {len(tables)} 表, {total_columns} 字段, {len(metrics)} 指标"})
    logger.info(f"assemble_config 完成: {len(tables)} 表, {total_columns} 字段, {len(metrics)} 指标")
    return {"meta_config": meta_config, "error": None}