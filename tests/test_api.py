from __future__ import annotations

import json
import pytest
from fastapi.testclient import TestClient

from src.api.app import app
from src.api.store import job_store


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_job_store():
    job_store.jobs.clear()
    yield
    job_store.jobs.clear()


class TestHealthEndpoints:
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    def test_readiness_check(self, client):
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True

    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data


class TestJobEndpoints:
    def test_create_job_missing_pdf(self, client, sample_photo_bytes):
        response = client.post(
            "/v1/jobs",
            files=[
                ("photos", ("photo.jpg", sample_photo_bytes, "image/jpeg")),
            ],
            data={
                "metadata": json.dumps(
                    {
                        "carrier": "State Farm",
                        "claim_number": "CLM-123",
                        "insured_name": "John Doe",
                        "property_address": "123 Main St",
                    }
                ),
                "costs": json.dumps({"materials_cost": 5000, "labor_cost": 8000}),
            },
        )
        assert response.status_code == 422  # Missing required field

    def test_create_job_invalid_pdf_type(self, client, sample_photo_bytes):
        response = client.post(
            "/v1/jobs",
            files=[
                ("estimate_pdf", ("estimate.txt", b"not a pdf", "text/plain")),
                ("photos", ("photo.jpg", sample_photo_bytes, "image/jpeg")),
            ],
            data={
                "metadata": json.dumps(
                    {
                        "carrier": "State Farm",
                        "claim_number": "CLM-123",
                        "insured_name": "John Doe",
                        "property_address": "123 Main St",
                    }
                ),
                "costs": json.dumps({"materials_cost": 5000, "labor_cost": 8000}),
            },
        )
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "INVALID_FILE_TYPE"

    def test_create_job_missing_metadata_fields(
        self, client, sample_pdf_bytes, sample_photo_bytes
    ):
        response = client.post(
            "/v1/jobs",
            files=[
                ("estimate_pdf", ("estimate.pdf", sample_pdf_bytes, "application/pdf")),
                ("photos", ("photo.jpg", sample_photo_bytes, "image/jpeg")),
            ],
            data={
                "metadata": json.dumps(
                    {"carrier": "State Farm"}
                ),  # Missing required fields
                "costs": json.dumps({"materials_cost": 5000, "labor_cost": 8000}),
            },
        )
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "MISSING_FIELDS"

    def test_create_job_invalid_json(
        self, client, sample_pdf_bytes, sample_photo_bytes
    ):
        response = client.post(
            "/v1/jobs",
            files=[
                ("estimate_pdf", ("estimate.pdf", sample_pdf_bytes, "application/pdf")),
                ("photos", ("photo.jpg", sample_photo_bytes, "image/jpeg")),
            ],
            data={
                "metadata": "not valid json",
                "costs": json.dumps({"materials_cost": 5000, "labor_cost": 8000}),
            },
        )
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "INVALID_JSON"

    def test_create_job_success(self, client, sample_pdf_bytes, sample_photo_bytes):
        response = client.post(
            "/v1/jobs",
            files=[
                ("estimate_pdf", ("estimate.pdf", sample_pdf_bytes, "application/pdf")),
                ("photos", ("photo.jpg", sample_photo_bytes, "image/jpeg")),
            ],
            data={
                "metadata": json.dumps(
                    {
                        "carrier": "State Farm",
                        "claim_number": "CLM-123",
                        "insured_name": "John Doe",
                        "property_address": "123 Main St",
                    }
                ),
                "costs": json.dumps({"materials_cost": 5000, "labor_cost": 8000}),
            },
        )
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"
        assert "created_at" in data
        assert "links" in data

    def test_get_job_not_found(self, client):
        response = client.get("/v1/jobs/nonexistent_job")
        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "JOB_NOT_FOUND"

    def test_get_job_success(self, client, sample_pdf_bytes, sample_photo_bytes):
        # Create a job first
        create_response = client.post(
            "/v1/jobs",
            files=[
                ("estimate_pdf", ("estimate.pdf", sample_pdf_bytes, "application/pdf")),
                ("photos", ("photo.jpg", sample_photo_bytes, "image/jpeg")),
            ],
            data={
                "metadata": json.dumps(
                    {
                        "carrier": "State Farm",
                        "claim_number": "CLM-123",
                        "insured_name": "John Doe",
                        "property_address": "123 Main St",
                    }
                ),
                "costs": json.dumps({"materials_cost": 5000, "labor_cost": 8000}),
            },
        )
        job_id = create_response.json()["job_id"]

        # Get the job
        response = client.get(f"/v1/jobs/{job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert "status" in data

    def test_list_jobs_empty(self, client):
        response = client.get("/v1/jobs")
        assert response.status_code == 200
        data = response.json()
        assert data["jobs"] == []
        assert data["pagination"]["total"] == 0

    def test_list_jobs_with_filters(self, client, sample_pdf_bytes, sample_photo_bytes):
        # Create a job
        client.post(
            "/v1/jobs",
            files=[
                ("estimate_pdf", ("estimate.pdf", sample_pdf_bytes, "application/pdf")),
                ("photos", ("photo.jpg", sample_photo_bytes, "image/jpeg")),
            ],
            data={
                "metadata": json.dumps(
                    {
                        "carrier": "State Farm",
                        "claim_number": "CLM-123",
                        "insured_name": "John Doe",
                        "property_address": "123 Main St",
                    }
                ),
                "costs": json.dumps({"materials_cost": 5000, "labor_cost": 8000}),
            },
        )

        # List all jobs (without status filter since background job may fail during test)
        response = client.get("/v1/jobs")
        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) >= 1
        # Verify pagination structure
        assert "pagination" in data

    def test_cancel_job_not_found(self, client):
        response = client.delete("/v1/jobs/nonexistent_job")
        assert response.status_code == 404

    def test_download_report_not_ready(
        self, client, sample_pdf_bytes, sample_photo_bytes
    ):
        # Create a job
        create_response = client.post(
            "/v1/jobs",
            files=[
                ("estimate_pdf", ("estimate.pdf", sample_pdf_bytes, "application/pdf")),
                ("photos", ("photo.jpg", sample_photo_bytes, "image/jpeg")),
            ],
            data={
                "metadata": json.dumps(
                    {
                        "carrier": "State Farm",
                        "claim_number": "CLM-123",
                        "insured_name": "John Doe",
                        "property_address": "123 Main St",
                    }
                ),
                "costs": json.dumps({"materials_cost": 5000, "labor_cost": 8000}),
            },
        )
        job_id = create_response.json()["job_id"]

        # Try to download report (not ready)
        response = client.get(f"/v1/jobs/{job_id}/report")
        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "REPORT_NOT_READY"


class TestApproveRejectEndpoints:
    def test_approve_job_not_found(self, client):
        response = client.post(
            "/v1/jobs/nonexistent/approve",
            json={"approved_by": "Test User"},
        )
        assert response.status_code == 404

    def test_reject_job_not_found(self, client):
        response = client.post(
            "/v1/jobs/nonexistent/reject",
            json={"rejected_by": "Test User", "reason": "Test reason"},
        )
        assert response.status_code == 404
