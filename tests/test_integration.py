from __future__ import annotations

import json
import pytest
from fastapi.testclient import TestClient
from typing import Literal

from src.api.app import app
from src.api.store import job_store
from src.orchestrator.core import JobStatus, Orchestrator
from src.schemas.job import (
    BusinessTargets,
    Costs,
    Job,
    JobMetadata,
    Photo,
)
from tests.conftest import TestLLMClient


@pytest.fixture
def integration_llm_client() -> TestLLMClient:
    return TestLLMClient(force_escalation=False)


@pytest.fixture
def escalation_llm_client() -> TestLLMClient:
    return TestLLMClient(force_escalation=True)


@pytest.fixture
def integration_job(
    sample_metadata, sample_costs, sample_photo, sample_pdf_bytes
) -> Job:
    return Job(
        job_id="integration_test_001",
        metadata=sample_metadata,
        insurance_estimate=sample_pdf_bytes,
        photos=[sample_photo],
        costs=sample_costs,
        business_targets=BusinessTargets(minimum_margin=0.33),
    )


@pytest.fixture
def multi_photo_job(
    sample_metadata, sample_costs, sample_pdf_bytes, sample_photo_bytes
) -> Job:
    view_types: list[Literal["overview", "close_up", "damage_detail"]] = [
        "overview",
        "close_up",
        "damage_detail",
    ]
    photos = [
        Photo(
            photo_id=f"photo_{i:03d}",
            file_binary=sample_photo_bytes,
            filename=f"roof_photo_{i}.jpg",
            mime_type="image/jpeg",
            view_type=view_types[i],
            notes=f"Test photo {i}",
        )
        for i in range(3)
    ]

    return Job(
        job_id="multi_photo_test_001",
        metadata=sample_metadata,
        insurance_estimate=sample_pdf_bytes,
        photos=photos,
        costs=sample_costs,
        business_targets=BusinessTargets(minimum_margin=0.33),
    )


@pytest.fixture
def api_client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_store():
    job_store.jobs.clear()
    yield
    job_store.jobs.clear()


