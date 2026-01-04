# System Architecture

Technical architecture documentation for the Insurance Supplementation Agent System.

## Design Principles

1. **Agent Autonomy**: Each agent operates independently with clear inputs/outputs
2. **Self-Correction**: Review loop enables automatic refinement without human intervention
3. **Defensibility**: Every supplement is backed by evidence and/or code citations
4. **Margin Awareness**: Business objectives (profit margin) are built into the pipeline
5. **Graceful Degradation**: System escalates to humans when confidence is low

## System Overview

```
┌────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT                                         │
│                    (Web App, Mobile App, Integration)                       │
└────────────────────────────────────┬───────────────────────────────────────┘
                                     │ HTTP/REST
                                     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                            API LAYER                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  FastAPI     │  │   Routes     │  │   Models     │  │  Job Store   │   │
│  │  Application │  │  /v1/jobs/*  │  │  Request/    │  │  (In-Memory) │   │
│  │              │  │              │  │  Response    │  │              │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
└────────────────────────────────────┬───────────────────────────────────────┘
                                     │ Background Task
                                     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATOR                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    OrchestratorContext                                │  │
│  │  - job: Job                    - gap_analysis: GapAnalysis           │  │
│  │  - vision_evidence: []         - supplement_strategy: Strategy       │  │
│  │  - estimate_interpretation     - review_result: ReviewResult         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Pipeline:  Prepare → Extract → Analyze → Strategize → Review → Report    │
└────────────────────────────────────┬───────────────────────────────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         ▼                           ▼                           ▼
┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐
│  VISION AGENT   │        │ ESTIMATE AGENT  │        │  GAP AGENT      │
│                 │        │                 │        │                 │
│ Input:          │        │ Input:          │        │ Input:          │
│ - Photo bytes   │        │ - PDF text      │        │ - Vision[]      │
│ - Job context   │        │ - Costs         │        │ - Estimate      │
│                 │        │                 │        │                 │
│ Output:         │        │ Output:         │        │ Output:         │
│ - Components[]  │        │ - LineItems[]   │        │ - ScopeGaps[]   │
│ - Observations  │        │ - Financials    │        │ - Summary       │
└─────────────────┘        └─────────────────┘        └─────────────────┘
         │                           │                           │
         └───────────────────────────┼───────────────────────────┘
                                     ▼
┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐
│ STRATEGIST      │        │ REVIEW AGENT    │        │ REPORT AGENT    │
│ AGENT           │        │                 │        │                 │
│                 │        │ Input:          │        │ Input:          │
│ Input:          │        │ - All upstream  │        │ - Strategy      │
│ - Gaps          │        │   outputs       │        │ - Metadata      │
│ - Estimate      │        │                 │        │ - Photos        │
│ - Evidence      │        │ Output:         │        │                 │
│                 │        │ - Approved?     │        │ Output:         │
│ Output:         │        │ - Reruns[]      │        │ - HTML          │
│ - Supplements[] │        │ - Adjustments[] │        │ - PDF bytes     │
│ - MarginAnalysis│        │ - HumanFlags[]  │        │                 │
│                 │        │                 │        │                 │
│ Tools:          │        │                 │        │ Tools:          │
│ - code_lookup   │        │                 │        │ - render_pdf    │
│ - examples      │        │                 │        │                 │
└─────────────────┘        └─────────────────┘        └─────────────────┘
         │                           │                           │
         └───────────────────────────┼───────────────────────────┘
                                     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                           LLM LAYER                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                      │
│  │  OpenAI      │  │  Anthropic   │  │  Mock        │                      │
│  │  Client      │  │  Client      │  │  Client      │                      │
│  │              │  │              │  │  (Testing)   │                      │
│  │ - complete() │  │ - complete() │  │              │                      │
│  │ - vision()   │  │ - vision()   │  │              │                      │
│  │ - tools()    │  │ - tools()    │  │              │                      │
│  └──────────────┘  └──────────────┘  └──────────────┘                      │
└────────────────────────────────────────────────────────────────────────────┘
```

## Agent Pipeline Flow

```
                                START
                                  │
                                  ▼
                        ┌─────────────────┐
                        │  Prepare Job    │
                        │  - Extract PDF  │
                        │  - Load photos  │
                        └────────┬────────┘
                                 │
                ┌────────────────┴────────────────┐
                │         PARALLEL                 │
                ▼                                  ▼
    ┌───────────────────┐              ┌───────────────────┐
    │   Vision Agent    │              │  Estimate Agent   │
    │   (per photo)     │              │                   │
    └─────────┬─────────┘              └─────────┬─────────┘
              │                                  │
              └────────────────┬─────────────────┘
                               │
                               ▼
                    ┌───────────────────┐
                    │  Gap Analysis     │
                    │  Agent            │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │  Strategist       │
                    │  Agent            │
                    └─────────┬─────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │        REVIEW LOOP            │
              │  ┌─────────────────────────┐  │
              │  │     Review Agent        │  │
              │  └───────────┬─────────────┘  │
              │              │                │
              │    ┌─────────┴─────────┐      │
              │    │                   │      │
              │    ▼                   ▼      │
              │ Approved?           Reruns?   │
              │    │                   │      │
              │    │ YES               │ YES  │
              │    │              ┌────┴────┐ │
              │    │              │ Execute │ │
              │    │              │ Reruns  │ │
              │    │              └────┬────┘ │
              │    │                   │      │
              │    │            ◄──────┘      │
              │    │         (max 2 cycles)   │
              └────┼──────────────────────────┘
                   │
                   ▼
          ┌────────────────┐
          │  Ready for     │──NO──▶ ESCALATE
          │  Delivery?     │        (Human Review)
          └────────┬───────┘
                   │ YES
                   ▼
          ┌────────────────┐
          │ Report Agent   │
          │ Generate PDF   │
          └────────┬───────┘
                   │
                   ▼
                COMPLETE
```

