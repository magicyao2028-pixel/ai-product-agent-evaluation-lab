"""Deterministic release-gate evaluation for AI products and Agents."""

from .comparison import compare_files, compare_runs, write_comparison
from .evaluator import evaluate_files, evaluate_run, write_report
from .rubric import RubricConfig, default_rubric, load_rubric

__all__ = [
    "compare_files",
    "compare_runs",
    "evaluate_files",
    "evaluate_run",
    "RubricConfig",
    "default_rubric",
    "load_rubric",
    "write_comparison",
    "write_report",
]
__version__ = "0.3.0"