class TestOrchestratorPipeline:
    @pytest.mark.asyncio
    async def test_full_pipeline_success(
        self, integration_job: Job, integration_llm_client: TestLLMClient
    ):
        orchestrator = Orchestrator(integration_job, integration_llm_client)
        result = await orchestrator.run()

        assert result.success is True
        assert result.status == JobStatus.COMPLETED
        assert result.job_id == integration_job.job_id

        assert result.report_html is not None
        assert len(result.report_html) > 0
        assert "Supplement Report" in result.report_html
        assert "CLM-12345" in result.report_html

        assert result.supplements is not None
        assert len(result.supplements.supplements) > 0
        assert result.supplements.margin_analysis is not None

        assert result.llm_calls > 0
        assert result.processing_time_seconds > 0

    @pytest.mark.asyncio
    async def test_pipeline_context_populated(
        self, integration_job: Job, integration_llm_client: TestLLMClient
    ):
        orchestrator = Orchestrator(integration_job, integration_llm_client)
        await orchestrator.run()

        ctx = orchestrator.context

        assert ctx.raw_estimate_text is not None
        assert len(ctx.raw_estimate_text) > 0

        assert ctx.job is not None
        assert ctx.job.job_id == integration_job.job_id

        assert ctx.vision_evidence is not None
        assert len(ctx.vision_evidence) == 1
        assert ctx.vision_evidence[0].photo_id is not None

        assert ctx.estimate_interpretation is not None
        assert ctx.estimate_interpretation.estimate_summary.carrier == "State Farm"
        assert len(ctx.estimate_interpretation.line_items) > 0

        assert ctx.gap_analysis is not None
        assert len(ctx.gap_analysis.scope_gaps) > 0
        assert ctx.gap_analysis.coverage_summary is not None

        assert ctx.supplement_strategy is not None
        assert len(ctx.supplement_strategy.supplements) > 0
        assert ctx.supplement_strategy.margin_analysis is not None

        assert ctx.review_result is not None
        assert ctx.review_cycle_count > 0

    @pytest.mark.asyncio
    async def test_multi_photo_processing(
        self, multi_photo_job: Job, integration_llm_client: TestLLMClient
    ):
        orchestrator = Orchestrator(multi_photo_job, integration_llm_client)
        result = await orchestrator.run()

        assert result.success is True

        ctx = orchestrator.context
        assert len(ctx.vision_evidence) == 3

        photo_ids = {ve.photo_id for ve in ctx.vision_evidence}
        assert len(photo_ids) == 3

    @pytest.mark.asyncio
    async def test_escalation_path(
        self, integration_job: Job, escalation_llm_client: TestLLMClient
    ):
        orchestrator = Orchestrator(integration_job, escalation_llm_client)
        result = await orchestrator.run()

        assert result.success is False
        assert result.status == JobStatus.ESCALATED

        assert result.escalation_reason is not None
        assert len(result.escalation_reason) > 0

        assert result.human_flags is not None
        assert len(result.human_flags) > 0
        assert any(flag.severity == "critical" for flag in result.human_flags)

        assert result.partial_results is not None
        assert "supplements" in result.partial_results

    @pytest.mark.asyncio
    async def test_vision_evidence_structure(
        self, integration_job: Job, integration_llm_client: TestLLMClient
    ):
        orchestrator = Orchestrator(integration_job, integration_llm_client)
        await orchestrator.run()

        evidence = orchestrator.context.vision_evidence[0]

        assert len(evidence.components) > 0
        component = evidence.components[0]
        assert component.component_type in [
            "shingle",
            "flashing",
            "ridge_cap",
            "valley",
            "vent",
            "pipe_boot",
            "skylight",
            "chimney",
            "gutter",
            "downspout",
            "fascia",
            "soffit",
            "drip_edge",
            "ice_water_shield",
            "underlayment",
            "decking",
            "satellite_dish_mount",
            "hvac_curb",
            "other",
        ]
        assert component.condition in [
            "damaged_severe",
            "damaged_moderate",
            "damaged_minor",
            "worn",
            "good",
            "new",
            "missing",
            "unknown",
        ]
        assert 0 <= component.severity_score <= 1
        assert 0 <= component.detection_confidence <= 1

        assert len(evidence.global_observations) > 0
        obs = evidence.global_observations[0]
        assert obs.type in [
            "overall_condition",
            "age_estimate",
            "material_type",
            "storm_damage_pattern",
            "water_damage",
            "structural_concern",
            "code_violation",
            "installation_defect",
            "wear_pattern",
            "environmental_factor",
            "other",
        ]

    @pytest.mark.asyncio
    async def test_supplement_proposals_structure(
        self, integration_job: Job, integration_llm_client: TestLLMClient
    ):
        orchestrator = Orchestrator(integration_job, integration_llm_client)
        await orchestrator.run()

        strategy = orchestrator.context.supplement_strategy
        assert strategy is not None

        assert len(strategy.supplements) > 0
        supp = strategy.supplements[0]

        assert supp.supplement_id is not None
        assert supp.type in [
            "new_line_item",
            "quantity_increase",
            "price_adjustment",
            "code_requirement",
            "material_upgrade",
            "additional_labor",
            "missed_component",
            "other",
        ]
        assert supp.pushback_risk in ["low", "medium", "high"]
        assert supp.priority in ["critical", "high", "medium", "low"]
        assert supp.quantity > 0
        assert supp.estimated_value > 0

        margin = strategy.margin_analysis
        assert margin.original_estimate > 0
        assert margin.total_costs > 0
        assert margin.proposed_supplement_total >= 0


