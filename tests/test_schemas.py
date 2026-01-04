from __future__ import annotations


from src.schemas.job import (
    JobMetadata,
    Photo,
    BusinessTargets,
)
from src.schemas.evidence import (
    VisionEvidence,
    Component,
    EstimatedArea,
    BoundingBox,
    GlobalObservation,
)
from src.schemas.estimate import (
    EstimateInterpretation,
    EstimateSummary,
    LineItem,
    Financials,
    ActualCosts,
)
from src.schemas.gaps import (
    GapAnalysis,
    ScopeGap,
    CoverageSummary,
)
from src.schemas.supplements import (
    SupplementProposal,
    MarginAnalysis,
)
from src.schemas.review import (
    ReviewResult,
    RerunRequest,
    Adjustment,
    HumanFlag,
    MarginAssessment,
    CarrierRiskAssessment,
)


class TestJobSchemas:
    def test_job_metadata_required_fields(self):
        metadata = JobMetadata(
            carrier="State Farm",
            claim_number="CLM-123",
            insured_name="John Doe",
            property_address="123 Main St",
        )
        assert metadata.carrier == "State Farm"
        assert metadata.claim_number == "CLM-123"

    def test_job_metadata_optional_fields(self):
        metadata = JobMetadata(
            carrier="Allstate",
            claim_number="CLM-456",
            insured_name="Jane Doe",
            property_address="456 Oak Ave",
            date_of_loss="2024-01-15",
            adjuster_name="Bob Smith",
        )
        assert metadata.date_of_loss == "2024-01-15"
        assert metadata.adjuster_name == "Bob Smith"
        assert metadata.policy_number is None

    def test_costs_total_property(self, sample_costs):
        assert sample_costs.total == 13500.0

    def test_business_targets_default(self):
        targets = BusinessTargets()
        assert targets.minimum_margin == 0.33

    def test_photo_valid_mime_types(self, sample_photo_bytes):
        for mime in ["image/jpeg", "image/png", "image/webp", "image/heic"]:
            photo = Photo(
                photo_id="test",
                file_binary=sample_photo_bytes,
                filename="test.jpg",
                mime_type=mime,
            )
            assert photo.mime_type == mime

    def test_job_creation(self, sample_job):
        assert sample_job.job_id == "job_test_001"
        assert len(sample_job.photos) == 1
        assert sample_job.costs.total == 13500.0


class TestEvidenceSchemas:
    def test_bounding_box_normalized(self):
        bbox = BoundingBox(x=0.1, y=0.2, width=0.5, height=0.3)
        assert bbox.x == 0.1
        assert bbox.width == 0.5

    def test_estimated_area(self):
        area = EstimatedArea(
            value=25.0,
            unit="sq_ft",
            confidence=0.85,
            method="reference_object",
        )
        assert area.value == 25.0
        assert area.unit == "sq_ft"

    def test_component_with_all_fields(self):
        component = Component(
            component_type="shingle",
            location_hint="north slope near ridge",
            condition="damaged_moderate",
            description="Cracked shingles visible",
            estimated_area=EstimatedArea(
                value=15.0, unit="sq_ft", confidence=0.8, method="model_estimate"
            ),
            severity_score=0.6,
            detection_confidence=0.92,
            bbox=BoundingBox(x=0.2, y=0.3, width=0.4, height=0.3),
        )
        assert component.component_type == "shingle"
        assert component.severity_score == 0.6

    def test_vision_evidence(self):
        evidence = VisionEvidence(
            photo_id="photo_001",
            components=[],
            global_observations=[
                GlobalObservation(
                    type="storm_damage_pattern",
                    description="Hail impact visible",
                    confidence=0.85,
                )
            ],
        )
        assert evidence.photo_id == "photo_001"
        assert len(evidence.global_observations) == 1


