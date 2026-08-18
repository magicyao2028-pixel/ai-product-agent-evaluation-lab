from __future__ import annotations

import argparse
from pathlib import Path

from .reviews import analyze_review_files, write_review_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze human-review annotations without overwriting evaluation evidence.")
    parser.add_argument("evaluation", type=Path)
    parser.add_argument("annotations", type=Path)
    parser.add_argument("--json-output", type=Path, default=Path("reports/review_report.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("reports/review_report.md"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = analyze_review_files(args.evaluation, args.annotations)
    write_review_report(report, args.json_output, args.markdown_output)
    print(
        f"Review analysis: {report['summary']['release_status']}; "
        f"{report['summary']['disagreements']} disagreement(s)"
    )


if __name__ == "__main__":
    main()
