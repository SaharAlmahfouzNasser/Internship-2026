from typing import Any, TypedDict


class TumorBoardState(TypedDict):
    case_id: str
    case_packet: str
    oncologist_images: list[dict[str, Any]]  # base64 image blocks, oncologist-only
    pathologist_independent_assessment: str
    oncologist_independent_assessment: str
    pathologist_opening: str
    oncologist_response: str
    pathologist_reply: str
    oncologist_revision: str
    pathologist_final_contribution: str
    consistency_check: str
    final_summary: str
