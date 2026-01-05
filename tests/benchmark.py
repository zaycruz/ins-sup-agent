#!/usr/bin/env python3
"""
Cross-validation benchmark for supplement accuracy.
Runs N iterations and calculates precision, recall, F1, MAE, and value metrics.
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

BASE_URL = "http://localhost:8000"
TEST_DATA_DIR = Path("/home/zay/projects/ins-sup-agent/test-data/Clarivel Perez")

ORIGINAL_ESTIMATE_RCV = 16415.92
SUPPLEMENTED_ESTIMATE_RCV = 28958.38
GROUND_TRUTH_SUPPLEMENT_AMOUNT = SUPPLEMENTED_ESTIMATE_RCV - ORIGINAL_ESTIMATE_RCV

GROUND_TRUTH_ITEMS = [
    {
        "id": "solar",
        "description": "Solar Panel work",
        "rcv": 7826.98,
        "keywords": ["solar", "panel", "detach", "reset"],
    },
    {
        "id": "underlayment",
        "description": "Additional underlayment removal",
        "rcv": 487.34,
        "keywords": ["underlayment", "felt", "layer"],
    },
    {
        "id": "valley",
        "description": "Valley metal R&R",
        "rcv": 344.70,
        "keywords": ["valley", "metal"],
    },
    {
        "id": "fascia",
        "description": "Fascia metal R&R",
        "rcv": 1670.76,
        "keywords": ["fascia", "metal"],
    },
    {
        "id": "flue_cap",
        "description": "Flue cap oversized",
        "rcv": 298.34,
        "keywords": ["flue", "cap", "oversized"],
    },
    {
        "id": "pressure_clean",
        "description": "Pressure cleaning",
        "rcv": 470.40,
        "keywords": ["pressure", "clean", "spray", "chemical"],
    },
    {
        "id": "fence_stain",
        "description": "Wood fence staining",
        "rcv": 1171.20,
        "keywords": ["fence", "stain", "wood"],
    },
    {
        "id": "fireplace_labor",
        "description": "Fireplace labor minimum",
        "rcv": 133.72,
        "keywords": ["fireplace", "labor", "minimum"],
    },
    {
        "id": "overhead_profit",
        "description": "Overhead & Profit",
        "rcv": 5580.86,
        "keywords": ["overhead", "profit", "o&p", "o & p", "gc", "contractor"],
    },
]

GROUND_TRUTH_ITEM_TOTAL = sum(item["rcv"] for item in GROUND_TRUTH_ITEMS)


@dataclass
class MatchResult:
    gt_item_id: str
    ai_description: str
    ai_value: float
    gt_value: float
    value_accuracy: float


@dataclass
class RunMetrics:
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    ai_total_value: float = 0.0
    matched_value: float = 0.0
    gt_matched_value: float = 0.0
    matches: list[MatchResult] = field(default_factory=list)
    ai_items: list[dict] = field(default_factory=list)
    run_time_seconds: float = 0.0
    error: str | None = None

    @property
    def precision(self) -> float:
        if self.true_positives + self.false_positives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_positives)

    @property
    def recall(self) -> float:
        if self.true_positives + self.false_negatives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_negatives)

    @property
    def f1_score(self) -> float:
        if self.precision + self.recall == 0:
            return 0.0
        return 2 * (self.precision * self.recall) / (self.precision + self.recall)

    @property
    def value_capture_rate(self) -> float:
        return (
            self.ai_total_value / GROUND_TRUTH_ITEM_TOTAL
            if GROUND_TRUTH_ITEM_TOTAL > 0
            else 0.0
        )

    @property
    def absolute_error(self) -> float:
        return abs(self.ai_total_value - GROUND_TRUTH_SUPPLEMENT_AMOUNT)

    @property
    def percentage_error(self) -> float:
        if GROUND_TRUTH_SUPPLEMENT_AMOUNT == 0:
            return 0.0
        return (
            self.ai_total_value - GROUND_TRUTH_SUPPLEMENT_AMOUNT
        ) / GROUND_TRUTH_SUPPLEMENT_AMOUNT

    @property
    def false_positive_rate(self) -> float:
        total_ai = self.true_positives + self.false_positives
        if total_ai == 0:
            return 0.0
        return self.false_positives / total_ai


def match_ai_to_ground_truth(ai_items: list[dict]) -> RunMetrics:
    metrics = RunMetrics()
    metrics.ai_items = ai_items
    metrics.ai_total_value = sum(item.get("value", 0) for item in ai_items)

    matched_gt_ids = set()
    matched_ai_indices = set()

    for gt_item in GROUND_TRUTH_ITEMS:
        gt_keywords = [kw.lower() for kw in gt_item["keywords"]]

        for i, ai_item in enumerate(ai_items):
            if i in matched_ai_indices:
                continue

            ai_desc = ai_item.get("description", "").lower()
            ai_code = ai_item.get("xactimate_code", "").lower()
            ai_combined = f"{ai_desc} {ai_code}"

            if any(kw in ai_combined for kw in gt_keywords):
                ai_value = ai_item.get("value", 0)
                value_accuracy = ai_value / gt_item["rcv"] if gt_item["rcv"] > 0 else 0

                metrics.matches.append(
                    MatchResult(
                        gt_item_id=gt_item["id"],
                        ai_description=ai_item.get("description", ""),
                        ai_value=ai_value,
                        gt_value=gt_item["rcv"],
                        value_accuracy=value_accuracy,
                    )
                )
                metrics.matched_value += ai_value
                metrics.gt_matched_value += gt_item["rcv"]
                matched_gt_ids.add(gt_item["id"])
                matched_ai_indices.add(i)
                break

    metrics.true_positives = len(matched_gt_ids)
    metrics.false_negatives = len(GROUND_TRUTH_ITEMS) - len(matched_gt_ids)
    metrics.false_positives = len(ai_items) - len(matched_ai_indices)

    return metrics


async def submit_job(
    client: httpx.AsyncClient,
    num_photos: int = 20,
    vision_framework: str = "parallel_aggregate",
    estimate_framework: str = "single",
    gap_framework: str = "single",
    strategist_framework: str = "single",
) -> str | None:
    estimate_pdf = TEST_DATA_DIR / "estimate" / "mijh4sdaxl4pirrf.pdf"
    photos_dir = TEST_DATA_DIR / "photos"

    all_photos = sorted(photos_dir.glob("*.jpeg"))
    photos = all_photos[:num_photos]

    metadata = {
        "carrier": "AllState",
        "claim_number": "CLM-PEREZ-2025",
        "insured_name": "Clarivel Perez",
        "property_address": "6520 Burrows Ct, Plano, TX 75023",
    }

    costs = {"materials_cost": 12000.0, "labor_cost": 10000.0, "other_costs": 2000.0}
    targets = {"minimum_margin": 0.33}

    files = [
        (
            "estimate_pdf",
            (estimate_pdf.name, open(estimate_pdf, "rb"), "application/pdf"),
        )
    ]
    for photo in photos:
        files.append(("photos", (photo.name, open(photo, "rb"), "image/jpeg")))

    data = {
        "metadata": json.dumps(metadata),
        "costs": json.dumps(costs),
        "targets": json.dumps(targets),
        "vision_framework": vision_framework,
        "estimate_framework": estimate_framework,
        "gap_framework": gap_framework,
        "strategist_framework": strategist_framework,
    }

    response = await client.post(f"{BASE_URL}/v1/jobs", files=files, data=data)
    if response.status_code != 202:
        print(f"  Submit failed: {response.status_code}")
        return None

    return response.json()["job_id"]


async def poll_job(
    client: httpx.AsyncClient, job_id: str, max_wait: int = 600
) -> dict | None:
    start = time.time()
    while time.time() - start < max_wait:
        response = await client.get(f"{BASE_URL}/v1/jobs/{job_id}")
        if response.status_code != 200:
            return None
        job = response.json()
        status = job["status"]
        if status in ["completed", "failed", "escalated"]:
            return job
        await asyncio.sleep(5)
    return None


async def run_single_iteration(
    iteration: int,
    num_photos: int = 20,
    vision_framework: str = "parallel_aggregate",
    estimate_framework: str = "single",
    gap_framework: str = "single",
    strategist_framework: str = "single",
) -> RunMetrics | None:
    print(f"\n  Iteration {iteration + 1}...")
    start_time = time.time()

    async with httpx.AsyncClient(timeout=60.0) as client:
        job_id = await submit_job(
            client,
            num_photos,
            vision_framework,
            estimate_framework,
            gap_framework,
            strategist_framework,
        )
        if not job_id:
            metrics = RunMetrics()
            metrics.error = "submit_failed"
            metrics.run_time_seconds = time.time() - start_time
            return metrics

        print(f"    Job: {job_id[:8]}...")
        result = await poll_job(client, job_id)

        if not result:
            metrics = RunMetrics()
            metrics.error = "timeout"
            metrics.run_time_seconds = time.time() - start_time
            return metrics

        if result["status"] != "completed":
            metrics = RunMetrics()
            metrics.error = result["status"]
            metrics.run_time_seconds = time.time() - start_time
            print(f"    Failed: {result['status']}")
            return metrics

        results = result.get("results", {})
        supplement_count = results.get("supplement_count", 0)
        supplement_total = results.get("supplement_total", 0)
        supplement_items = results.get("supplement_items", [])

        print(f"    Completed: {supplement_count} items, ${supplement_total:,.2f}")

        ai_items = []
        for item in supplement_items:
            ai_items.append(
                {
                    "description": item.get("line_item_description", ""),
                    "value": item.get("estimated_value", 0),
                    "xactimate_code": item.get("supplement_id", ""),
                }
            )

        metrics = match_ai_to_ground_truth(ai_items)
        metrics.run_time_seconds = time.time() - start_time

        return metrics


async def run_benchmark(
    num_iterations: int = 10,
    num_photos: int = 20,
    vision_framework: str = "parallel_aggregate",
    estimate_framework: str = "single",
    gap_framework: str = "single",
    strategist_framework: str = "single",
) -> dict:
    framework_label = f"v:{vision_framework}/e:{estimate_framework}/g:{gap_framework}/s:{strategist_framework}"
    print(f"\n{'=' * 70}")
    print(f"SUPPLEMENT ACCURACY BENCHMARK")
    print(f"Frameworks: {framework_label}")
    print(f"Iterations: {num_iterations}, Photos: {num_photos}")
    print(f"Ground Truth Supplement: ${GROUND_TRUTH_SUPPLEMENT_AMOUNT:,.2f}")
    print(f"{'=' * 70}")

    all_metrics: list[RunMetrics] = []
    failed_runs: list[RunMetrics] = []

    for i in range(num_iterations):
        metrics = await run_single_iteration(
            i,
            num_photos,
            vision_framework,
            estimate_framework,
            gap_framework,
            strategist_framework,
        )
        if metrics:
            if metrics.error:
                failed_runs.append(metrics)
                print(f"    ERROR: {metrics.error}")
            else:
                all_metrics.append(metrics)
                error = metrics.ai_total_value - GROUND_TRUTH_SUPPLEMENT_AMOUNT
                print(
                    f"    P:{metrics.precision:.1%} R:{metrics.recall:.1%} "
                    f"F1:{metrics.f1_score:.1%} | "
                    f"${metrics.ai_total_value:,.0f} (err: ${error:+,.0f})"
                )

    if not all_metrics:
        print("\nNo successful runs!")
        return {
            "framework_label": framework_label,
            "successful_runs": 0,
            "failed_runs": len(failed_runs),
        }

    avg_precision = sum(m.precision for m in all_metrics) / len(all_metrics)
    avg_recall = sum(m.recall for m in all_metrics) / len(all_metrics)
    avg_f1 = sum(m.f1_score for m in all_metrics) / len(all_metrics)
    avg_value = sum(m.ai_total_value for m in all_metrics) / len(all_metrics)
    avg_mae = sum(m.absolute_error for m in all_metrics) / len(all_metrics)
    avg_mape = sum(abs(m.percentage_error) for m in all_metrics) / len(all_metrics)
    avg_fpr = sum(m.false_positive_rate for m in all_metrics) / len(all_metrics)
    avg_time = sum(m.run_time_seconds for m in all_metrics) / len(all_metrics)

    std_f1 = (
        sum((m.f1_score - avg_f1) ** 2 for m in all_metrics) / len(all_metrics)
    ) ** 0.5
    std_mae = (
        sum((m.absolute_error - avg_mae) ** 2 for m in all_metrics) / len(all_metrics)
    ) ** 0.5
    std_value = (
        sum((m.ai_total_value - avg_value) ** 2 for m in all_metrics) / len(all_metrics)
    ) ** 0.5

    consistency_score = 1 - (std_value / avg_value if avg_value > 0 else 1)

    print(f"\n{'=' * 70}")
    print(
        f"RESULTS: {framework_label} ({len(all_metrics)}/{num_iterations} successful)"
    )
    print(f"{'=' * 70}")
    print(f"\n{'Metric':<30} {'Mean':>12} {'Std Dev':>12}")
    print(f"{'-' * 54}")
    print(f"{'Precision':<30} {avg_precision:>11.1%} {'':<12}")
    print(f"{'Recall':<30} {avg_recall:>11.1%} {'':<12}")
    print(f"{'F1 Score':<30} {avg_f1:>11.1%} {std_f1:>11.1%}")
    print(f"{'False Positive Rate':<30} {avg_fpr:>11.1%} {'':<12}")
    print(f"{'-' * 54}")
    print(f"{'Supplement Value':<30} ${avg_value:>10,.0f} ${std_value:>10,.0f}")
    print(f"{'Ground Truth':<30} ${GROUND_TRUTH_SUPPLEMENT_AMOUNT:>10,.0f}")
    print(f"{'Mean Absolute Error (MAE)':<30} ${avg_mae:>10,.0f} ${std_mae:>10,.0f}")
    print(f"{'Mean Abs % Error (MAPE)':<30} {avg_mape:>11.1%}")
    print(f"{'-' * 54}")
    print(f"{'Consistency Score':<30} {consistency_score:>11.1%}")
    print(f"{'Avg Run Time':<30} {avg_time:>10.1f}s")
    print(f"{'Success Rate':<30} {len(all_metrics) / num_iterations:>11.1%}")

    return {
        "vision_framework": vision_framework,
        "estimate_framework": estimate_framework,
        "gap_framework": gap_framework,
        "strategist_framework": strategist_framework,
        "framework_label": framework_label,
        "iterations": num_iterations,
        "successful_runs": len(all_metrics),
        "failed_runs": len(failed_runs),
        "success_rate": len(all_metrics) / num_iterations,
        "precision": {"mean": avg_precision},
        "recall": {"mean": avg_recall},
        "f1_score": {"mean": avg_f1, "std": std_f1},
        "false_positive_rate": avg_fpr,
        "supplement_value": {"mean": avg_value, "std": std_value},
        "ground_truth": GROUND_TRUTH_SUPPLEMENT_AMOUNT,
        "mae": {"mean": avg_mae, "std": std_mae},
        "mape": avg_mape,
        "consistency_score": consistency_score,
        "avg_run_time_seconds": avg_time,
    }


if __name__ == "__main__":
    import sys

    iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    photos = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    vision_fw = sys.argv[3] if len(sys.argv) > 3 else "parallel_aggregate"
    estimate_fw = sys.argv[4] if len(sys.argv) > 4 else "single"
    gap_fw = sys.argv[5] if len(sys.argv) > 5 else "single"
    strategist_fw = sys.argv[6] if len(sys.argv) > 6 else "single"

    results = asyncio.run(
        run_benchmark(iterations, photos, vision_fw, estimate_fw, gap_fw, strategist_fw)
    )

    output_file = Path(
        f"/tmp/benchmark_{vision_fw}_{estimate_fw}_{gap_fw}_{strategist_fw}.json"
    )
    output_file.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved to {output_file}")
