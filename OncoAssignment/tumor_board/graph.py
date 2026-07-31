from langgraph.graph import END, START, StateGraph

from tumor_board.nodes import (
    consistency_check_node,
    final_summary_node,
    oncologist_independent_assessment_node,
    oncologist_response_node,
    oncologist_revision_node,
    pathologist_final_contribution_node,
    pathologist_independent_assessment_node,
    pathologist_opening_node,
    pathologist_reply_node,
)
from tumor_board.state import TumorBoardState

_builder = StateGraph(TumorBoardState)

_builder.add_node("pathologist_independent_assessment", pathologist_independent_assessment_node)
_builder.add_node("oncologist_independent_assessment",  oncologist_independent_assessment_node)
_builder.add_node("pathologist_opening",                pathologist_opening_node)
_builder.add_node("oncologist_response",                oncologist_response_node)
_builder.add_node("pathologist_reply",                  pathologist_reply_node)
# Round 4 + Round 5 run in parallel: neither sees the other's final summary.
_builder.add_node("oncologist_revision",                oncologist_revision_node)
_builder.add_node("pathologist_final_contribution",     pathologist_final_contribution_node)
_builder.add_node("consistency_check",                  consistency_check_node)
_builder.add_node("final_summary",                      final_summary_node)

# Parallel independent assessments from START
_builder.add_edge(START, "pathologist_independent_assessment")
_builder.add_edge(START, "oncologist_independent_assessment")

# Join independent assessments → begin discussion
_builder.add_edge(
    ["pathologist_independent_assessment", "oncologist_independent_assessment"],
    "pathologist_opening",
)

# Sequential discussion rounds 1-3
_builder.add_edge("pathologist_opening", "oncologist_response")
_builder.add_edge("oncologist_response", "pathologist_reply")

# Fan-out: both write their summary contributions independently
_builder.add_edge("pathologist_reply", "oncologist_revision")
_builder.add_edge("pathologist_reply", "pathologist_final_contribution")

# Join both contributions → board chair consistency check
_builder.add_edge(
    ["oncologist_revision", "pathologist_final_contribution"],
    "consistency_check",
)

_builder.add_edge("consistency_check", "final_summary")
_builder.add_edge("final_summary", END)

tumor_board_graph = _builder.compile()
