from __future__ import annotations

import pytest
import pytest_asyncio
from pathlib import Path
from typing import Any

from src.llm.client import LLMClient
from src.schemas.job import (
    Job,
    JobMetadata,
    Photo,
    Costs,
    BusinessTargets,
)
from tests.llm_responses import (
    detect_agent_type,
    get_response_for_agent,
    create_openai_response,
    create_anthropic_response,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestLLMClient(LLMClient):
    def __init__(self, force_escalation: bool = False) -> None:
        self.force_escalation = force_escalation

    async def complete(
        self,
        system: str,
        user: str,
        model: str | None = None,
    ) -> str:
        agent_type = detect_agent_type(system)
        return get_response_for_agent(agent_type, user, self.force_escalation)

    async def complete_vision(
        self,
        system: str,
        user: str,
        images: list[bytes],
        model: str | None = None,
    ) -> str:
        return get_response_for_agent("vision", user)

    async def complete_with_tools(
        self,
        system: str,
        user: str,
        tools: list[dict[str, Any]],
        model: str | None = None,
    ) -> dict[str, Any]:
        agent_type = detect_agent_type(system)
        content = get_response_for_agent(agent_type, user, self.force_escalation)
        return {"tool_calls": [], "content": content}


@pytest.fixture
def test_llm_client() -> TestLLMClient:
    return TestLLMClient()


@pytest.fixture
def escalation_test_client() -> TestLLMClient:
    return TestLLMClient(force_escalation=True)


@pytest.fixture
def sample_metadata() -> JobMetadata:
    return JobMetadata(
        carrier="State Farm",
        claim_number="CLM-12345",
        insured_name="John Doe",
        property_address="123 Main St, Dallas, TX 75201",
        date_of_loss="2024-01-15",
        policy_number="POL-999888",
        adjuster_name="Jane Smith",
        adjuster_email="jane.smith@statefarm.com",
        adjuster_phone="555-123-4567",
    )


@pytest.fixture
def sample_costs() -> Costs:
    return Costs(
        materials_cost=5000.0,
        labor_cost=8000.0,
        other_costs=500.0,
    )


@pytest.fixture
def sample_business_targets() -> BusinessTargets:
    return BusinessTargets(minimum_margin=0.33)


@pytest.fixture
def sample_photo_bytes() -> bytes:
    return bytes(
        [
            0xFF,
            0xD8,
            0xFF,
            0xE0,
            0x00,
            0x10,
            0x4A,
            0x46,
            0x49,
            0x46,
            0x00,
            0x01,
            0x01,
            0x00,
            0x00,
            0x01,
            0x00,
            0x01,
            0x00,
            0x00,
            0xFF,
            0xDB,
            0x00,
            0x43,
            0x00,
            0x08,
            0x06,
            0x06,
            0x07,
            0x06,
            0x05,
            0x08,
            0x07,
            0x07,
            0x07,
            0x09,
            0x09,
            0x08,
            0x0A,
            0x0C,
            0x14,
            0x0D,
            0x0C,
            0x0B,
            0x0B,
            0x0C,
            0x19,
            0x12,
            0x13,
            0x0F,
            0x14,
            0x1D,
            0x1A,
            0x1F,
            0x1E,
            0x1D,
            0x1A,
            0x1C,
            0x1C,
            0x20,
            0x24,
            0x2E,
            0x27,
            0x20,
            0x22,
            0x2C,
            0x23,
            0x1C,
            0x1C,
            0x28,
            0x37,
            0x29,
            0x2C,
            0x30,
            0x31,
            0x34,
            0x34,
            0x34,
            0x1F,
            0x27,
            0x39,
            0x3D,
            0x38,
            0x32,
            0x3C,
            0x2E,
            0x33,
            0x34,
            0x32,
            0xFF,
            0xC0,
            0x00,
            0x0B,
            0x08,
            0x00,
            0x01,
            0x00,
            0x01,
            0x01,
            0x01,
            0x11,
            0x00,
            0xFF,
            0xC4,
            0x00,
            0x1F,
            0x00,
            0x00,
            0x01,
            0x05,
            0x01,
            0x01,
            0x01,
            0x01,
            0x01,
            0x01,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x01,
            0x02,
            0x03,
            0x04,
            0x05,
            0x06,
            0x07,
            0x08,
            0x09,
            0x0A,
            0x0B,
            0xFF,
            0xC4,
            0x00,
            0xB5,
            0x10,
            0x00,
            0x02,
            0x01,
            0x03,
            0x03,
            0x02,
            0x04,
            0x03,
            0x05,
            0x05,
            0x04,
            0x04,
            0x00,
            0x00,
            0x01,
            0x7D,
            0x01,
            0x02,
            0x03,
            0x00,
            0x04,
            0x11,
            0x05,
            0x12,
            0x21,
            0x31,
            0x41,
            0x06,
            0x13,
            0x51,
            0x61,
            0x07,
            0x22,
            0x71,
            0x14,
            0x32,
            0x81,
            0x91,
            0xA1,
            0x08,
            0x23,
            0x42,
            0xB1,
            0xC1,
            0x15,
            0x52,
            0xD1,
            0xF0,
            0x24,
            0x33,
            0x62,
            0x72,
            0x82,
            0x09,
            0x0A,
            0x16,
            0x17,
            0x18,
            0x19,
            0x1A,
            0x25,
            0x26,
            0x27,
            0x28,
            0x29,
            0x2A,
            0x34,
            0x35,
            0x36,
            0x37,
            0x38,
            0x39,
            0x3A,
            0x43,
            0x44,
            0x45,
            0x46,
            0x47,
            0x48,
            0x49,
            0x4A,
            0x53,
            0x54,
            0x55,
            0x56,
            0x57,
            0x58,
            0x59,
            0x5A,
            0x63,
            0x64,
            0x65,
            0x66,
            0x67,
            0x68,
            0x69,
            0x6A,
            0x73,
            0x74,
            0x75,
            0x76,
            0x77,
            0x78,
            0x79,
            0x7A,
            0x83,
            0x84,
            0x85,
            0x86,
            0x87,
            0x88,
            0x89,
            0x8A,
            0x92,
            0x93,
            0x94,
            0x95,
            0x96,
            0x97,
            0x98,
            0x99,
            0x9A,
            0xA2,
            0xA3,
            0xA4,
            0xA5,
            0xA6,
            0xA7,
            0xA8,
            0xA9,
            0xAA,
            0xB2,
            0xB3,
            0xB4,
            0xB5,
            0xB6,
            0xB7,
            0xB8,
            0xB9,
            0xBA,
            0xC2,
            0xC3,
            0xC4,
            0xC5,
            0xC6,
            0xC7,
            0xC8,
            0xC9,
            0xCA,
            0xD2,
            0xD3,
            0xD4,
            0xD5,
            0xD6,
            0xD7,
            0xD8,
            0xD9,
            0xDA,
            0xE1,
            0xE2,
            0xE3,
            0xE4,
            0xE5,
            0xE6,
            0xE7,
            0xE8,
            0xE9,
            0xEA,
            0xF1,
            0xF2,
            0xF3,
            0xF4,
            0xF5,
            0xF6,
            0xF7,
            0xF8,
            0xF9,
            0xFA,
            0xFF,
            0xDA,
            0x00,
            0x08,
            0x01,
            0x01,
            0x00,
            0x00,
            0x3F,
            0x00,
            0xFB,
            0xD5,
            0xDB,
            0x20,
            0xA8,
            0xF1,
            0x7E,
            0xCB,
            0xCE,
            0x72,
            0x31,
            0xC6,
            0x7A,
            0xD6,
            0x85,
            0xF4,
            0x44,
            0xFF,
            0xD9,
        ]
    )


@pytest.fixture
def sample_photo(sample_photo_bytes: bytes) -> Photo:
    return Photo(
        photo_id="photo_001",
        file_binary=sample_photo_bytes,
        filename="roof_overview.jpg",
        mime_type="image/jpeg",
        view_type="overview",
        notes="Main roof view from street",
    )


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 200 >>
stream
BT
/F1 12 Tf
50 700 Td
(Insurance Estimate - State Farm) Tj
0 -20 Td
(Claim: CLM-12345) Tj
0 -20 Td
(25 SQ - Remove and replace shingles @ $350.00 = $8,750.00) Tj
0 -20 Td
(180 LF - Drip edge @ $3.50 = $630.00) Tj
0 -20 Td
(Total: $9,380.00) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000206 00000 n
trailer
<< /Size 5 /Root 1 0 R >>
startxref
458
%%EOF"""
    return pdf_content


@pytest.fixture
def sample_job(
    sample_metadata: JobMetadata,
    sample_costs: Costs,
    sample_business_targets: BusinessTargets,
    sample_photo: Photo,
    sample_pdf_bytes: bytes,
) -> Job:
    return Job(
        job_id="job_test_001",
        metadata=sample_metadata,
        insurance_estimate=sample_pdf_bytes,
        photos=[sample_photo],
        costs=sample_costs,
        business_targets=sample_business_targets,
    )


@pytest.fixture
def sample_estimate_text() -> str:
    return """
INSURANCE ESTIMATE
==================
Carrier: State Farm
Claim Number: CLM-12345
Insured: John Doe
Property: 123 Main St, Dallas, TX 75201
Date of Loss: 01/15/2024

LINE ITEMS:
-----------
1. Remove & replace - Composition shingles
   Quantity: 25 SQ @ $350.00 = $8,750.00

2. Drip edge - Aluminum
   Quantity: 180 LF @ $3.50 = $630.00

3. Felt underlayment - 15#
   Quantity: 25 SQ @ $45.00 = $1,125.00

4. Ridge cap shingles
   Quantity: 40 LF @ $8.00 = $320.00

SUBTOTAL: $10,825.00
O&P (20%): $2,165.00
TOTAL: $12,990.00

Depreciation: $2,500.00
ACV: $10,490.00
"""


@pytest_asyncio.fixture
async def async_test_client() -> TestLLMClient:
    return TestLLMClient()
