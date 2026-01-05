#!/usr/bin/env python3
"""
Live benchmark dashboard - monitors benchmark progress and displays results.
Run: uv run python tests/benchmark_dashboard.py
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

RESULTS_DIR = Path("/tmp/framework_benchmarks")
LOG_FILE = Path("/tmp/benchmark_all.log")
GROUND_TRUTH = 12542.46

CLEAR = "\033[2J\033[H"
BOLD = "\033[1m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"


def load_results() -> dict[str, dict]:
    results = {}
    if not RESULTS_DIR.exists():
        return results

    for f in RESULTS_DIR.glob("*.json"):
        if f.name == "all_results.json":
            continue
        try:
            data = json.loads(f.read_text())
            label = data.get("framework_label", f.stem)
            results[label] = data
        except Exception:
            pass
    return results


def get_current_progress() -> tuple[str, int, int]:
    if not LOG_FILE.exists():
        return "Not started", 0, 0

    content = LOG_FILE.read_text()
    lines = content.split("\n")

    current_config = "Unknown"
    current_iter = 0
    total_iter = 10

    for line in reversed(lines):
        if "# CONFIG:" in line:
            current_config = line.replace("# CONFIG:", "").strip()
            break
        if "Iteration" in line and "..." in line:
            try:
                current_iter = int(line.split("Iteration")[1].split("...")[0].strip())
            except Exception:
                pass

    return current_config, current_iter, total_iter


def is_benchmark_running() -> bool:
    result = os.popen("ps aux | grep benchmark_all_frameworks | grep -v grep").read()
    return len(result.strip()) > 0


def format_metric(
    value: float, is_pct: bool = False, lower_better: bool = False
) -> str:
    if is_pct:
        formatted = f"{value * 100:>6.1f}%"
    else:
        formatted = f"${value:>8,.0f}"
    return formatted


def render_dashboard(
    results: dict[str, dict], current_config: str, current_iter: int, running: bool
):
    print(CLEAR)
    print(f"{BOLD}{CYAN}{'=' * 80}{RESET}")
    print(f"{BOLD}{CYAN}  INSURANCE SUPPLEMENT AGENT - BENCHMARK DASHBOARD{RESET}")
    print(f"{BOLD}{CYAN}{'=' * 80}{RESET}")
    print(f"  Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Ground Truth Supplement: ${GROUND_TRUTH:,.2f}")
    print()

    if running:
        status = f"{GREEN}RUNNING{RESET}"
        print(
            f"  Status: {status} | Current: {YELLOW}{current_config}{RESET} | Iteration: {current_iter}/10"
        )
    else:
        if results:
            status = f"{GREEN}COMPLETE{RESET}"
        else:
            status = f"{YELLOW}NOT STARTED{RESET}"
        print(f"  Status: {status}")

    print()
    print(f"{BOLD}{'=' * 80}{RESET}")
    print(f"{BOLD}  RESULTS{RESET}")
    print(f"{'=' * 80}")

    if not results:
        print(
            f"\n  {YELLOW}No results yet. Waiting for first config to complete...{RESET}\n"
        )
    else:
        print()
        print(f"  {'Config':<40} {'F1':>8} {'MAE':>10} {'MAPE':>8} {'Success':>8}")
        print(f"  {'-' * 76}")

        sorted_results = sorted(
            results.items(),
            key=lambda x: x[1].get("f1_score", {}).get("mean", 0),
            reverse=True,
        )

        for i, (label, data) in enumerate(sorted_results):
            f1 = data.get("f1_score", {}).get("mean", 0)
            mae = data.get("mae", {}).get("mean", 0)
            mape = data.get("mape", 0)
            success = data.get("success_rate", 0)

            if i == 0 and len(sorted_results) > 1:
                prefix = f"{GREEN}*"
                suffix = RESET
            else:
                prefix = " "
                suffix = ""

            print(
                f"  {prefix}{label:<39}{suffix} {f1 * 100:>7.1f}% ${mae:>8,.0f} {mape * 100:>7.1f}% {success * 100:>7.0f}%"
            )

        print(f"  {'-' * 76}")
        print()

        print(f"{BOLD}  DETAILED METRICS{RESET}")
        print()

        for label, data in sorted_results:
            f1_mean = data.get("f1_score", {}).get("mean", 0)
            f1_std = data.get("f1_score", {}).get("std", 0)
            prec = data.get("precision", {}).get("mean", 0)
            recall = data.get("recall", {}).get("mean", 0)
            mae_mean = data.get("mae", {}).get("mean", 0)
            mae_std = data.get("mae", {}).get("std", 0)
            mape = data.get("mape", 0)
            sup_mean = data.get("supplement_value", {}).get("mean", 0)
            sup_std = data.get("supplement_value", {}).get("std", 0)
            consistency = data.get("consistency_score", 0)
            avg_time = data.get("avg_run_time_seconds", 0)
            success = data.get("success_rate", 0)

            error_direction = "UNDER" if sup_mean < GROUND_TRUTH else "OVER"
            error_color = YELLOW if sup_mean < GROUND_TRUTH else GREEN

            print(f"  {BOLD}{label}{RESET}")
            print(
                f"    F1: {f1_mean * 100:.1f}% (+/-{f1_std * 100:.1f}%)  |  Precision: {prec * 100:.1f}%  |  Recall: {recall * 100:.1f}%"
            )
            print(
                f"    Supplement: ${sup_mean:,.0f} (+/-${sup_std:,.0f})  |  {error_color}{error_direction} by ${abs(GROUND_TRUTH - sup_mean):,.0f}{RESET}"
            )
            print(
                f"    MAE: ${mae_mean:,.0f} (+/-${mae_std:,.0f})  |  MAPE: {mape * 100:.1f}%"
            )
            print(
                f"    Consistency: {consistency * 100:.1f}%  |  Avg Time: {avg_time:.0f}s  |  Success: {success * 100:.0f}%"
            )
            print()

    print(f"{'=' * 80}")
    print(f"  {CYAN}Press Ctrl+C to exit{RESET}")
    print()


def main():
    refresh_interval = 10

    try:
        while True:
            results = load_results()
            current_config, current_iter, _ = get_current_progress()
            running = is_benchmark_running()

            render_dashboard(results, current_config, current_iter, running)

            if not running and results:
                print(f"  {GREEN}Benchmark complete! Final results above.{RESET}")
                print()
                break

            time.sleep(refresh_interval)

    except KeyboardInterrupt:
        print(f"\n  {YELLOW}Dashboard stopped.{RESET}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
