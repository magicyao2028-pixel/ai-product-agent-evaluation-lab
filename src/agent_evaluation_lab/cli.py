from __future__ import annotations

import argparse
import json
from pathlib import Path

from .evaluator import evaluate_files, write_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate an AI product or Agent run against deterministic contracts.")
    parser.add_argument("suite", type=Path, help="Evaluation-suite JSON")
    parser.add_argument("candidate", type=Path, help="Candidate-run JSON")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--rubric", type=Path, help="Optional validated rubric JSON")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = evaluate_files(args.suite, args.candidate, args.rubric)
    if args.json_output or args.markdown_output:
        json_path = args.json_output or Path("reports/evaluation_report.json")
        markdown_path = args.markdown_output or Path("reports/evaluation_report.md")
        write_report(report, json_path, markdown_path)
        print(f"Report written to {json_path} and {markdown_path}")
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
