import json

from langgraph.runtime import Runtime

from app.agent.llm import llm
from app.metadata_agent.context import MetaAgentContext
from app.metadata_agent.state import MetaAgentState
from app.prompt.prompt_loader import load_prompt
from app.core.log import logger


async def classify_tables(state: MetaAgentState, runtime: Runtime[MetaAgentContext]) -> dict:
    """AI 分析表结构，识别维度表/事实表"""
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "classify_tables", "status": "running", "message": "AI 正在分析表类型..."})

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

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        classifications = json.loads(content.strip())
        
        dim_count = sum(1 for v in classifications.values() if v == "dim")
        fact_count = sum(1 for v in classifications.values() if v == "fact")
        writer({"type": "progress", "step": "classify_tables", "status": "success", "message": f"识别到 {dim_count} 张维度表，{fact_count} 张事实表"})
        logger.info(f"classify_tables 完成: {classifications}")
        return {"table_classifications": classifications, "error": None}
    except Exception as e:
        logger.error(f"classify_tables 失败: {str(e)}")
        writer({"type": "progress", "step": "classify_tables", "status": "error", "message": str(e)})
        return {
            "table_classifications": {t["name"]: "unknown" for t in raw_schema},
            "error": f"分类失败: {str(e)}"
        }
