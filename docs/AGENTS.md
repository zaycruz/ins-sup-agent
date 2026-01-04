# Agent Documentation

Detailed documentation for each agent in the Insurance Supplementation Agent System.

## Overview

| Agent | Purpose | Input | Output |
|-------|---------|-------|--------|
| Vision | Analyze photos for components/damage | Photo bytes | VisionEvidence |
| Estimate | Parse insurance estimate PDF | PDF text + costs | EstimateInterpretation |
| Gap Analysis | Find coverage discrepancies | Vision + Estimate | GapAnalysis |
| Strategist | Create supplement proposals | Gaps + Evidence | SupplementStrategy |
| Review | Quality gate and refinement | All outputs | ReviewResult |
| Report | Generate carrier-ready docs | Strategy + Photos | HTML/PDF |

---

## Vision Evidence Agent

**Purpose**: Analyze roofing photographs to detect and document visible components, damage, and conditions.

### Configuration

```python
agent = VisionEvidenceAgent(llm_client)
agent.name = "vision_agent"
agent.version = "1.0.0"
```

### Input Context

```python
{
    "photo_id": "photo_001",
    "image_bytes": b"...",  # Raw image bytes
    "job_type": "storm_damage",
    "damage_type": "hail_and_wind",
    "roof_type": "asphalt_shingle",
    "roof_squares": 25.0,
    "additional_notes": "Focus on north slope"
}
```

### Output: VisionEvidence

```python
VisionEvidence(
    photo_id="photo_001",
    components=[
        Component(
            component_type="shingle",
            location_hint="north-facing slope near ridge",
            condition="damaged_moderate",
            description="Cracked and displaced shingles with exposed underlayment",
            estimated_area=EstimatedArea(value=15.0, unit="sq_ft", confidence=0.8),
            severity_score=0.6,
            detection_confidence=0.92,
            bbox=BoundingBox(x=0.2, y=0.3, width=0.4, height=0.3)
        )
    ],
    global_observations=[
        GlobalObservation(
            type="storm_damage_pattern",
            description="Consistent hail impact pattern across visible shingles",
            confidence=0.85
        )
    ]
)
```

### Component Types

| Type | Description |
|------|-------------|
| `shingle` | Roof shingles (3-tab, architectural, designer) |
| `ridge_cap` | Ridge cap shingles |
| `flashing` | Step, counter, valley, chimney, wall flashing |
| `decking` | Plywood or OSB sheathing |
| `underlayment` | Felt or synthetic underlayment |
| `drip_edge` | Metal drip edge |
| `vent` | Box, ridge, turbine, power vents |
| `pipe_boot` | Lead, rubber, or plastic pipe boots |
| `chimney` | Chimney structure |
| `skylight` | Skylights |
| `gutter` | Gutters |
| `valley` | Open, closed, or woven valleys |

### Condition Levels

| Condition | Severity Score Range |
|-----------|---------------------|
| `intact` | 0.0 - 0.1 |
| `minor_damage` | 0.1 - 0.3 |
| `moderate_damage` | 0.3 - 0.6 |
| `severe_damage` | 0.6 - 0.8 |
| `missing` | 0.8 - 1.0 |

---

## Estimate Interpreter Agent

**Purpose**: Parse raw insurance estimate text into structured line items and compute financial metrics.

### Configuration

```python
agent = EstimateInterpreterAgent(llm_client)
agent.name = "estimate_agent"
agent.version = "1.0.0"
```

### Input Context

```python
{
    "estimate_text": "... extracted PDF text ...",
    "carrier": "State Farm",
    "claim_number": "CLM-12345",
    "materials_cost": 5000.0,
    "labor_cost": 8000.0,
    "other_costs": 500.0,
    "target_margin": 33.0
}
```

### Output: EstimateInterpretation

