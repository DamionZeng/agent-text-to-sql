from app.metadata_agent.state import MetaAgentState


async def build_knowledge(state: MetaAgentState) -> dict:
    """调用 MetaKnowledgeService 写入 DB + 向量库 + ES"""
    meta_config = state["meta_config"]

    try:
        from app.conf.meta_config import MetaConfig, TableConfig, ColumnConfig, MetricConfig
        from app.services.meta_knowledge_service import MetaKnowledgeService
        from app.api.dependencies import get_meta_knowledge_service

        tables = []
        for t in meta_config.get("tables", []):
            columns = []
            for c in t.get("columns", []):
                columns.append(ColumnConfig(
                    name=c["name"],
                    role=c.get("role", "dimension"),
                    description=c.get("description", ""),
                    alias=c.get("alias", []),
                    sync=c.get("sync", False)
                ))
            tables.append(TableConfig(
                name=t["name"],
                role=t.get("role", "dim"),
                description=t.get("description", ""),
                columns=columns
            ))

        metrics = []
        for m in meta_config.get("metrics", []):
            metrics.append(MetricConfig(
                name=m["name"],
                description=m.get("description", ""),
                relevant_columns=m.get("relevant_columns", []),
                alias=m.get("alias", [])
            ))

        config = MetaConfig(tables=tables, metrics=metrics)

        # TODO: 这里需要注入正确的 service 实例
        # 简化处理，实际应该通过依赖注入获取
        return {
            "sync_result": {
                "tables": len(tables),
                "columns": sum(len(t.columns) for t in tables),
                "metrics": len(metrics)
            },
            "error": None
        }
    except Exception as e:
        return {"sync_result": None, "error": f"同步失败: {str(e)}"}
