from langgraph.constants import START, END
from langgraph.graph import StateGraph

from app.agents.metadata_agent.context import MetaAgentContext
from app.agents.metadata_agent.state import MetaAgentState
from app.agents.metadata_agent.nodes import (
    analyze_schema, classify_tables, infer_tables,
    infer_columns, infer_metrics, assemble_config,
    validate_config, build_knowledge
)

draft_graph_builder = StateGraph(state_schema=MetaAgentState, context_schema=MetaAgentContext)

draft_graph_builder.add_node("analyze_schema", analyze_schema)
draft_graph_builder.add_node("classify_tables", classify_tables)
draft_graph_builder.add_node("infer_tables", infer_tables)
draft_graph_builder.add_node("infer_columns", infer_columns)
draft_graph_builder.add_node("infer_metrics", infer_metrics)
draft_graph_builder.add_node("assemble_config", assemble_config)
draft_graph_builder.add_node("validate_config", validate_config)

draft_graph_builder.add_edge(START, "analyze_schema")
draft_graph_builder.add_edge("analyze_schema", "classify_tables")
draft_graph_builder.add_edge("classify_tables", "infer_tables")
draft_graph_builder.add_edge("infer_tables", "infer_columns")
draft_graph_builder.add_edge("infer_columns", "infer_metrics")
draft_graph_builder.add_edge("infer_metrics", "assemble_config")
draft_graph_builder.add_edge("assemble_config", "validate_config")


def draft_validate_router(state: MetaAgentState):
    if state.get("error"):
        return END
    if state.get("retry_count", 0) >= 3:
        return END
    validation_result = state.get("validation_result", {})
    if validation_result.get("valid"):
        return END
    return "infer_tables"


draft_graph_builder.add_conditional_edges(
    "validate_config",
    draft_validate_router,
    {"infer_tables": "infer_tables", END: END}
)

meta_agent_draft = draft_graph_builder.compile()

publish_graph_builder = StateGraph(state_schema=MetaAgentState, context_schema=MetaAgentContext)

publish_graph_builder.add_node("build_knowledge", build_knowledge)

publish_graph_builder.add_edge(START, "build_knowledge")
publish_graph_builder.add_edge("build_knowledge", END)

meta_agent_publish = publish_graph_builder.compile()