```python
EstimateInterpretation(
    estimate_summary=EstimateSummary(
        carrier="State Farm",
        claim_number="CLM-12345",
        total_estimate_amount=15000.0,
        roof_related_total=14500.0,
        overhead_and_profit_included=True,
        depreciation_amount=2500.0
    ),
    line_items=[
        LineItem(
            line_id="LI-001",
            description="Remove & replace - Shingles - 3 tab",
            scope_category="roofing_installation",
            quantity=25.0,
            unit="SQ",
            unit_price=350.0,
            total=8750.0,
            is_roofing_core=True,
            is_code_item=False,
            is_oversight_risk=False,
            raw_line_text="25 SQ - R&R Shingles 3-tab @350.00 = $8,750.00"
        )
    ],
    financials=Financials(
        original_estimate_total=15000.0,
        actual_costs=ActualCosts(materials=5000, labor=8000, other=500, total=13500),
        current_margin=0.10,
        target_margin=0.33,
        margin_gap=0.23
    ),
    parsing_confidence=0.95
)
```

### Scope Categories

| Category | Examples |
|----------|----------|
| `roofing_removal` | Tear-off, disposal, dumpster |
| `roofing_installation` | Shingle install, labor |
| `flashing` | Step, counter, valley flashing |
| `ventilation` | Ridge vents, box vents |
| `underlayment` | Felt, synthetic underlayment |
| `code_upgrade` | Code-required items |
| `overhead_profit` | O&P line items |

---

## Gap Analysis Agent

**Purpose**: Cross-reference visual evidence against estimate line items to identify unpaid or under-scoped work.

### Configuration

```python
agent = GapAnalysisAgent(llm_client)
agent.name = "gap_agent"
agent.version = "1.0.0"
```

### Input Context

```python
{
    "vision_evidence": [...],  # List of VisionEvidence dicts
    "estimate_interpretation": {...},  # EstimateInterpretation dict
    "roof_squares": 25.0,
    "jurisdiction": "TX"
}
```

### Output: GapAnalysis

```python
GapAnalysis(
    scope_gaps=[
        ScopeGap(
            gap_id="GAP-001",
            category="missing_line_item",
            severity="CRITICAL",
            description="Starter strip not included in estimate",
            linked_photos=["photo_001", "photo_003"],
            linked_estimate_lines=[],
            confidence=0.95,
            unpaid_work_risk=True,
            notes="Required per manufacturer specs"
        )
    ],
    coverage_summary=CoverageSummary(
        critical_gaps=2,
        major_gaps=3,
        minor_gaps=1,
        total_unpaid_risk_items=4,
        narrative="Found 6 gaps including 2 critical..."
    )
)
```

### Gap Categories

| Category | Description |
|----------|-------------|
| `missing_core_scope` | Essential roofing work not included |
| `insufficient_quantity` | Line item quantity too low |
| `hidden_damage` | Damage visible but not covered |
| `code_compliance` | Code-required items missing |
| `safety_related` | Safety-critical items omitted |
| `material_mismatch` | Wrong materials specified |
| `accessory_items` | Supporting items omitted |

---

## Supplement Strategist Agent

**Purpose**: Convert identified gaps into defensible supplement proposals with code citations and justifications.

### Configuration

```python
agent = SupplementStrategistAgent(llm_client)
agent.name = "supplement_agent"
agent.version = "1.0.0"
```

### Tools Available

#### lookup_building_code

```python
{
    "type": "function",
    "function": {
        "name": "lookup_building_code",
        "description": "Look up building code requirements",
        "parameters": {
            "jurisdiction": "TX",
            "topic": "ice_barrier"
        }
    }
}
```

#### retrieve_examples

```python
{
    "type": "function",
    "function": {
        "name": "retrieve_examples",
        "description": "Retrieve approved supplement examples",
        "parameters": {
            "query": "starter strip",
            "carrier": "State Farm",
            "limit": 3
        }
    }
}
```

### Input Context

```python
{
    "gap_analysis": {...},
    "estimate_interpretation": {...},
    "vision_evidence": [...],
    "target_margin": 0.33,
    "carrier": "State Farm",
    "jurisdiction": "TX"
}
```

### Output: SupplementStrategy

