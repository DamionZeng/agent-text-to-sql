from langgraph.runtime import Runtime

from app.metadata_agent.context import MetaAgentContext
from app.metadata_agent.state import MetaAgentState
from app.core.log import logger


async def validate_config(state: MetaAgentState, runtime: Runtime[MetaAgentContext]) -> dict:
    """校验配置完整性"""
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "validate_config", "status": "running", "message": "校验配置完整性..."})

    meta_config = state["meta_config"]
    errors = []

    if not meta_config or not meta_config.get("tables"):
        errors.append("配置缺少表信息")
        writer({"type": "progress", "step": "validate_config", "status": "error", "message": "配置缺少表信息"})
        return {
            "validation_result": {"valid": False, "errors": errors},
            "error": "配置不完整"
        }

    tables = meta_config["tables"]
    all_column_ids = set()

    for table in tables:
        if not table.get("description"):
            errors.append(f"表 {table['name']} 缺少描述")
        if not table.get("role"):
            errors.append(f"表 {table['name']} 缺少角色")

        has_measure = False
        for col in table.get("columns", []):
            all_column_ids.add(f"{table['name']}.{col['name']}")
            if not col.get("description"):
                errors.append(f"字段 {table['name']}.{col['name']} 缺少描述")
            if not col.get("role"):
                errors.append(f"字段 {table['name']}.{col['name']} 缺少角色")
            if col.get("role") == "measure":
                has_measure = True

        if table.get("role") == "fact" and not has_measure:
            errors.append(f"事实表 {table['name']} 缺少度量字段")

    for metric in meta_config.get("metrics", []):
        for col_id in metric.get("relevant_columns", []):
            if col_id not in all_column_ids:
                errors.append(f"指标 {metric['name']} 关联的字段 {col_id} 不存在")

    valid = len(errors) == 0
    if valid:
        writer({"type": "progress", "step": "validate_config", "status": "success", "message": "配置校验通过"})
        logger.info("validate_config 完成: 配置校验通过")
    else:
        writer({"type": "progress", "step": "validate_config", "status": "error", "message": f"发现 {len(errors)} 个问题"})
        logger.warning(f"validate_config 完成: 发现 {len(errors)} 个问题: {errors}")
    
    return {
        "validation_result": {"valid": valid, "errors": errors},
        "error": None if valid else "; ".join(errors[:3])
    }
