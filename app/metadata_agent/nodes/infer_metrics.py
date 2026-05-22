import json

from langgraph.runtime import Runtime

from app.agent.llm import llm
from app.metadata_agent.context import MetaAgentContext
from app.metadata_agent.state import MetaAgentState
from app.prompt.prompt_loader import load_prompt
from app.core.log import logger


async def infer_metrics(state: MetaAgentState, runtime: Runtime[MetaAgentContext]) -> dict:
    """AI 基于事实表和度量字段推断业务指标"""
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "推断业务指标", "status": "running", "message": "AI 正在推断业务指标..."})

    table_configs = state["table_configs"]
    column_configs = state["column_configs"]

    fact_tables = [t for t in table_configs if t.get("role") == "fact"]
    measure_columns = [c for c in column_configs if c.get("role") == "measure"]

    if not fact_tables or not measure_columns:
        writer({"type": "progress", "step": "推断业务指标", "status": "success", "message": "未发现事实表或度量字段，跳过指标推断"})
        return {"metric_configs": [], "error": None}

    prompt = load_prompt("infer_metrics")

    tables_text = "\n\n".join([
        f"事实表: {t['name']}\n描述: {t.get('description', '')}"
        for t in fact_tables
    ])

    columns_text = "\n".join([
        f"  - {c['table_name']}.{c['name']}: {c.get('description', '')}"
        for c in measure_columns
    ])

    messages = [
        ("system", prompt),
        ("human", f"基于以下事实表和度量字段，推断常见的业务指标:\n\n{tables_text}\n\n度量字段:\n{columns_text}\n\n请返回 JSON 数组格式: [{{\"name\": \"指标名\", \"description\": \"描述\", \"relevant_columns\": [\"表.字段\"], \"alias\": [\"别名1\"]}}]")
    ]

    try:
        response = await llm.ainvoke(messages)
        content = response.content

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        metric_configs = json.loads(content.strip())
        if not isinstance(metric_configs, list):
            metric_configs = []
        writer({"type": "progress", "step": "推断业务指标", "status": "success", "message": f"推断出 {len(metric_configs)} 个业务指标"})
        logger.info(f"infer_metrics 完成: {len(metric_configs)} 个指标")
        return {"metric_configs": metric_configs, "error": None}
    except Exception as e:
        logger.error(f"infer_metrics 失败: {str(e)}")
        writer({"type": "progress", "step": "推断业务指标", "status": "error", "message": str(e)})
        metric_configs = []
        for c in measure_columns[:3]:
            metric_configs.append({
                "name": f"{c['name']}_总和",
                "description": f"{c.get('description', c['name'])}的总和",
                "relevant_columns": [f"{c['table_name']}.{c['name']}"],
                "alias": [f"总{c['name']}"]
            })
        return {"metric_configs": metric_configs, "error": f"推断指标失败: {str(e)}"}
