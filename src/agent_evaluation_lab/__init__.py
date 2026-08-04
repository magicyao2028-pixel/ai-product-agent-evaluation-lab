"""Deterministic release-gate evaluation for AI products and Agents."""

from .evaluator import evaluate_files, evaluate_run, write_report

__all__ = ["evaluate_files", "evaluate_run", "write_report"]
__version__ = "0.1.0"
