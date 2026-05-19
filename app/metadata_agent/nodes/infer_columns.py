import json

from app.agent.llm import llm
from app.metadata_agent.state import MetaAgentState
from app.prompt.prompt_loader import load_prompt


async def infer_columns(state: MetaAgentState) -> dict:
    """AI 为每个字段生成描述、别名、角色"""
    raw_schema = state["raw_schema"]
    table_configs = state["table_configs"]

    prompt = load_prompt("infer_columns")

    all_columns = []
    for table in raw_schema:
        table_role = next((t["role"] for t in table_configs if t["name"] == table["name"]), "dim")
        for col in table["columns"]:
            all_columns.append({
                "table_name": table["name"],
                "table_role": table_role,
                "column_name": col["name"],
                "column_type": col["type"],
                "examples": col["examples"]
            })

    # 分批处理，每批 20 个字段
    batch_size = 20
    column_configs = []

    for i in range(0, len(all_columns), batch_size):
        batch = all_columns[i:i + batch_size]
        columns_text = "\n\n".join([
            f"表: {c['table_name']}(角色: {c['table_role']})\n字段: {c['column_name']}(类型: {c['column_type']})\n示例值: {', '.join(c['examples'][:3]) if c['examples'] else '无'}"
            for c in batch
        ])

        messages = [
            ("system", prompt),
            ("human", f"请为以下字段生成描述、别名和角色:\n\n{columns_text}\n\n请返回 JSON 数组格式: [{\"table_name\": \"表名\", \"name\": \"字段名\", \"role\": \"primary_key|foreign_key|measure|dimension\", \"description\": \"描述\", \"alias\": [\"别名1\", \"别名2\"], \"sync\": true|false}]")
        ]

        try:
            response = await llm.ainvoke(messages)
            content = response.content

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            batch_configs = json.loads(content.strip())
            if isinstance(batch_configs, list):
                column_configs.extend(batch_configs)
        except Exception as e:
            # 降级处理
            for c in batch:
                column_configs.append({
                    "table_name": c["table_name"],
                    "name": c["column_name"],
                    "role": "dimension",
                    "description": f"{c['column_name']} 字段",
                    "alias": [],
                    "sync": False
                })

    return {"column_configs": column_configs, "error": None}
