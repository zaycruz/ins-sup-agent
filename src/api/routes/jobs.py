from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
)

from src.api.models.requests import ApproveRequest, RejectRequest
from src.api.models.responses import (
    JobCreatedResponse,
    JobListResponse,
    JobStatusResponse,
    JobSummary,
    PaginationInfo,
)
from src.api.store import job_store


router = APIRouter()
logger = logging.getLogger("api.jobs")


@router.post("/jobs", status_code=202, response_model=JobCreatedResponse)
async def create_job(
    background_tasks: BackgroundTasks,
    estimate_pdf: UploadFile = File(..., description="Insurance estimate PDF"),
    photos: list[UploadFile] = File(..., description="Job photos (1-20)"),
    metadata: str = Form(..., description="JSON metadata"),
    costs: str = Form(..., description="JSON costs"),
    targets: str | None = Form(None, description="JSON business targets"),
    callback_url: str | None = Form(None, description="Webhook URL for completion"),
) -> JobCreatedResponse:
    if not estimate_pdf.filename or not estimate_pdf.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_FILE_TYPE", "message": "Estimate must be PDF"},
        )

    if len(photos) > 20:
        raise HTTPException(
            status_code=400,
            detail={"code": "TOO_MANY_PHOTOS", "message": "Maximum 20 photos allowed"},
        )

    if len(photos) < 1:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_REQUEST",
                "message": "At least one photo required",
            },
        )

    try:
        metadata_dict = json.loads(metadata)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_JSON", "message": f"Invalid metadata JSON: {e}"},
        )

    try:
        costs_dict = json.loads(costs)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_JSON", "message": f"Invalid costs JSON: {e}"},
        )

    try:
        targets_dict = json.loads(targets) if targets else {"minimum_margin": 0.33}
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_JSON", "message": f"Invalid targets JSON: {e}"},
        )

    required_metadata = ["carrier", "insured_name", "property_address"]
    missing = [f for f in required_metadata if f not in metadata_dict]
    if missing:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "MISSING_FIELDS",
                "message": f"Missing required metadata fields: {missing}",
            },
        )

    required_costs = ["materials_cost", "labor_cost"]
    missing_costs = [f for f in required_costs if f not in costs_dict]
    if missing_costs:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "MISSING_FIELDS",
                "message": f"Missing required cost fields: {missing_costs}",
            },
        )

    pdf_content = await estimate_pdf.read()

    photo_contents = []
    for i, photo in enumerate(photos):
        content = await photo.read()
        photo_contents.append(
            {
                "photo_id": f"photo_{i:03d}",
                "filename": photo.filename,
                "content_type": photo.content_type or "image/jpeg",
                "size": len(content),
                "binary": content,
            }
        )

    job = await job_store.create(
        {
            "metadata": metadata_dict,
            "costs": costs_dict,
            "targets": targets_dict,
            "callback_url": callback_url,
            "pdf_filename": estimate_pdf.filename,
            "pdf_size": len(pdf_content),
            "photo_count": len(photos),
            "_pdf_binary": pdf_content,
            "_photos": photo_contents,
        }
    )

    background_tasks.add_task(process_job, job["job_id"])

    estimated_completion = datetime.utcnow() + timedelta(minutes=5)

    return JobCreatedResponse(
        job_id=job["job_id"],
        status="queued",
        created_at=job["created_at"],
        estimated_completion=estimated_completion.isoformat() + "Z",
        links={
            "self": f"/v1/jobs/{job['job_id']}",
            "status": f"/v1/jobs/{job['job_id']}",
            "report": f"/v1/jobs/{job['job_id']}/report",
        },
    )