```python
SupplementStrategy(
    supplements=[
        SupplementProposal(
            supplement_id="SUP-001",
            type="missing_line_item",
            line_item_description="Starter strip shingles - eaves and rakes",
            justification="Starter strip required per manufacturer installation...",
            source="code_requirement",
            linked_gaps=["GAP-001"],
            linked_photos=["photo_001"],
            code_citation="IRC R905.2",
            quantity=180.0,
            unit="LF",
            estimated_unit_price=1.25,
            estimated_value=225.0,
            confidence=0.92,
            pushback_risk="LOW",
            priority="critical"
        )
    ],
    margin_analysis=MarginAnalysis(
        original_estimate=15000.0,
        total_costs=13500.0,
        current_margin=0.10,
        proposed_supplement_total=2450.0,
        new_estimate_total=17450.0,
        projected_margin=0.226,
        target_margin=0.33,
        margin_gap_remaining=0.104,
        target_achieved=False
    ),
    strategy_notes=["Focus on code-backed items first..."]
)
```

---

## Review Agent

**Purpose**: Act as skeptical adjuster AND profit-aware advisor to quality-gate the supplement package.

### Configuration

```python
agent = ReviewAgent(llm_client)
agent.name = "review_agent"
agent.version = "1.0.0"
```

### Input Context

```python
{
    "supplement_strategy": {...},
    "gap_analysis": {...},
    "estimate_interpretation": {...},
    "vision_evidence": [...],
    "target_margin": 0.33,
    "iteration": 1,
    "max_iterations": 2
}
```

### Output: ReviewResult

```python
ReviewResult(
    approved=True,
    overall_assessment="Package is complete and defensible...",
    reruns_requested=[],
    adjustments_requested=[
        Adjustment(
            request_id="ADJ-001",
            target_type="supplement",
            target_id="SUP-003",
            field="quantity",
            current_value=10.0,
            suggested_value=12.0,
            reason="Photo evidence shows 12 pieces needed"
        )
    ],
    human_flags=[],
    margin_assessment=MarginAssessment(
        target=0.33,
        projected=0.28,
        acceptable=True,
        notes="Within acceptable range"
    ),
    carrier_risk_assessment=CarrierRiskAssessment(
        overall_risk="LOW",
        high_risk_items=[],
        notes="All supplements well-supported"
    ),
    ready_for_delivery=True
)
```

### Decision Matrix

| Condition | Action |
|-----------|--------|
| All checks pass | `approved=True, ready=True` |
| Minor issues | `approved=True, ready=False, human_flags` |
| Needs refinement | `approved=False, reruns/adjustments` |
| Unresolvable | `approved=False, human_flags` |

---

## Report Generator Agent

**Purpose**: Generate professional HTML reports suitable for carrier submission.

### Configuration

```python
agent = ReportGeneratorAgent(llm_client)
agent.name = "report_agent"
agent.version = "1.0.0"
```

### Tools Available

#### render_pdf

```python
{
    "type": "function",
    "function": {
        "name": "render_pdf",
        "description": "Render HTML to PDF",
        "parameters": {
            "html_content": "<html>...",
            "options": {"page_size": "letter"}
        }
    }
}
```

### Input Context

```python
{
    "supplement_strategy": {...},
    "estimate_interpretation": {...},
    "vision_evidence": [...],
    "job_metadata": {...},
    "photo_data": [{"photo_id": "...", "base64": "..."}],
    "render_pdf": True
}
```

### Output: ReportOutput

```python
ReportOutput(
    html_content="<!DOCTYPE html>...",
    pdf_bytes=b"..."  # Optional
)
```

### Report Sections

1. **Cover Page**: Claim info, contractor branding
2. **Executive Summary**: Financial overview, key findings
3. **Supplement Details**: Line items grouped by category
4. **Photo Evidence**: Images with captions
5. **Appendix**: Code citations, terms

---

## Agent Lifecycle

```python
# 1. Initialize with LLM client
agent = VisionEvidenceAgent(llm_client)

# 2. Prepare context
context = {"photo_id": "001", "image_bytes": image_data, ...}

# 3. Run agent
result = await agent.run(context)

# 4. Result is typed Pydantic model
print(result.components)  # Type-safe access
```

## Error Handling

All agents follow this pattern:

```python
async def run(self, context):
    self.logger.info(f"Starting {self.name}")
    try:
        # Execute LLM call
        response = await self.llm.complete(...)
        
        # Parse and validate
        result = self._parse_response(response, OutputType)
        
        self.logger.info(f"Completed {self.name}")
        return result
        
    except Exception as e:
        self.logger.error(f"Failed: {e}")
        raise
```
