from app.metadata_agent.state import MetaAgentState


async def assemble_config(state: MetaAgentState) -> dict:
    """组装成完整的 MetaConfig"""
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

    return {"meta_config": meta_config, "error": None}
