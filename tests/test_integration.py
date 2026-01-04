from __future__ import annotations

import pytest


pytestmark = pytest.mark.skip(reason="Integration tests require database and LLM setup")


class TestOrchestratorPipeline:
    def test_full_pipeline_success(self):
        pass

    def test_pipeline_context_populated(self):
        pass

    def test_multi_photo_processing(self):
        pass

    def test_escalation_path(self):
        pass

    def test_vision_evidence_structure(self):
        pass

    def test_supplement_proposals_structure(self):
        pass


class TestAPIFlow:
    def test_create_job_returns_job_id(self):
        pass

    def test_get_job_status(self):
        pass

    def test_list_jobs_includes_created_job(self):
        pass

    def test_job_metadata_validation(self):
        pass

    def test_download_report_not_ready(self):
        pass


class TestLLMClientResponses:
    def test_vision_response_structure(self):
        pass

    def test_estimate_response_structure(self):
        pass

    def test_gap_analysis_response_structure(self):
        pass

    def test_strategist_response_structure(self):
        pass

    def test_review_approved_response(self):
        pass

    def test_review_escalation_response(self):
        pass

    def test_report_response_is_html(self):
        pass


class TestEdgeCases:
    def test_job_with_no_photos(self):
        pass

    def test_processing_time_tracked(self):
        pass

    def test_llm_call_count_tracked(self):
        pass
