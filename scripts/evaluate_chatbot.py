#!/usr/bin/env python3
"""
Script to evaluate chatbot accuracy, retrieval relevance, memory context, and guardrails.
Generates reports/chatbot_evaluation.json and reports/chatbot_evaluation_summary.md.
Usage:
    python scripts/evaluate_chatbot.py
"""

import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.services.evaluation_service import EvaluationService

def main():
    print("=" * 65)
    print("Starting Automated Chatbot Benchmark Evaluation")
    print("=" * 65)

    evaluator = EvaluationService()
    summary = evaluator.run_evaluation()

    print("\nEvaluation Completed!")
    print(f"Total Questions Evaluated: {summary['total_questions_evaluated']}")
    print(f"Passed: {summary['passed_tests']}")
    print(f"Failed: {summary['failed_tests']}")
    print(f"Overall Accuracy: {summary['overall_accuracy_percentage']}%")
    print("\nCategory Breakdown:")
    for cat, stats in summary["category_breakdown"].items():
        rate = round((stats["passed"] / stats["total"]) * 100, 1)
        print(f" - {cat:25}: {stats['passed']}/{stats['total']} ({rate}%)")

    reports_dir = BASE_DIR / "reports"
    print(f"\nDetailed reports saved to:")
    print(f" - JSON: {reports_dir / 'chatbot_evaluation.json'}")
    print(f" - Markdown: {reports_dir / 'chatbot_evaluation_summary.md'}")

if __name__ == "__main__":
    main()
