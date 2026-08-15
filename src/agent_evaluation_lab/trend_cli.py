from __future__ import annotations

import argparse
import json
from pathlib import Path

from .trend import analyze_files, write_trend


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze ordered Agent runs without statistical claims.")
    parser.add_argument("suite", type=Path)
    parser.add_argument("runs", type=Path, nargs="+")
    parser.add_argument("--rubric", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args()
    report = analyze_files(args.suite, args.runs, args.rubric)
    if args.json_output or args.markdown_output:
        json_path = args.json_output or Path("reports/trend_report.json")
        markdown_path = args.markdown_output or Path("reports/trend_report.md")
        write_trend(report, json_path, markdown_path)
        print(f"Trend written to {json_path} and {markdown_path}")
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
