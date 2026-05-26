from langgraph.constants import START, END
from langgraph.graph import StateGraph

from app.agents.chat_agent.nodes.add_extra_context import add_extra_context
from app.agents.chat_agent.nodes.correct_sql import correct_sql
from app.agents.chat_agent.nodes.extract_keywords import extract_keywords
from app.agents.chat_agent.nodes.filter_metric import filter_metric
from app.agents.chat_agent.nodes.filter_table import filter_table
from app.agents.chat_agent.nodes.generate_sql import generate_sql
from app.agents.chat_agent.nodes.merge_retrieved_info import merge_retrieved_info
from app.agents.chat_agent.nodes.recall_column import recall_column
from app.agents.chat_agent.nodes.recall_metric import recall_metric
from app.agents.chat_agent.nodes.recall_value import recall_value
from app.agents.chat_agent.nodes.validate_sql import validate_sql
from app.agents.common_nodes.run_sql import run_sql
from app.agents.viz_agent.context import VizAgentContext
from app.agents.viz_agent.state import VizAgentState
from app.agents.viz_agent.nodes.recommend_chart import recommend_chart
from app.agents.viz_agent.nodes.parse_intent import parse_intent
from app.agents.viz_agent.nodes.plan_layout import plan_layout
from app.agents.viz_agent.nodes.generate_sqls_via_chat_agent import generate_sqls_via_chat_agent
from app.agents.viz_agent.nodes.generate_charts import generate_charts
from app.agents.viz_agent.nodes.assemble_dashboard import assemble_dashboard


def build_recommend_graph():
    graph = StateGraph(VizAgentState, context_schema=VizAgentContext)
    graph.add_node("recommend_chart", recommend_chart)
    graph.set_entry_point("recommend_chart")
    graph.add_edge("recommend_chart", END)
    return graph.compile()


def build_generate_graph():
    graph = StateGraph(VizAgentState, context_schema=VizAgentContext)

    graph.add_node("extract_keywords", extract_keywords)
    graph.add_node("recall_column", recall_column)
    graph.add_node("recall_value", recall_value)
    graph.add_node("recall_metric", recall_metric)
    graph.add_node("merge_retrieved_info", merge_retrieved_info)
    graph.add_node("filter_metric", filter_metric)
    graph.add_node("filter_table", filter_table)
    graph.add_node("add_extra_context", add_extra_context)
    graph.add_node("generate_sql", generate_sql)
    graph.add_node("validate_sql", validate_sql)
    graph.add_node("correct_sql", correct_sql)
    graph.add_node("run_sql", run_sql)
    graph.add_node("recommend_chart", recommend_chart)

    graph.add_edge(START, "extract_keywords")
    graph.add_edge("extract_keywords", "recall_column")
    graph.add_edge("extract_keywords", "recall_value")
    graph.add_edge("extract_keywords", "recall_metric")
    graph.add_edge("recall_column", "merge_retrieved_info")
    graph.add_edge("recall_value", "merge_retrieved_info")
    graph.add_edge("recall_metric", "merge_retrieved_info")
    graph.add_edge("merge_retrieved_info", "filter_table")
    graph.add_edge("merge_retrieved_info", "filter_metric")
    graph.add_edge("filter_table", "add_extra_context")
    graph.add_edge("filter_metric", "add_extra_context")
    graph.add_edge("add_extra_context", "generate_sql")
    graph.add_edge("generate_sql", "validate_sql")

    def should_continue(state: VizAgentState):
        if state.get("error") is None:
            return "run_sql"
        if state.get("retry_count", 0) < 3:
            return "correct_sql"
        return "run_sql"

    graph.add_conditional_edges(
        source="validate_sql",
        path=should_continue,
        path_map={"run_sql": "run_sql", "correct_sql": "correct_sql"},
    )
    graph.add_edge("correct_sql", "validate_sql")
    graph.add_edge("run_sql", "recommend_chart")
    graph.add_edge("recommend_chart", END)

    return graph.compile()


recommend_graph = build_recommend_graph()
generate_graph = build_generate_graph()


def build_dashboard_graph():
    graph = StateGraph(VizAgentState, context_schema=VizAgentContext)

    graph.add_node("parse_intent", parse_intent)
    graph.add_node("generate_sqls_via_chat_agent", generate_sqls_via_chat_agent)
    graph.add_node("generate_charts", generate_charts)
    graph.add_node("plan_layout", plan_layout)
    graph.add_node("assemble_dashboard", assemble_dashboard)

    graph.add_edge(START, "parse_intent")
    graph.add_edge("parse_intent", "generate_sqls_via_chat_agent")
    graph.add_edge("generate_sqls_via_chat_agent", "generate_charts")
    graph.add_edge("generate_charts", "plan_layout")
    graph.add_edge("plan_layout", "assemble_dashboard")
    graph.add_edge("assemble_dashboard", END)

    return graph.compile()


dashboard_graph = build_dashboard_graph()