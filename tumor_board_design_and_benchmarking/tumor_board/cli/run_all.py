"""Run all three presentation cases sequentially and log results."""

import argparse
import sys

from tumor_board.cli.run import run_case

CASES = [
    "cases/nsclc_egfr_l858r_advanced/case.json",
    "cases/breast_her2_equivocal_then_fish_positive/case.json",
    "cases/synchronous_sclc_nsclc/case.json",
]


def main() -> None:
    argparse.ArgumentParser(description="Run all presentation cases sequentially.").parse_args()
    for case in CASES:
        print(f"\n{'=' * 60}", flush=True)
        print(f"STARTING: {case}", flush=True)
        print(f"{'=' * 60}", flush=True)
        try:
            run_case(case)
            print(f"\nCOMPLETED: {case} (exit 0)", flush=True)
        except Exception as exc:
            print(f"\nFAILED: {case} ({exc})", file=sys.stderr, flush=True)

    print("\nALL CASES DONE", flush=True)
