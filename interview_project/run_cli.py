import argparse
import json
from pathlib import Path

from agents import run_tumor_board
from cases import CASES, get_case


def main():
    parser = argparse.ArgumentParser(description="Run the tumor-board multi-agent simulation.")
    parser.add_argument("--case", default=CASES[0].case_id, choices=[c.case_id for c in CASES])
    parser.add_argument("--max-iterations", type=int, default=5)
    parser.add_argument("--no-evaluator", action="store_true")
    parser.add_argument("--out", default="outputs/transcript.json")
    args = parser.parse_args()

    case = get_case(args.case)
    result = run_tumor_board(
        case,
        max_iterations=args.max_iterations,
        use_evaluator=not args.no_evaluator,
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Saved transcript to {out_path}")
    print("\nFINAL SUMMARY\n")
    print(result.final_summary)


if __name__ == "__main__":
    main()
