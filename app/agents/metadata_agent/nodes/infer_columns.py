import json

from langgraph.runtime import Runtime

from app.agents.common_nodes.llm import llm
from app.agents.metadata_agent.context import MetaAgentContext
from app.agents.metadata_agent.state import MetaAgentState
from app.prompt.prompt_loader import load_prompt
from app.core.log import logger


async def infer_columns(state: MetaAgentState, runtime: Runtime[MetaAgentContext]) -> dict:
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "生成字段描述", "status": "running", "message": "AI 正在生成字段描述..."})

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

    batch_size = 20
    column_configs = []
    total_batches = (len(all_columns) + batch_size - 1) // batch_size

    for batch_idx in range(0, len(all_columns), batch_size):
        batch_num = batch_idx // batch_size + 1
        writer({"type": "progress", "step": "生成字段描述", "status": "running", "message": f"处理字段批次 {batch_num}/{total_batches}"})
        
        batch = all_columns[batch_idx:batch_idx + batch_size]
        columns_text = "\n\n".join([
            f"表: {c['table_name']}(角色: {c['table_role']})\n字段: {c['column_name']}(类型: {c['column_type']})\n示例值: {', '.join(c['examples'][:3]) if c['examples'] else '无'}"
            for c in batch
        ])

        messages = [
            ("system", prompt),
            ("human", f"请为以下字段生成描述、别名和角色:\n\n{columns_text}\n\n请返回 JSON 数组格式: [{{\"table_name\": \"表名\", \"name\": \"字段名\", \"role\": \"primary_key|foreign_key|measure|dimension\", \"description\": \"描述\", \"alias\": [\"别名1\", \"别名2\"], \"sync\": true|false}}]")
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
            logger.warning(f"infer_columns 批次 {batch_num} 失败: {str(e)}")
            for c in batch:
                column_configs.append({
                    "table_name": c["table_name"],
                    "name": c["column_name"],
                    "role": "dimension",
                    "description": f"{c['column_name']} 字段",
                    "alias": [],
                    "sync": False
                })

    writer({"type": "progress", "step": "生成字段描述", "status": "success", "message": f"生成 {len(column_configs)} 个字段的描述"})
    logger.info(f"infer_columns 完成: {len(column_configs)} 个字段")
    return {"column_configs": column_configs, "error": None}