class TestAPIFlow:
    def test_create_job_returns_job_id(
        self, api_client: TestClient, sample_pdf_bytes: bytes, sample_photo_bytes: bytes
    ):
        response = api_client.post(
            "/v1/jobs",
            files=[
                ("estimate_pdf", ("estimate.pdf", sample_pdf_bytes, "application/pdf")),
                ("photos", ("photo.jpg", sample_photo_bytes, "image/jpeg")),
            ],
            data={
                "metadata": json.dumps(
                    {
                        "carrier": "State Farm",
                        "claim_number": "CLM-API-TEST",
                        "insured_name": "API Test User",
                        "property_address": "456 Test Ave, Houston, TX 77001",
                    }
                ),
                "costs": json.dumps(
                    {
                        "materials_cost": 6000,
                        "labor_cost": 9000,
                    }
                ),
            },
        )

        assert response.status_code == 202
        data = response.json()

        assert "job_id" in data
        assert data["status"] == "queued"
        assert "created_at" in data
        assert "links" in data
        assert "self" in data["links"]

    def test_get_job_status(
        self, api_client: TestClient, sample_pdf_bytes: bytes, sample_photo_bytes: bytes
    ):
        create_response = api_client.post(
            "/v1/jobs",
            files=[
                ("estimate_pdf", ("estimate.pdf", sample_pdf_bytes, "application/pdf")),
                ("photos", ("photo.jpg", sample_photo_bytes, "image/jpeg")),
            ],
            data={
                "metadata": json.dumps(
                    {
                        "carrier": "Allstate",
                        "claim_number": "CLM-STATUS-TEST",
                        "insured_name": "Status Test User",
                        "property_address": "789 Status Blvd",
                    }
                ),
                "costs": json.dumps(
                    {
                        "materials_cost": 5500,
                        "labor_cost": 8500,
                    }
                ),
            },
        )

        job_id = create_response.json()["job_id"]

        get_response = api_client.get(f"/v1/jobs/{job_id}")

        assert get_response.status_code == 200
        data = get_response.json()

        assert data["job_id"] == job_id
        assert "status" in data
        assert "created_at" in data

    def test_list_jobs_includes_created_job(
        self, api_client: TestClient, sample_pdf_bytes: bytes, sample_photo_bytes: bytes
    ):
        api_client.post(
            "/v1/jobs",
            files=[
                ("estimate_pdf", ("estimate.pdf", sample_pdf_bytes, "application/pdf")),
                ("photos", ("photo.jpg", sample_photo_bytes, "image/jpeg")),
            ],
            data={
                "metadata": json.dumps(
                    {
                        "carrier": "USAA",
                        "claim_number": "CLM-LIST-TEST",
                        "insured_name": "List Test User",
                        "property_address": "111 List Lane",
                    }
                ),
                "costs": json.dumps(
                    {
                        "materials_cost": 5000,
                        "labor_cost": 8000,
                    }
                ),
            },
        )

        list_response = api_client.get("/v1/jobs")

        assert list_response.status_code == 200
        data = list_response.json()

        assert "jobs" in data
        assert len(data["jobs"]) >= 1
        assert "pagination" in data

    def test_job_metadata_validation(
        self, api_client: TestClient, sample_pdf_bytes: bytes, sample_photo_bytes: bytes
    ):
        response = api_client.post(
            "/v1/jobs",
            files=[
                ("estimate_pdf", ("estimate.pdf", sample_pdf_bytes, "application/pdf")),
                ("photos", ("photo.jpg", sample_photo_bytes, "image/jpeg")),
            ],
            data={
                "metadata": json.dumps(
                    {
                        "carrier": "State Farm",
                    }
                ),
                "costs": json.dumps(
                    {
                        "materials_cost": 5000,
                        "labor_cost": 8000,
                    }
                ),
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["code"] == "MISSING_FIELDS"

    def test_download_report_not_ready(
        self, api_client: TestClient, sample_pdf_bytes: bytes, sample_photo_bytes: bytes
    ):
        create_response = api_client.post(
            "/v1/jobs",
            files=[
                ("estimate_pdf", ("estimate.pdf", sample_pdf_bytes, "application/pdf")),
                ("photos", ("photo.jpg", sample_photo_bytes, "image/jpeg")),
            ],
            data={
                "metadata": json.dumps(
                    {
                        "carrier": "Liberty Mutual",
                        "claim_number": "CLM-REPORT-TEST",
                        "insured_name": "Report Test User",
                        "property_address": "222 Report Road",
                    }
                ),
                "costs": json.dumps(
                    {
                        "materials_cost": 5000,
                        "labor_cost": 8000,
                    }
                ),
            },
        )

        job_id = create_response.json()["job_id"]

        report_response = api_client.get(f"/v1/jobs/{job_id}/report")

        assert report_response.status_code == 404
        data = report_response.json()
        assert data["detail"]["code"] == "REPORT_NOT_READY"


class TestLLMClientResponses:
    @pytest.mark.asyncio
    async def test_vision_response_structure(self):
        client = TestLLMClient()
        response = await client.complete_vision(
            system="You are a vision evidence agent...",
            user="Analyze this photo. photo_id: test_photo_123",
            images=[b"fake_image_bytes"],
        )

        data = json.loads(response)

        assert "photo_id" in data
        assert "components" in data
        assert "global_observations" in data
        assert isinstance(data["components"], list)

    @pytest.mark.asyncio
    async def test_estimate_response_structure(self):
        client = TestLLMClient()
        response = await client.complete(
            system="You are an estimate interpreter agent...",
            user="Parse this estimate...",
        )

        data = json.loads(response)

        assert "estimate_summary" in data
        assert "line_items" in data
        assert "financials" in data
        assert "parsing_confidence" in data

    @pytest.mark.asyncio
    async def test_gap_analysis_response_structure(self):
        client = TestLLMClient()
        response = await client.complete(
            system="You are a roofing scope analysis specialist. GAP CATEGORIES...",
            user="Analyze gaps...",
        )

        data = json.loads(response)

        assert "scope_gaps" in data
        assert "coverage_summary" in data
        assert isinstance(data["scope_gaps"], list)

    @pytest.mark.asyncio
    async def test_strategist_response_structure(self):
        client = TestLLMClient()
        response = await client.complete(
            system="You are a supplement strategist agent...",
            user="Create strategy...",
        )

        data = json.loads(response)

        assert "supplements" in data
        assert "margin_analysis" in data
        assert isinstance(data["supplements"], list)

    @pytest.mark.asyncio
    async def test_review_approved_response(self):
        client = TestLLMClient(force_escalation=False)
        response = await client.complete(
            system="You are a senior supplement reviewer who acts as skeptical adjuster...",
            user="Review the package...",
        )

        data = json.loads(response)

        assert data["approved"] is True
        assert data["ready_for_delivery"] is True
        assert "margin_assessment" in data
        assert "carrier_risk_assessment" in data

    @pytest.mark.asyncio
    async def test_review_escalation_response(self):
        client = TestLLMClient(force_escalation=True)
        response = await client.complete(
            system="You are a senior supplement reviewer who acts as skeptical adjuster...",
            user="Review the package...",
        )

        data = json.loads(response)

        assert data["approved"] is False
        assert data["ready_for_delivery"] is False
        assert len(data["human_flags"]) > 0

    @pytest.mark.asyncio
    async def test_report_response_is_html(self):
        client = TestLLMClient()
        response = await client.complete(
            system="You are a report generator. Generate HTML...",
            user="Generate report...",
        )

        assert "<!DOCTYPE html>" in response
        assert "<html" in response
        assert "</html>" in response


class TestEdgeCases:
    @pytest.mark.asyncio
    async def test_job_with_no_photos(
        self, sample_metadata, sample_costs, sample_pdf_bytes, integration_llm_client
    ):
        job = Job(
            job_id="no_photos_test",
            metadata=sample_metadata,
            insurance_estimate=sample_pdf_bytes,
            photos=[],
            costs=sample_costs,
            business_targets=BusinessTargets(minimum_margin=0.33),
        )

        orchestrator = Orchestrator(job, integration_llm_client)
        result = await orchestrator.run()

        assert result.success is True
        assert orchestrator.context.vision_evidence == []

    @pytest.mark.asyncio
    async def test_processing_time_tracked(
        self, integration_job, integration_llm_client
    ):
        orchestrator = Orchestrator(integration_job, integration_llm_client)
        result = await orchestrator.run()

        assert result.processing_time_seconds > 0
        assert result.processing_time_seconds < 60

    @pytest.mark.asyncio
    async def test_llm_call_count_tracked(
        self, integration_job, integration_llm_client
    ):
        orchestrator = Orchestrator(integration_job, integration_llm_client)
        result = await orchestrator.run()

        assert result.llm_calls >= 5
