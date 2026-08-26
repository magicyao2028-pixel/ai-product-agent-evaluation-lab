from __future__ import annotations

import argparse
import json
from pathlib import Path

from .review_history import validate_review_history


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate an append-only review-history fixture")
    parser.add_argument("path", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = validate_review_history(json.loads(args.path.read_text(encoding="utf-8")))
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
