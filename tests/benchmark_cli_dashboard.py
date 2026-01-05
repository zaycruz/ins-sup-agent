#!/usr/bin/env python3
"""
Live CLI dashboard for benchmark monitoring.
Run: uv run python tests/benchmark_cli_dashboard.py
"""

import json
import os
import time
from pathlib import Path

RESULTS_DIR = Path("/tmp/framework_benchmarks")
LOG_FILE = Path("/tmp/benchmark_all.log")
GROUND_TRUTH = 12542.46
TOTAL_CONFIGS = 8


def clear_screen():
    os.system("clear" if os.name == "posix" else "cls")


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


def get_current_progress() -> tuple[str, int]:
    if not LOG_FILE.exists():
        return "Not started", 0
    content = LOG_FILE.read_text()
    lines = content.split("\n")
    current_config = "Unknown"
    current_iter = 0
    for line in reversed(lines):
        if "# CONFIG:" in line:
            current_config = line.replace("# CONFIG:", "").strip()
            break
        if "Iteration" in line and "..." in line:
            try:
                current_iter = int(line.split("Iteration")[1].split("...")[0].strip())
            except Exception:
                pass
    return current_config, current_iter


def is_benchmark_running() -> bool:
    result = os.popen("ps aux | grep benchmark_all_frameworks | grep -v grep").read()
    return len(result.strip()) > 0


def get_recent_log_lines(n: int = 8) -> list[str]:
    if not LOG_FILE.exists():
        return []
    lines = LOG_FILE.read_text().strip().split("\n")
    return lines[-n:] if len(lines) >= n else lines


def render_dashboard():
    results = load_results()
    current_config, current_iter = get_current_progress()
    running = is_benchmark_running()

    sorted_results = sorted(
        results.items(),
        key=lambda x: x[1].get("f1_score", {}).get("mean", 0),
        reverse=True,
    )

    clear_screen()

    # Header
    status = (
        "🟢 RUNNING" if running else ("✅ COMPLETE" if results else "⏳ NOT STARTED")
    )
    print("=" * 90)
    print(f"  INSURANCE SUPPLEMENT AGENT - BENCHMARK DASHBOARD  |  {status}")
    print("=" * 90)
    print(f"  Current: {current_config}")
    print(
        f"  Progress: Config {len(results)}/{TOTAL_CONFIGS} | Iteration {current_iter}/5"
    )
    print(f"  Ground Truth: ${GROUND_TRUTH:,.2f}")
    print("=" * 90)
    print()

    # Results table
    if sorted_results:
        print(
            f"{'Rank':<5} {'Framework Config':<50} {'F1':>8} {'MAE':>10} {'Supplement':>12} {'Diff':>10}"
        )
        print("-" * 90)

        for i, (label, data) in enumerate(sorted_results, 1):
            f1 = data.get("f1_score", {}).get("mean", 0) * 100
            mae = data.get("mae", {}).get("mean", 0)
            sup = data.get("supplement_value", {}).get("mean", 0)
            diff = sup - GROUND_TRUTH
            diff_str = f"+${diff:,.0f}" if diff >= 0 else f"-${abs(diff):,.0f}"

            badge = "🥇" if i == 1 else ("🥈" if i == 2 else ("🥉" if i == 3 else "  "))

            print(
                f"{badge}{i:<3} {label:<50} {f1:>7.1f}% ${mae:>8,.0f} ${sup:>10,.0f} {diff_str:>10}"
            )

        print("-" * 90)

        # Summary stats
        best_f1 = sorted_results[0][1].get("f1_score", {}).get("mean", 0) * 100
        best_mae = min(d.get("mae", {}).get("mean", 999999) for _, d in sorted_results)
        print(f"\n  Best F1: {best_f1:.1f}%  |  Best MAE: ${best_mae:,.0f}")
    else:
        print("  No results yet. Waiting for first config to complete...")

    print()
    print("=" * 90)
    print("  RECENT LOG:")
    print("-" * 90)
    for line in get_recent_log_lines(6):
        print(f"  {line[:86]}")
    print("=" * 90)
    print(f"\n  Auto-refreshing every 5 seconds. Press Ctrl+C to exit.")


def main():
    try:
        while True:
            render_dashboard()
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n\nDashboard stopped.")


if __name__ == "__main__":
    main()
