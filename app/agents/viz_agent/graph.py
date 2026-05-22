from langgraph.graph import StateGraph, END

from app.agents.viz_agent.context import VizAgentContext
from app.agents.viz_agent.state import VizAgentState
from app.agents.viz_agent.nodes.recommend_chart import recommend_chart
from app.agents.viz_agent.nodes.run_chat_agent import run_chat_agent


def build_recommend_graph():
    graph = StateGraph(VizAgentState, context_schema=VizAgentContext)
    graph.add_node("recommend_chart", recommend_chart)
    graph.set_entry_point("recommend_chart")
    graph.add_edge("recommend_chart", END)
    return graph.compile()


def build_generate_graph():
    graph = StateGraph(VizAgentState, context_schema=VizAgentContext)
    graph.add_node("run_chat_agent", run_chat_agent)
    graph.add_node("recommend_chart", recommend_chart)
    graph.set_entry_point("run_chat_agent")
    graph.add_edge("run_chat_agent", "recommend_chart")
    graph.add_edge("recommend_chart", END)
    return graph.compile()


recommend_graph = build_recommend_graph()
generate_graph = build_generate_graph()