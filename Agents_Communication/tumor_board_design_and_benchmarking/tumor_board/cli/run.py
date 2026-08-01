import argparse
import sys
from pathlib import Path

import tumor_board.logger as logger
from tumor_board import tumor_board_graph
from tumor_board.loader import format_case_packet, load_case, load_oncologist_images

DEFAULT_CASE_PATH = "cases/breast_her2_equivocal_then_fish_positive/case.json"


def print_section(title: str, value: str) -> None:
    print(f"\n=== {title} ===\n")
    print(value)


def run_case(case_path: str, log_dir: str = "logs") -> dict:
    case = load_case(case_path)
    case_dir = Path(case_path).parent
    oncologist_images = load_oncologist_images(case, case_dir)

    log_path = logger.init(case["id"], log_dir=log_dir)
    print(f"[setup] logging to {log_path}", file=sys.stderr, flush=True)
    if oncologist_images:
        print(f"[setup] loaded {len(oncologist_images)} oncologist image(s)", file=sys.stderr)

    result = tumor_board_graph.invoke(
        {
            "case_id": case["id"],
            "case_packet": format_case_packet(case),
            "oncologist_images": oncologist_images,
            "pathologist_independent_assessment": "",
            "oncologist_independent_assessment": "",
            "pathologist_opening": "",
            "oncologist_response": "",
            "pathologist_reply": "",
            "oncologist_revision": "",
            "pathologist_final_contribution": "",
            "consistency_check": "",
            "final_summary": "",
        }
    )

    logger.finalize()

    print_section("CASE", result["case_packet"])
    print_section("PATHOLOGIST INDEPENDENT ASSESSMENT", result["pathologist_independent_assessment"])
    print_section("ONCOLOGIST INDEPENDENT ASSESSMENT", result["oncologist_independent_assessment"])
    print_section("ROUND 1 - PATHOLOGIST OPENS", result["pathologist_opening"])
    print_section("ROUND 2 - ONCOLOGIST RESPONDS", result["oncologist_response"])
    print_section("ROUND 3 - PATHOLOGIST REPLIES", result["pathologist_reply"])
    print_section("ONCOLOGIST SUMMARY CONTRIBUTION", result["oncologist_revision"])
    print_section("PATHOLOGIST SUMMARY CONTRIBUTION", result["pathologist_final_contribution"])
    print_section("BOARD CHAIR CONSISTENCY CHECK", result["consistency_check"])
    print_section("FINAL SUMMARY", result["final_summary"])
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the tumor board multi-agent graph.")
    parser.add_argument("--case", default=DEFAULT_CASE_PATH, help="Path to case.json")
    parser.add_argument("--log-dir", default="logs", help="Directory for log files")
    args = parser.parse_args()
    run_case(args.case, log_dir=args.log_dir)
