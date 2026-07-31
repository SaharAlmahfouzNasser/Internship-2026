import argparse
import sys
from pathlib import Path

from tumor_board import tumor_board_graph

DEFAULT_OUTPUT = Path("diagram.png")


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the tumor board LangGraph as an image.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output PNG path. Default: diagram.png",
    )
    parser.add_argument(
        "--mermaid",
        action="store_true",
        help="Print raw Mermaid source instead of rendering",
    )
    args = parser.parse_args()

    graph = tumor_board_graph.get_graph()
    if args.mermaid:
        print(graph.draw_mermaid())
        return

    if args.output.suffix.lower() != ".png":
        parser.error("only .png output is supported; use --mermaid for raw Mermaid source")

    graph.draw_mermaid_png(output_file_path=str(args.output))
    print(f"Wrote {args.output.resolve()}", file=sys.stderr)
