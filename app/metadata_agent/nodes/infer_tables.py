import json

from langgraph.runtime import Runtime

from app.agent.llm import llm
from app.metadata_agent.context import MetaAgentContext
from app.metadata_agent.state import MetaAgentState
from app.prompt.prompt_loader import load_prompt
from app.core.log import logger


async def infer_tables(state: MetaAgentState, runtime: Runtime[MetaAgentContext]) -> dict:
    """AI 为每个表生成描述和确认角色"""
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "infer_tables", "status": "running", "message": "AI 正在生成表描述..."})

    raw_schema = state["raw_schema"]
    classifications = state["table_classifications"]

    prompt = load_prompt("infer_tables")

    tables_text = "\n\n".join([
        f"表名: {t['name']}\n分类: {classifications.get(t['name'], 'unknown')}\n字段: {', '.join([c['name'] for c in t['columns']])}"
        for t in raw_schema
    ])

    messages = [
        ("system", prompt),
        ("human", f"请为以下表生成中文描述并确认角色:\n\n{tables_text}\n\n请返回 JSON 数组格式: [{{\"name\": \"表名\", \"role\": \"dim|fact\", \"description\": \"描述\"}}]")
    ]

    try:
        response = await llm.ainvoke(messages)
        content = response.content

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        table_configs = json.loads(content.strip())
        writer({"type": "progress", "step": "infer_tables", "status": "success", "message": f"生成 {len(table_configs)} 张表的描述"})
        logger.info(f"infer_tables 完成: {len(table_configs)} 张表")
        return {"table_configs": table_configs, "error": None, "retry_count": state.get("retry_count", 0) + 1}
    except Exception as e:
        logger.error(f"infer_tables 失败: {str(e)}")
        writer({"type": "progress", "step": "infer_tables", "status": "error", "message": str(e)})
        return {
            "table_configs": [
                {"name": t["name"], "role": classifications.get(t["name"], "dim"), "description": f"{t['name']} 表"}
                for t in raw_schema
            ],
            "error": f"推断表信息失败: {str(e)}",
            "retry_count": state.get("retry_count", 0) + 1
        }
