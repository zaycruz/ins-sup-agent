#!/usr/bin/env python3
"""
Web-based benchmark dashboard.
Run: uv run python tests/benchmark_web_dashboard.py
Then open: http://localhost:8050
"""

import json
import os
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI(title="Benchmark Dashboard")

RESULTS_DIR = Path("/tmp/framework_benchmarks")
LOG_FILE = Path("/tmp/benchmark_all.log")
GROUND_TRUTH = 12542.46


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


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    results = load_results()
    current_config, current_iter = get_current_progress()
    running = is_benchmark_running()

    status_color = "#22c55e" if running else ("#3b82f6" if results else "#eab308")
    status_text = "RUNNING" if running else ("COMPLETE" if results else "NOT STARTED")

    sorted_results = sorted(
        results.items(),
        key=lambda x: x[1].get("f1_score", {}).get("mean", 0),
        reverse=True,
    )

    best_f1 = (
        sorted_results[0][1].get("f1_score", {}).get("mean", 0) * 100
        if sorted_results
        else 0
    )
    best_mae = (
        min([d.get("mae", {}).get("mean", 999999) for _, d in sorted_results])
        if sorted_results
        else 0
    )

    rows_html = ""
    for i, (label, data) in enumerate(sorted_results):
        f1 = data.get("f1_score", {}).get("mean", 0)
        f1_std = data.get("f1_score", {}).get("std", 0)
        prec = data.get("precision", {}).get("mean", 0)
        recall = data.get("recall", {}).get("mean", 0)
        mae = data.get("mae", {}).get("mean", 0)
        mape = data.get("mape", 0)
        sup = data.get("supplement_value", {}).get("mean", 0)
        consistency = data.get("consistency_score", 0)
        success = data.get("success_rate", 0)
        avg_time = data.get("avg_run_time_seconds", 0)

        direction = "UNDER" if sup < GROUND_TRUTH else "OVER"
        direction_color = "#ef4444" if sup < GROUND_TRUTH else "#22c55e"
        diff = abs(GROUND_TRUTH - sup)

        rank_badge = ""
        if i == 0 and len(sorted_results) > 1:
            rank_badge = '<span style="background:#22c55e;color:white;padding:2px 8px;border-radius:4px;font-size:12px;margin-left:8px;">BEST</span>'

        rows_html += f"""
        <tr style="border-bottom:1px solid #e5e7eb;">
            <td style="padding:12px;font-weight:500;">{label}{rank_badge}</td>
            <td style="padding:12px;text-align:center;">{f1 * 100:.1f}%<br><span style="color:#9ca3af;font-size:12px;">±{f1_std * 100:.1f}%</span></td>
            <td style="padding:12px;text-align:center;">{prec * 100:.1f}%</td>
            <td style="padding:12px;text-align:center;">{recall * 100:.1f}%</td>
            <td style="padding:12px;text-align:center;">${mae:,.0f}</td>
            <td style="padding:12px;text-align:center;">{mape * 100:.1f}%</td>
            <td style="padding:12px;text-align:center;">${sup:,.0f}<br><span style="color:{direction_color};font-size:12px;">{direction} ${diff:,.0f}</span></td>
            <td style="padding:12px;text-align:center;">{consistency * 100:.0f}%</td>
            <td style="padding:12px;text-align:center;">{success * 100:.0f}%</td>
            <td style="padding:12px;text-align:center;">{avg_time:.0f}s</td>
        </tr>
        """

    if not rows_html:
        rows_html = '<tr><td colspan="10" style="padding:40px;text-align:center;color:#9ca3af;">No results yet. Waiting for first config to complete...</td></tr>'

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Benchmark Dashboard</title>
        <meta http-equiv="refresh" content="10">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f3f4f6; padding: 20px; }}
            .container {{ max-width: 1400px; margin: 0 auto; }}
            .header {{ background: white; padding: 24px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
            .header h1 {{ font-size: 24px; margin-bottom: 8px; }}
            .status {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 14px; font-weight: 500; color: white; background: {status_color}; }}
            .meta {{ color: #6b7280; font-size: 14px; margin-top: 12px; }}
            .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 20px; }}
            .card {{ background: white; padding: 20px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
            .card-label {{ font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; }}
            .card-value {{ font-size: 28px; font-weight: 600; margin-top: 4px; }}
            .table-container {{ background: white; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); overflow: hidden; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th {{ background: #f9fafb; padding: 12px; text-align: center; font-size: 12px; text-transform: uppercase; color: #6b7280; letter-spacing: 0.5px; }}
            th:first-child {{ text-align: left; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Insurance Supplement Agent - Benchmark Dashboard</h1>
                <span class="status">{status_text}</span>
                <div class="meta">
                    <strong>Current:</strong> {current_config} | <strong>Iteration:</strong> {current_iter}/10 | 
                    <strong>Ground Truth:</strong> ${GROUND_TRUTH:,.2f} |
                    <strong>Last Updated:</strong> {datetime.now().strftime("%H:%M:%S")}
                </div>
            </div>
            
            <div class="cards">
                <div class="card">
                    <div class="card-label">Configs Tested</div>
                    <div class="card-value">{len(results)} / 8</div>
                </div>
                <div class="card">
                    <div class="card-label">Best F1 Score</div>
                    <div class="card-value">{best_f1:.1f}%</div>
                </div>
                <div class="card">
                    <div class="card-label">Best MAE</div>
                    <div class="card-value">${best_mae:,.0f}</div>
                </div>
                <div class="card">
                    <div class="card-label">Target</div>
                    <div class="card-value">${GROUND_TRUTH:,.0f}</div>
                </div>
            </div>
            
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th style="text-align:left;">Config</th>
                            <th>F1 Score</th>
                            <th>Precision</th>
                            <th>Recall</th>
                            <th>MAE</th>
                            <th>MAPE</th>
                            <th>Supplement</th>
                            <th>Consistency</th>
                            <th>Success</th>
                            <th>Avg Time</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=html)


@app.get("/api/results")
async def api_results():
    return {
        "results": load_results(),
        "current_config": get_current_progress()[0],
        "current_iteration": get_current_progress()[1],
        "running": is_benchmark_running(),
        "ground_truth": GROUND_TRUTH,
    }


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("Benchmark Dashboard")
    print("=" * 50)
    print("Open in browser: http://localhost:8050")
    print("Auto-refreshes every 10 seconds")
    print("=" * 50 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8050, log_level="warning")
