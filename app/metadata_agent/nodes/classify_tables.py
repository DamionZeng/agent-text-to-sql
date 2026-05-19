import json

from app.agent.llm import llm
from app.metadata_agent.state import MetaAgentState
from app.prompt.prompt_loader import load_prompt


async def classify_tables(state: MetaAgentState) -> dict:
    """AI 分析表结构，识别维度表/事实表"""
    raw_schema = state["raw_schema"]

    prompt = load_prompt("classify_tables")

    schema_text = "\n".join([
        f"表名: {t['name']}\n字段: {', '.join([c['name'] + '(' + c['type'] + ')' for c in t['columns']])}"
        for t in raw_schema
    ])

    messages = [
        ("system", prompt),
        ("human", f"请分析以下数据库表结构，判断每个表是维度表(dim)还是事实表(fact):\n\n{schema_text}\n\n请返回 JSON 格式: {{\"table_name\": \"dim\"|\"fact\"}}")
    ]

    try:
        response = await llm.ainvoke(messages)
        content = response.content

        # 提取 JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        classifications = json.loads(content.strip())
        return {"table_classifications": classifications, "error": None}
    except Exception as e:
        # 如果 AI 失败，默认全部为 unknown
        return {
            "table_classifications": {t["name"]: "unknown" for t in raw_schema},
            "error": f"分类失败: {str(e)}"
        }
