from __future__ import annotations

import argparse
import json
from pathlib import Path

from .comparison import compare_files, write_comparison


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare a candidate Agent run with a named baseline.")
    parser.add_argument("suite", type=Path)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--rubric", type=Path, help="Optional validated rubric JSON")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = compare_files(args.suite, args.baseline, args.candidate, args.rubric)
    if args.json_output or args.markdown_output:
        json_path = args.json_output or Path("reports/comparison_report.json")
        markdown_path = args.markdown_output or Path("reports/comparison_report.md")
        write_comparison(report, json_path, markdown_path)
        print(f"Comparison written to {json_path} and {markdown_path}")
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
