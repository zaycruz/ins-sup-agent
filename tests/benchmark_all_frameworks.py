#!/usr/bin/env python3
"""
Multi-framework benchmark runner.
Runs benchmarks for all framework combinations and generates comparison report.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

VISION_FRAMEWORKS = ["ensemble_voting"]
ESTIMATE_FRAMEWORKS = ["single", "ensemble"]
GAP_FRAMEWORKS = ["single", "consensus"]
STRATEGIST_FRAMEWORKS = ["single", "consensus"]

OUTPUT_DIR = Path("/tmp/framework_benchmarks")


def get_framework_configs() -> list[dict[str, str]]:
    configs = []
    for vision in VISION_FRAMEWORKS:
        for estimate in ESTIMATE_FRAMEWORKS:
            for gap in GAP_FRAMEWORKS:
                for strategist in STRATEGIST_FRAMEWORKS:
                    configs.append(
                        {
                            "vision": vision,
                            "estimate": estimate,
                            "gap": gap,
                            "strategist": strategist,
                            "label": f"v:{vision}/e:{estimate}/g:{gap}/s:{strategist}",
                        }
                    )
    return configs


async def run_framework_benchmark(
    config: dict[str, str], iterations: int, photos: int
) -> dict | None:
    from tests.benchmark import run_benchmark

    print(f"\n{'#' * 70}")
    print(f"# CONFIG: {config['label']}")
    print(f"{'#' * 70}")

    try:
        result = await run_benchmark(
            iterations,
            photos,
            config["vision"],
            config["estimate"],
            config["gap"],
            config["strategist"],
        )
        return result
    except Exception as e:
        print(f"ERROR running {config['label']}: {e}")
        return None


def generate_comparison_report(results: list[dict]) -> str:
    lines = []
    lines.append("=" * 100)
    lines.append("MULTI-FRAMEWORK BENCHMARK COMPARISON REPORT")
    lines.append(f"Generated: {datetime.now().isoformat()}")
    lines.append("=" * 100)
    lines.append("")

    successful = [r for r in results if r and r.get("successful_runs", 0) > 0]

    if not successful:
        lines.append("No successful benchmark runs!")
        return "\n".join(lines)

    lines.append(
        f"{'Framework Config':<55} {'F1':>8} {'MAE':>10} {'MAPE':>8} {'Cons':>8}"
    )
    lines.append("-" * 100)

    ranked_f1 = sorted(
        successful, key=lambda x: x.get("f1_score", {}).get("mean", 0), reverse=True
    )

    for data in ranked_f1:
        label = data.get("framework_label", "unknown")
        f1 = data.get("f1_score", {}).get("mean", 0) * 100
        mae = data.get("mae", {}).get("mean", 0)
        mape = data.get("mape", 0) * 100
        cons = data.get("consistency_score", 0) * 100

        lines.append(
            f"{label:<55} {f1:>7.1f}% ${mae:>8,.0f} {mape:>7.1f}% {cons:>7.1f}%"
        )

    lines.append("-" * 100)
    lines.append("")

    lines.append("RANKING BY F1 SCORE (Best to Worst):")
    for i, data in enumerate(ranked_f1, 1):
        f1 = data.get("f1_score", {}).get("mean", 0) * 100
        lines.append(f"  {i}. {data.get('framework_label')}: {f1:.1f}%")

    lines.append("")
    lines.append("RANKING BY MAE (Best to Worst):")
    ranked_mae = sorted(
        successful, key=lambda x: x.get("mae", {}).get("mean", float("inf"))
    )
    for i, data in enumerate(ranked_mae, 1):
        mae = data.get("mae", {}).get("mean", 0)
        lines.append(f"  {i}. {data.get('framework_label')}: ${mae:,.0f}")

    lines.append("")

    def parse_label(label: str) -> dict[str, str]:
        parts = {}
        for chunk in label.split("/"):
            if ":" in chunk:
                k, v = chunk.split(":", 1)
                parts[k] = v
        return parts

    def summarize_axis(axis: str) -> list[str]:
        buckets: dict[str, list[dict]] = {}
        for r in successful:
            label = r.get("framework_label", "")
            parsed = parse_label(label)
            key = parsed.get(axis, "unknown")
            buckets.setdefault(key, []).append(r)

        rows = []
        for key, items in sorted(buckets.items(), key=lambda kv: kv[0]):
            f1_vals = [i.get("f1_score", {}).get("mean", 0) for i in items]
            mae_vals = [i.get("mae", {}).get("mean", 0) for i in items]
            if not f1_vals or not mae_vals:
                continue
            rows.append(
                f"  {axis}:{key:<10} avg F1={(sum(f1_vals) / len(f1_vals)) * 100:5.1f}%  avg MAE=${sum(mae_vals) / len(mae_vals):,.0f}  (n={len(items)})"
            )
        return rows

    lines.append("ROLE-LEVEL AGGREGATES (marginal impact across configs):")
    for axis in ["e", "g", "s"]:
        lines.extend(summarize_axis(axis))
    lines.append("")

    lines.append("=" * 100)

    best_f1 = ranked_f1[0] if ranked_f1 else None
    best_mae = ranked_mae[0] if ranked_mae else None

    if best_f1 and best_mae:
        lines.append("RECOMMENDATIONS:")
        lines.append(f"  Best F1 Score: {best_f1.get('framework_label')}")
        lines.append(f"  Best MAE: {best_mae.get('framework_label')}")

        if best_f1.get("framework_label") == best_mae.get("framework_label"):
            lines.append(f"  OVERALL BEST: {best_f1.get('framework_label')}")
        else:
            lines.append("  Note: Best F1 and MAE differ - consider tradeoffs")

    lines.append("=" * 100)

    return "\n".join(lines)


async def main(iterations: int = 10, photos: int = 20, quick: bool = False):
    OUTPUT_DIR.mkdir(exist_ok=True)

    configs = get_framework_configs()

    results: list[dict] = []

    for config in configs:
        result = await run_framework_benchmark(config, iterations, photos)
        if result:
            results.append(result)

            safe_label = config["label"].replace(":", "_").replace("/", "_")
            output_file = OUTPUT_DIR / f"{safe_label}.json"
            output_file.write_text(json.dumps(result, indent=2))
            print(f"\nSaved {config['label']} results to {output_file}")

    report = generate_comparison_report(results)
    print(f"\n{report}")

    report_file = OUTPUT_DIR / "comparison_report.txt"
    report_file.write_text(report)
    print(f"\nReport saved to {report_file}")

    all_results_file = OUTPUT_DIR / "all_results.json"
    all_results_file.write_text(json.dumps(results, indent=2))
    print(f"All results saved to {all_results_file}")


if __name__ == "__main__":
    iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    photos = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    quick = "--quick" in sys.argv

    asyncio.run(main(iterations, photos, quick))
