import base64
import json
from pathlib import Path
from typing import Any


def load_case(path: str) -> dict[str, Any]:
    with Path(path).open() as f:
        return json.load(f)


def load_oncologist_images(case: dict[str, Any], case_dir: Path) -> list[dict[str, Any]]:
    blocks = []
    for img in case.get("images", []):
        if img.get("viewer") != "oncologist":
            continue
        img_path = case_dir / img["file"]
        with img_path.open("rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        suffix = img_path.suffix.lower().lstrip(".")
        mime = "image/jpeg" if suffix in ("jpg", "jpeg") else f"image/{suffix}"
        blocks.append(
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}
        )
    return blocks


def format_case_packet(case: dict[str, Any]) -> str:
    packet = case["case_packet"]
    return (
        f"Case ID: {case['id']}\n\n"
        f"Clinical summary:\n{packet['clinical_summary']}\n\n"
        f"Imaging findings:\n{packet['imaging_findings']}\n\n"
        f"Pathology report:\n{packet['pathology_report']}"
    )
