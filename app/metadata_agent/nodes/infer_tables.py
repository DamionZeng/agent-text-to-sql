import json

from app.agent.llm import llm
from app.metadata_agent.state import MetaAgentState
from app.prompt.prompt_loader import load_prompt


async def infer_tables(state: MetaAgentState) -> dict:
    """AI 为每个表生成描述和确认角色"""
    raw_schema = state["raw_schema"]
    classifications = state["table_classifications"]

    prompt = load_prompt("infer_tables")

    tables_text = "\n\n".join([
        f"表名: {t['name']}\n分类: {classifications.get(t['name'], 'unknown')}\n字段: {', '.join([c['name'] for c in t['columns']])}"
        for t in raw_schema
    ])

    messages = [
        ("system", prompt),
        ("human", f"请为以下表生成中文描述并确认角色:\n\n{tables_text}\n\n请返回 JSON 数组格式: [{\"name\": \"表名\", \"role\": \"dim|fact\", \"description\": \"描述\"}]")
    ]

    try:
        response = await llm.ainvoke(messages)
        content = response.content

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        table_configs = json.loads(content.strip())
        return {"table_configs": table_configs, "error": None}
    except Exception as e:
        # 降级处理：使用默认描述
        return {
            "table_configs": [
                {"name": t["name"], "role": classifications.get(t["name"], "dim"), "description": f"{t['name']} 表"}
                for t in raw_schema
            ],
            "error": f"推断表信息失败: {str(e)}"
        }