## Review Loop Logic

The review loop is the critical quality gate that ensures output quality.

### Cycle Limits

| Limit | Value | Purpose |
|-------|-------|---------|
| `MAX_REVIEW_CYCLES` | 2 | Maximum review iterations |
| `MAX_RERUNS_PER_AGENT` | 1 | Max reruns per agent type |
| `MAX_TOTAL_LLM_CALLS` | 12 | Total LLM call budget |

### Feedback Processing

```
Review Result
     │
     ├─▶ Adjustments (cheap, direct)
     │   └─▶ Apply directly to context objects
     │
     └─▶ Reruns (expensive, cascading)
         │
         ├─▶ supplement_agent: Just rerun
         ├─▶ gap_agent: Rerun → Strategist
         ├─▶ vision_agent: Rerun → Gap → Strategist
         └─▶ estimate_agent: Rerun → Gap → Strategist
```

### Cascade Rules

When an upstream agent is rerun, downstream agents must also rerun:

```
vision_agent ──▶ gap_agent ──▶ supplement_agent
                     ▲
estimate_agent ──────┘
```

## Data Schemas

### Core Entities

```
Job
├── job_id: str
├── metadata: JobMetadata
├── insurance_estimate: bytes (PDF)
├── photos: Photo[]
├── costs: Costs
└── business_targets: BusinessTargets

Photo
├── photo_id: str
├── file_binary: bytes
├── filename: str
├── mime_type: Literal[jpeg, png, webp, heic]
└── view_type: Literal[overview, close_up, ...]

Costs
├── materials_cost: float
├── labor_cost: float
└── other_costs: float
```

### Agent Outputs

```
VisionEvidence
├── photo_id: str
├── components: Component[]
└── global_observations: GlobalObservation[]

EstimateInterpretation
├── estimate_summary: EstimateSummary
├── line_items: LineItem[]
├── financials: Financials
└── parsing_confidence: float

GapAnalysis
├── scope_gaps: ScopeGap[]
└── coverage_summary: CoverageSummary

SupplementStrategy
├── supplements: SupplementProposal[]
├── margin_analysis: MarginAnalysis
└── strategy_notes: str[]

ReviewResult
├── approved: bool
├── ready_for_delivery: bool
├── reruns_requested: RerunRequest[]
├── adjustments_requested: Adjustment[]
├── human_flags: HumanFlag[]
├── margin_assessment: MarginAssessment
└── carrier_risk_assessment: CarrierRiskAssessment
```

## Tools

### Code Lookup Tool

Provides jurisdiction-specific building code requirements.

```python
await code_lookup.lookup(
    jurisdiction="TX",  # or "Texas" or "123 Main St, Dallas, TX"
    topics=["ice_barrier", "drip_edge", "ventilation"]
)
# Returns: CodeRequirement[]
```

Supported states: TX, FL, CA, CO, GA, NC, OK, LA, TN, AZ

### Example Store

K-shot example retrieval for supplement generation.

```python
await example_store.retrieve(
    query="decking water damage",
    carrier="State Farm",
    limit=3
)
# Returns: SupplementExample[]
```

### PDF Renderer

Converts HTML reports to PDF with embedded images.

```python
await pdf_renderer.render(
    html="<html>...</html>",
    images=[ImageEmbed(...)],
    options=RenderOptions(page_size="letter")
)
# Returns: RenderResult(pdf_binary, page_count)
```

## Configuration

### Environment Variables

```bash
# LLM Provider
LLM_PROVIDER=openai|anthropic|mock
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Models
VISION_MODEL=gpt-4o
TEXT_MODEL=gpt-4o

# Processing
MAX_REVIEW_CYCLES=2
MAX_RERUNS_PER_AGENT=1
DEFAULT_MARGIN_TARGET=0.33
```

### Settings Class

```python
from src.config import settings

settings.llm_provider      # "openai"
settings.vision_model      # "gpt-4o"
settings.default_margin_target  # 0.33
settings.is_production     # True if using real LLM
```

## Error Handling

### Agent Failures

```python
try:
    result = await agent.run(context)
except Exception as e:
    logger.error(f"Agent {agent.name} failed: {e}")
    # Orchestrator catches and creates failed result
```

### Review Loop Exhaustion

When max cycles reached without approval:
1. Create `HumanFlag` with severity=critical
2. Set `ready_for_delivery=False`
3. Return escalated result

### LLM Call Budget

If `llm_call_count >= MAX_TOTAL_LLM_CALLS`:
1. Stop further agent calls
2. Return current state as partial result
3. Flag for human review

## Performance Considerations

### Parallelization

- Vision analysis runs in parallel for all photos
- Estimate parsing runs in parallel with vision
- Gap analysis waits for both to complete

### Caching

- PDF text extraction is cached per job
- Building code lookups can be cached per jurisdiction
- Example retrieval can be cached per query hash

### Timeouts

| Operation | Timeout |
|-----------|---------|
| LLM API call | 120s |
| PDF extraction | 30s |
| Total job processing | 10min |
