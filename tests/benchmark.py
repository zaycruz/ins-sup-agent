#!/usr/bin/env python3
"""
Cross-validation benchmark for supplement accuracy.
Runs N iterations and calculates average precision, recall, F1, and value capture.
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
        "keywords": ["overhead", "profit", "o&p", "o & p"],
    },
]

GROUND_TRUTH_TOTAL = sum(item["rcv"] for item in GROUND_TRUTH_ITEMS)


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
            self.ai_total_value / GROUND_TRUTH_TOTAL if GROUND_TRUTH_TOTAL > 0 else 0.0
        )

    @property
    def false_positive_rate(self) -> float:
        total_ai = self.true_positives + self.false_positives
        if total_ai == 0:
            return 0.0
        return self.false_positives / total_ai


def match_ai_to_ground_truth(ai_items: list[dict]) -> RunMetrics:
    """Match AI-generated items to ground truth items."""
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


async def submit_job(client: httpx.AsyncClient, num_photos: int = 20) -> str | None:
    """Submit a job and return job_id."""
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
    }

    response = await client.post(f"{BASE_URL}/v1/jobs", files=files, data=data)
    if response.status_code != 202:
        print(f"  Submit failed: {response.status_code}")
        return None

    return response.json()["job_id"]


async def poll_job(
    client: httpx.AsyncClient, job_id: str, max_wait: int = 600
) -> dict | None:
    """Poll until job completes."""
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


async def get_supplements(client: httpx.AsyncClient, job_id: str) -> list[dict]:
    """Extract supplement items from the completed job."""
    response = await client.get(f"{BASE_URL}/v1/jobs/{job_id}/report?format=html")
    if response.status_code != 200:
        return []

    html = response.text
    items = []

    import re

    patterns = [
        r"SUP-\d+[^<]*?(\$[\d,]+\.?\d*)",
        r"<td[^>]*>([^<]*(?:solar|underlayment|valley|fascia|flue|clean|fence|fireplace|overhead|profit)[^<]*)</td>",
    ]

    return items


async def run_single_iteration(
    iteration: int, num_photos: int = 20
) -> RunMetrics | None:
    """Run a single benchmark iteration."""
    print(f"\n  Iteration {iteration + 1}...")
    start_time = time.time()

    async with httpx.AsyncClient(timeout=60.0) as client:
        job_id = await submit_job(client, num_photos)
        if not job_id:
            return None

        print(f"    Job: {job_id[:8]}...")
        result = await poll_job(client, job_id)

        if not result or result["status"] != "completed":
            print(f"    Failed: {result.get('status') if result else 'timeout'}")
            return None

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


async def run_benchmark(num_iterations: int = 10, num_photos: int = 20) -> dict:
    """Run full benchmark with multiple iterations."""
    print(f"\n{'=' * 60}")
    print(f"SUPPLEMENT ACCURACY BENCHMARK")
    print(f"Iterations: {num_iterations}, Photos: {num_photos}")
    print(f"{'=' * 60}")

    all_metrics: list[RunMetrics] = []

    for i in range(num_iterations):
        metrics = await run_single_iteration(i, num_photos)
        if metrics:
            all_metrics.append(metrics)
            print(
                f"    P:{metrics.precision:.1%} R:{metrics.recall:.1%} F1:{metrics.f1_score:.1%}"
            )

    if not all_metrics:
        print("\nNo successful runs!")
        return {}

    avg_precision = sum(m.precision for m in all_metrics) / len(all_metrics)
    avg_recall = sum(m.recall for m in all_metrics) / len(all_metrics)
    avg_f1 = sum(m.f1_score for m in all_metrics) / len(all_metrics)
    avg_value_capture = sum(m.value_capture_rate for m in all_metrics) / len(
        all_metrics
    )
    avg_fpr = sum(m.false_positive_rate for m in all_metrics) / len(all_metrics)
    avg_time = sum(m.run_time_seconds for m in all_metrics) / len(all_metrics)

    std_precision = (
        sum((m.precision - avg_precision) ** 2 for m in all_metrics) / len(all_metrics)
    ) ** 0.5
    std_recall = (
        sum((m.recall - avg_recall) ** 2 for m in all_metrics) / len(all_metrics)
    ) ** 0.5
    std_f1 = (
        sum((m.f1_score - avg_f1) ** 2 for m in all_metrics) / len(all_metrics)
    ) ** 0.5

    print(f"\n{'=' * 60}")
    print(f"RESULTS ({len(all_metrics)}/{num_iterations} successful runs)")
    print(f"{'=' * 60}")
    print(f"\n{'Metric':<25} {'Mean':>10} {'Std Dev':>10}")
    print(f"{'-' * 45}")
    print(f"{'Precision':<25} {avg_precision:>9.1%} {std_precision:>9.1%}")
    print(f"{'Recall':<25} {avg_recall:>9.1%} {std_recall:>9.1%}")
    print(f"{'F1 Score':<25} {avg_f1:>9.1%} {std_f1:>9.1%}")
    print(f"{'Value Capture':<25} {avg_value_capture:>9.1%}")
    print(f"{'False Positive Rate':<25} {avg_fpr:>9.1%}")
    print(f"{'Avg Run Time':<25} {avg_time:>8.1f}s")

    return {
        "iterations": num_iterations,
        "successful_runs": len(all_metrics),
        "precision": {"mean": avg_precision, "std": std_precision},
        "recall": {"mean": avg_recall, "std": std_recall},
        "f1_score": {"mean": avg_f1, "std": std_f1},
        "value_capture": avg_value_capture,
        "false_positive_rate": avg_fpr,
        "avg_run_time_seconds": avg_time,
    }


if __name__ == "__main__":
    import sys

    iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    photos = int(sys.argv[2]) if len(sys.argv) > 2 else 20

    results = asyncio.run(run_benchmark(iterations, photos))

    output_file = Path("/tmp/benchmark_results.json")
    output_file.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved to {output_file}")