async def process_job(job_id: str) -> None:
    from src.orchestrator.core import Orchestrator
    from src.schemas.job import (
        BusinessTargets,
        Costs,
        Job,
        JobMetadata,
        Photo,
    )

    logger.info(f"Starting to process job {job_id}")

    try:
        job_data = await job_store.get(job_id, include_binaries=True)
    except Exception as e:
        logger.exception(f"Failed to get job {job_id}: {e}")
        return

    if not job_data:
        logger.error(f"Job {job_id} not found for processing")
        return

    logger.info(
        f"Job {job_id} has {len(job_data.get('_photos', []))} photos and {len(job_data.get('_pdf_binary', b''))} byte PDF"
    )

    await job_store.update(job_id, {"status": "processing", "stage": "preparing"})

    try:
        photos = []
        for p in job_data.get("_photos", []):
            content_type = p.get("content_type", "image/jpeg")
            mime_map = {
                "image/jpeg": "image/jpeg",
                "image/jpg": "image/jpeg",
                "image/png": "image/png",
                "image/webp": "image/webp",
                "image/heic": "image/heic",
            }
            mime_type = mime_map.get(content_type, "image/jpeg")

            photos.append(
                Photo(
                    photo_id=p["photo_id"],
                    file_binary=p["binary"],
                    filename=p["filename"],
                    mime_type=mime_type,  # type: ignore
                )
            )

        metadata_raw = job_data.get("metadata", {})
        job = Job(
            job_id=job_id,
            metadata=JobMetadata(
                carrier=metadata_raw.get("carrier", ""),
                claim_number=metadata_raw.get("claim_number", ""),
                insured_name=metadata_raw.get("insured_name", ""),
                property_address=metadata_raw.get("property_address", ""),
                date_of_loss=metadata_raw.get("date_of_loss"),
                policy_number=metadata_raw.get("policy_number"),
                adjuster_name=metadata_raw.get("adjuster_name"),
                adjuster_email=metadata_raw.get("adjuster_email"),
                adjuster_phone=metadata_raw.get("adjuster_phone"),
            ),
            insurance_estimate=job_data.get("_pdf_binary", b""),
            photos=photos,
            costs=Costs(**job_data.get("costs", {})),
            business_targets=BusinessTargets(**job_data.get("targets", {})),
        )

        await job_store.update(job_id, {"stage": "running_agents"})

        orchestrator = Orchestrator(job)
        result = await orchestrator.run()

        supplement_total = 0.0
        supplement_count = 0
        if result.supplements:
            supplement_count = len(result.supplements.supplements)
            supplement_total = sum(
                s.estimated_value for s in result.supplements.supplements
            )

        human_flags_data = None
        if result.human_flags:
            human_flags_data = [f.model_dump() for f in result.human_flags]

        await job_store.update(
            job_id,
            {
                "status": result.status.value,
                "stage": "completed" if result.success else "escalated",
                "completed_at": datetime.utcnow().isoformat() + "Z",
                "results": {
                    "supplement_total": supplement_total,
                    "supplement_count": supplement_count,
                    "processing_time_seconds": result.processing_time_seconds,
                    "llm_calls": result.llm_calls,
                    "review_cycles": result.review_cycles,
                },
                "_report_html": result.report_html,
                "_report_pdf": result.report_pdf,
                "escalation_reason": result.escalation_reason,
                "human_flags": human_flags_data,
            },
        )

        logger.info(f"Job {job_id} completed with status {result.status.value}")

    except Exception as e:
        logger.exception(f"Job {job_id} failed with error: {e}")
        await job_store.update(
            job_id,
            {
                "status": "failed",
                "stage": "error",
                "error": str(e),
                "completed_at": datetime.utcnow().isoformat() + "Z",
            },
        )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job(
    job_id: str,
    include: list[str] | None = Query(
        None, description="Include: evidence, gaps, supplements, review"
    ),
) -> JobStatusResponse:
    job = await job_store.get(job_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail={"code": "JOB_NOT_FOUND", "message": "Job not found"},
        )

    return JobStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        stage=job.get("stage"),
        created_at=job["created_at"],
        updated_at=job.get("updated_at"),
        completed_at=job.get("completed_at"),
        results=job.get("results"),
        escalation_reason=job.get("escalation_reason"),
        human_flags=job.get("human_flags"),
        error=job.get("error"),
        links={
            "self": f"/v1/jobs/{job_id}",
            "report": f"/v1/jobs/{job_id}/report",
        },
    )