class TestEstimateSchemas:
    def test_line_item(self):
        item = LineItem(
            line_id="LI-001",
            description="Remove and replace shingles",
            scope_category="roofing_installation",
            quantity=25.0,
            unit="SQ",
            unit_price=350.0,
            total=8750.0,
            is_roofing_core=True,
        )
        assert item.total == 8750.0
        assert item.is_roofing_core is True

    def test_financials_margin_calculation(self):
        financials = Financials(
            original_estimate_total=15000.0,
            actual_costs=ActualCosts(
                materials=5000.0, labor=8000.0, other=500.0, total=13500.0
            ),
            current_margin=0.10,
            target_margin=0.33,
            margin_gap=0.23,
        )
        assert financials.margin_gap == 0.23

    def test_estimate_interpretation(self):
        interp = EstimateInterpretation(
            estimate_summary=EstimateSummary(
                carrier="State Farm",
                claim_number="CLM-123",
                total_estimate_amount=15000.0,
                roof_related_total=14500.0,
                overhead_and_profit_included=True,
            ),
            line_items=[],
            financials=Financials(
                original_estimate_total=15000.0,
                actual_costs=ActualCosts(
                    materials=5000.0, labor=8000.0, other=0.0, total=13000.0
                ),
                current_margin=0.133,
                target_margin=0.33,
                margin_gap=0.197,
            ),
            parsing_confidence=0.95,
        )
        assert interp.parsing_confidence == 0.95


class TestGapSchemas:
    def test_scope_gap(self):
        gap = ScopeGap(
            gap_id="GAP-001",
            category="missing_line_item",
            severity="critical",
            description="Starter strip not included",
            linked_photos=["photo_001"],
            confidence=0.95,
            unpaid_work_risk=True,
        )
        assert gap.severity == "critical"
        assert gap.unpaid_work_risk is True

    def test_coverage_summary(self):
        summary = CoverageSummary(
            critical_gaps=2,
            major_gaps=3,
            minor_gaps=1,
            total_unpaid_risk_items=4,
            narrative="Found 6 total gaps",
        )
        assert summary.critical_gaps == 2

    def test_gap_analysis(self):
        analysis = GapAnalysis(
            scope_gaps=[],
            coverage_summary=CoverageSummary(
                critical_gaps=0,
                major_gaps=0,
                minor_gaps=0,
                total_unpaid_risk_items=0,
                narrative="No gaps found",
            ),
        )
        assert len(analysis.scope_gaps) == 0


class TestSupplementSchemas:
    def test_supplement_proposal(self):
        proposal = SupplementProposal(
            supplement_id="SUP-001",
            type="new_line_item",
            line_item_description="Starter strip shingles",
            justification="Required per manufacturer specs",
            source="code_requirement",
            quantity=180.0,
            unit="LF",
            estimated_unit_price=1.25,
            estimated_value=225.0,
            confidence=0.92,
            pushback_risk="low",
            priority="critical",
        )
        assert proposal.estimated_value == 225.0
        assert proposal.pushback_risk == "low"

    def test_margin_analysis(self):
        margin = MarginAnalysis(
            original_estimate=15000.0,
            total_costs=13500.0,
            current_margin=0.10,
            proposed_supplement_total=2500.0,
            new_estimate_total=17500.0,
            projected_margin=0.229,
            target_margin=0.33,
            margin_gap_remaining=0.101,
            target_achieved=False,
        )
        assert margin.target_achieved is False


class TestReviewSchemas:
    def test_rerun_request(self):
        rerun = RerunRequest(
            request_id="RERUN-001",
            target_agent="supplement_agent",
            priority="high",
            reason="Quantities need adjustment",
            instructions="Review photo evidence for accurate quantities",
        )
        assert rerun.target_agent == "supplement_agent"

    def test_adjustment(self):
        adj = Adjustment(
            request_id="ADJ-001",
            target_type="supplement",
            target_id="SUP-003",
            field="quantity",
            current_value=10.0,
            suggested_value=12.0,
            reason="Photo shows 12 pieces needed",
        )
        assert adj.suggested_value == 12.0

    def test_human_flag(self):
        flag = HumanFlag(
            flag_id="FLAG-001",
            severity="warning",
            reason="Unusual damage pattern",
            context="May require expert review",
            recommended_action="Have senior adjuster review",
        )
        assert flag.severity == "warning"

    def test_review_result_approved(self):
        result = ReviewResult(
            approved=True,
            overall_assessment="Package is complete",
            reruns_requested=[],
            adjustments_requested=[],
            human_flags=[],
            margin_assessment=MarginAssessment(
                target=0.33, projected=0.30, acceptable=True
            ),
            carrier_risk_assessment=CarrierRiskAssessment(
                overall_risk="low", high_risk_items=[]
            ),
            ready_for_delivery=True,
        )
        assert result.approved is True
        assert result.ready_for_delivery is True
