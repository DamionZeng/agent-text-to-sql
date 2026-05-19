from langgraph.constants import START, END
from langgraph.graph import StateGraph

from app.metadata_agent.context import MetaAgentContext
from app.metadata_agent.state import MetaAgentState
from app.metadata_agent.nodes import (
    analyze_schema, classify_tables, infer_tables,
    infer_columns, infer_metrics, assemble_config,
    validate_config, build_knowledge
)

graph_builder = StateGraph(state_schema=MetaAgentState, context_schema=MetaAgentContext)

graph_builder.add_node("analyze_schema", analyze_schema)
graph_builder.add_node("classify_tables", classify_tables)
graph_builder.add_node("infer_tables", infer_tables)
graph_builder.add_node("infer_columns", infer_columns)
graph_builder.add_node("infer_metrics", infer_metrics)
graph_builder.add_node("assemble_config", assemble_config)
graph_builder.add_node("validate_config", validate_config)
graph_builder.add_node("build_knowledge", build_knowledge)

graph_builder.add_edge(START, "analyze_schema")
graph_builder.add_edge("analyze_schema", "classify_tables")
graph_builder.add_edge("classify_tables", "infer_tables")
graph_builder.add_edge("infer_tables", "infer_columns")
graph_builder.add_edge("infer_columns", "infer_metrics")
graph_builder.add_edge("infer_metrics", "assemble_config")
graph_builder.add_edge("assemble_config", "validate_config")


def validate_router(state: MetaAgentState):
    if state.get("error"):
        return END
    if state.get("retry_count", 0) >= 3:
        return END
    validation_result = state.get("validation_result", {})
    if validation_result.get("valid"):
        return "build_knowledge"
    return "infer_tables"


graph_builder.add_conditional_edges(
    "validate_config",
    validate_router,
    {"build_knowledge": "build_knowledge", "infer_tables": "infer_tables", END: END}
)

graph_builder.add_edge("build_knowledge", END)

meta_agent = graph_builder.compile()
