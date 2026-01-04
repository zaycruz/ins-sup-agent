from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    @pytest.fixture
    def client(self):
        with patch("src.api.app.init_db", new_callable=AsyncMock):
            with patch("src.api.app.close_pool", new_callable=AsyncMock):
                from src.api.app import app

                return TestClient(app)

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
    @pytest.fixture
    def client(self):
        with patch("src.api.app.init_db", new_callable=AsyncMock):
            with patch("src.api.app.close_pool", new_callable=AsyncMock):
                from src.api.app import app

                return TestClient(app)

    @pytest.fixture
    def sample_photo_bytes(self) -> bytes:
        return b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"

    @pytest.fixture
    def sample_pdf_bytes(self) -> bytes:
        return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"

    @pytest.fixture
    def valid_metadata(self) -> str:
        return json.dumps(
            {
                "carrier": "State Farm",
                "insured_name": "John Doe",
                "property_address": "123 Main St, Dallas, TX 75201",
            }
        )

    @pytest.fixture
    def valid_costs(self) -> str:
        return json.dumps(
            {
                "materials_cost": 5000.00,
                "labor_cost": 8000.00,
                "other_costs": 500.00,
            }
        )

    def test_create_job_missing_pdf(self, client, sample_photo_bytes):
        response = client.post(
            "/v1/jobs",
            files=[
                ("photos", ("photo.jpg", sample_photo_bytes, "image/jpeg")),
            ],
            data={
                "metadata": json.dumps({"carrier": "State Farm"}),
                "costs": json.dumps({"materials_cost": 5000}),
            },
        )
        assert response.status_code == 422

    def test_create_job_invalid_pdf_type(
        self, client, sample_photo_bytes, valid_metadata, valid_costs
    ):
        response = client.post(
            "/v1/jobs",
            files=[
                ("estimate_pdf", ("estimate.txt", b"not a pdf", "text/plain")),
                ("photos", ("photo.jpg", sample_photo_bytes, "image/jpeg")),
            ],
            data={
                "metadata": valid_metadata,
                "costs": valid_costs,
            },
        )
        assert response.status_code == 400
        assert "INVALID_FILE_TYPE" in response.text

    def test_create_job_missing_metadata_fields(
        self, client, sample_pdf_bytes, sample_photo_bytes, valid_costs
    ):
        response = client.post(
            "/v1/jobs",
            files=[
                ("estimate_pdf", ("estimate.pdf", sample_pdf_bytes, "application/pdf")),
                ("photos", ("photo.jpg", sample_photo_bytes, "image/jpeg")),
            ],
            data={
                "metadata": json.dumps({"carrier": "State Farm"}),
                "costs": valid_costs,
            },
        )
        assert response.status_code == 400
        assert "MISSING_FIELDS" in response.text

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
                "costs": json.dumps({"materials_cost": 5000}),
            },
        )
        assert response.status_code == 400
        assert "INVALID_JSON" in response.text

    @pytest.mark.skip(reason="Requires database connection - test in integration")
    def test_create_job_success(
        self, client, sample_pdf_bytes, sample_photo_bytes, valid_metadata, valid_costs
    ):
        pass

    @patch("src.api.store.JobStore.get")
    def test_get_job_not_found(self, mock_get, client):
        mock_get.return_value = None
        response = client.get(f"/v1/jobs/{uuid4()}")
        assert response.status_code == 404

    @patch("src.api.store.JobStore.get")
    def test_get_job_success(self, mock_get, client):
        job_id = str(uuid4())
        mock_get.return_value = {
            "job_id": job_id,
            "status": "processing",
            "metadata": {"carrier": "State Farm"},
            "created_at": "2024-01-01T00:00:00Z",
        }

        response = client.get(f"/v1/jobs/{job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id

    @patch("src.api.store.JobStore.list_jobs")
    @patch("src.api.store.JobStore.count")
    def test_list_jobs_empty(self, mock_count, mock_list, client):
        mock_list.return_value = []
        mock_count.return_value = 0

        response = client.get("/v1/jobs")
        assert response.status_code == 200
        data = response.json()
        assert data["jobs"] == []
        assert data["pagination"]["total"] == 0

    @patch("src.api.store.JobStore.list_jobs")
    @patch("src.api.store.JobStore.count")
    def test_list_jobs_with_filters(self, mock_count, mock_list, client):
        mock_list.return_value = []
        mock_count.return_value = 0

        response = client.get("/v1/jobs?status=completed&limit=10")
        assert response.status_code == 200
        mock_list.assert_called_once()

    @patch("src.api.store.JobStore.get")
    def test_cancel_job_not_found(self, mock_get, client):
        mock_get.return_value = None
        response = client.post(f"/v1/jobs/{uuid4()}/cancel")
        assert response.status_code == 404

    @pytest.mark.skip(reason="Requires database connection - test in integration")
    def test_download_report_not_ready(self, client):
        pass


class TestApproveRejectEndpoints:
    @pytest.fixture
    def client(self):
        with patch("src.api.app.init_db", new_callable=AsyncMock):
            with patch("src.api.app.close_pool", new_callable=AsyncMock):
                from src.api.app import app

                return TestClient(app)

    @patch("src.api.store.JobStore.get")
    def test_approve_job_not_found(self, mock_get, client):
        mock_get.return_value = None
        response = client.post(
            f"/v1/jobs/{uuid4()}/approve",
            json={"approved_by": "test_user"},
        )
        assert response.status_code == 404

    @patch("src.api.store.JobStore.get")
    def test_reject_job_not_found(self, mock_get, client):
        mock_get.return_value = None
        response = client.post(
            f"/v1/jobs/{uuid4()}/reject",
            json={"rejected_by": "test_user", "reason": "test reason"},
        )
        assert response.status_code == 404