@router.get("/jobs/{job_id}/report")
async def download_report(
    job_id: str,
    format: str = Query("pdf", pattern="^(pdf|html)$"),
) -> Response:
    job = await job_store.get(job_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail={"code": "JOB_NOT_FOUND", "message": "Job not found"},
        )

    if job["status"] != "completed":
        raise HTTPException(
            status_code=404,
            detail={"code": "REPORT_NOT_READY", "message": "Report not yet generated"},
        )

    if format == "pdf":
        pdf_binary = job.get("_report_pdf")
        if not pdf_binary:
            raise HTTPException(
                status_code=404,
                detail={"code": "REPORT_NOT_READY", "message": "PDF not available"},
            )

        return Response(
            content=pdf_binary,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="supplement_report_{job_id}.pdf"'
            },
        )
    else:
        html = job.get("_report_html", "")
        if not html:
            raise HTTPException(
                status_code=404,
                detail={"code": "REPORT_NOT_READY", "message": "HTML not available"},
            )
        return Response(content=html, media_type="text/html")


@router.post("/jobs/{job_id}/approve")
async def approve_job(job_id: str, request: ApproveRequest) -> dict[str, Any]:
    job = await job_store.get(job_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail={"code": "JOB_NOT_FOUND", "message": "Job not found"},
        )

    if job["status"] != "escalated":
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_STATE",
                "message": "Job is not in escalated state",
            },
        )

    await job_store.update(
        job_id,
        {
            "status": "approved",
            "approved_by": request.approved_by,
            "approved_at": datetime.utcnow().isoformat() + "Z",
            "approval_notes": request.notes,
        },
    )

    return {
        "job_id": job_id,
        "status": "approved",
        "message": "Job approved for delivery",
    }


@router.post("/jobs/{job_id}/reject")
async def reject_job(job_id: str, request: RejectRequest) -> dict[str, Any]:
    job = await job_store.get(job_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail={"code": "JOB_NOT_FOUND", "message": "Job not found"},
        )

    if job["status"] != "escalated":
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_STATE",
                "message": "Job is not in escalated state",
            },
        )

    await job_store.update(
        job_id,
        {
            "status": "rejected",
            "rejected_by": request.rejected_by,
            "rejected_at": datetime.utcnow().isoformat() + "Z",
            "rejection_reason": request.reason,
        },
    )

    return {"job_id": job_id, "status": "rejected"}


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    status: str | None = Query(None, description="Filter by status"),
    carrier: str | None = Query(None, description="Filter by carrier"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> JobListResponse:
    jobs = await job_store.list_jobs(
        status=status, carrier=carrier, limit=limit, offset=offset
    )
    total = await job_store.count(status=status)

    job_summaries = [
        JobSummary(
            job_id=j["job_id"],
            status=j["status"],
            carrier=j.get("metadata", {}).get("carrier"),
            created_at=j["created_at"],
            completed_at=j.get("completed_at"),
        )
        for j in jobs
    ]

    return JobListResponse(
        jobs=job_summaries,
        pagination=PaginationInfo(
            limit=limit,
            offset=offset,
            total=total,
        ),
    )


@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str) -> dict[str, Any]:
    job = await job_store.get(job_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail={"code": "JOB_NOT_FOUND", "message": "Job not found"},
        )

    if job["status"] in ["completed", "failed"]:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "CANNOT_CANCEL",
                "message": "Cannot cancel completed/failed job",
            },
        )

    await job_store.update(
        job_id,
        {
            "status": "cancelled",
            "cancelled_at": datetime.utcnow().isoformat() + "Z",
        },
    )

    return {"job_id": job_id, "status": "cancelled"}
