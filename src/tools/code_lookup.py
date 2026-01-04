from __future__ import annotations

import re

from pydantic import BaseModel, Field


class CodeRequirement(BaseModel):
    topic: str = Field(description="Code topic (ice_barrier, drip_edge, etc.)")
    requirement: str = Field(description="What the code requires")
    citation: str = Field(description="Code reference (e.g., IRC R905.1.2)")
    mandatory: bool = Field(description="Whether this is mandatory")
    typical_value: str | None = Field(default=None, description="Typical specification")

    model_config = {"json_schema_serialization_defaults_required": True}


class CodeLookupTool:
    CODES_DATABASE: dict[str, dict[str, CodeRequirement]] = {
        "TX": {
            "ice_barrier": CodeRequirement(
                topic="ice_barrier",
                requirement="Ice barrier required in valleys and at eaves extending 24 inches minimum inside exterior wall line",
                citation="IRC R905.1.2 with Texas amendments",
                mandatory=True,
                typical_value="24 inches past exterior wall",
            ),
            "drip_edge": CodeRequirement(
                topic="drip_edge",
                requirement="Drip edge required at eaves and rake edges",
                citation="IRC R905.2.8.5",
                mandatory=True,
                typical_value='Metal drip edge, min 2" back, 1.5" face',
            ),
            "underlayment": CodeRequirement(
                topic="underlayment",
                requirement="One layer of underlayment required for roof slopes 4:12 and greater; two layers for slopes 2:12 to 4:12",
                citation="IRC R905.1.1",
                mandatory=True,
                typical_value="ASTM D226 Type I or ASTM D4869 Type I",
            ),
            "starter_strip": CodeRequirement(
                topic="starter_strip",
                requirement="Starter strip required at eaves and rakes",
                citation="Manufacturer specifications per IRC R905.2",
                mandatory=True,
                typical_value="Self-sealing strip or inverted 3-tab",
            ),
            "ventilation": CodeRequirement(
                topic="ventilation",
                requirement="Minimum 1 sq ft NFA per 150 sq ft of attic floor; 1:300 with balanced intake/exhaust",
                citation="IRC R806.2",
                mandatory=True,
                typical_value="1:150 ratio standard, 1:300 with balance",
            ),
            "fastening": CodeRequirement(
                topic="fastening",
                requirement="4 nails per shingle standard; 6 nails in high-wind zones",
                citation="IRC R905.2.6",
                mandatory=True,
                typical_value='11 or 12 gauge, min 3/4" penetration',
            ),
            "decking": CodeRequirement(
                topic="decking",
                requirement='Minimum 7/16" OSB or 15/32" plywood for 24" o.c. rafters',
                citation="IRC R803.2.1.1",
                mandatory=True,
                typical_value='7/16" OSB or 1/2" plywood',
            ),
            "flashing": CodeRequirement(
                topic="flashing",
                requirement="Flashing required at walls, chimneys, vents, and other roof penetrations",
                citation="IRC R903.2",
                mandatory=True,
                typical_value='Galvanized steel min 26 gauge or aluminum .019"',
            ),
        },
        "FL": {
            "ice_barrier": CodeRequirement(
                topic="ice_barrier",
                requirement="Not typically required due to climate; may be required for added protection",
                citation="Florida Building Code, Roofing Section",
                mandatory=False,
                typical_value="Optional self-adhering membrane",
            ),
            "drip_edge": CodeRequirement(
                topic="drip_edge",
                requirement="Drip edge required at all roof edges",
                citation="FBC R905.2.8.5",
                mandatory=True,
                typical_value="Metal drip edge meeting TAS 110",
            ),
            "underlayment": CodeRequirement(
                topic="underlayment",
                requirement="Enhanced underlayment required in High-Velocity Hurricane Zones (HVHZ)",
                citation="FBC R905.1.1, TAS 102-95",
                mandatory=True,
                typical_value="Self-adhering polymer modified bitumen",
            ),
            "starter_strip": CodeRequirement(
                topic="starter_strip",
                requirement="Starter strip required at eaves and rakes per manufacturer specifications",
                citation="FBC R905.2",
                mandatory=True,
                typical_value="High-wind rated starter strip",
            ),
            "fastening": CodeRequirement(
                topic="fastening",
                requirement="Enhanced fastening required; specific patterns for hurricane zones",
                citation="FBC R905.2.6, TAS 107",
                mandatory=True,
                typical_value="6 nails minimum, specific pattern required",
            ),
            "ventilation": CodeRequirement(
                topic="ventilation",
                requirement="1:150 ratio required; ridge vents must meet TAS 100(A)",
                citation="FBC R806.2",
                mandatory=True,
                typical_value="Balanced intake/exhaust, hurricane-rated",
            ),
            "decking": CodeRequirement(
                topic="decking",
                requirement="Enhanced fastening of roof sheathing required in HVHZ",
                citation="FBC R803.2",
                mandatory=True,
                typical_value='8d ring-shank nails at 6" o.c. edges',
            ),
            "flashing": CodeRequirement(
                topic="flashing",
                requirement="Flashing must meet Florida Product Approval requirements",
                citation="FBC R903.2",
                mandatory=True,
                typical_value="TAS-approved flashing systems",
            ),
        },
        "CA": {
            "ice_barrier": CodeRequirement(
                topic="ice_barrier",
                requirement="Required where snow expected; Title 24 climate zones determine requirements",
                citation="CBC R905.1.2",
                mandatory=True,
                typical_value="Climate zone dependent",
            ),
            "drip_edge": CodeRequirement(
                topic="drip_edge",
                requirement="Drip edge required at eaves and rakes",
                citation="CBC R905.2.8.5",
                mandatory=True,
                typical_value="Corrosion-resistant metal",
            ),
            "underlayment": CodeRequirement(
                topic="underlayment",
                requirement="Fire-resistant underlayment may be required in WUI zones",
                citation="CBC Chapter 7A",
                mandatory=True,
                typical_value="Class A fire rated in WUI zones",
            ),
            "ventilation": CodeRequirement(
                topic="ventilation",
                requirement="1:150 ratio required; reduced to 1:300 with specific configurations",
                citation="CBC R806.2",
                mandatory=True,
                typical_value="Ember-resistant vents in WUI zones",
            ),
            "starter_strip": CodeRequirement(
                topic="starter_strip",
                requirement="Starter strip required per manufacturer specifications",
                citation="CBC R905.2",
                mandatory=True,
                typical_value="Self-sealing starter strip",
            ),
            "fastening": CodeRequirement(
                topic="fastening",
                requirement="4 nails per shingle; 6 nails in high-wind areas",
                citation="CBC R905.2.6",
                mandatory=True,
                typical_value="Corrosion-resistant fasteners",
            ),
            "decking": CodeRequirement(
                topic="decking",
                requirement="Fire-resistant decking may be required in WUI zones",
                citation="CBC Chapter 7A",
                mandatory=True,
                typical_value="Non-combustible or ignition-resistant",
            ),
            "flashing": CodeRequirement(
                topic="flashing",
                requirement="Flashing required at all roof penetrations and intersections",
                citation="CBC R903.2",
                mandatory=True,
                typical_value="Corrosion-resistant metal flashing",
            ),
        },
        "CO": {
            "ice_barrier": CodeRequirement(
                topic="ice_barrier",
                requirement='Ice barrier required at eaves extending 24" past interior wall line',
                citation="IRC R905.1.2 as adopted",
                mandatory=True,
                typical_value="Self-adhering membrane in all areas",
            ),
            "drip_edge": CodeRequirement(
                topic="drip_edge",
                requirement="Drip edge required at eaves and rakes",
                citation="IRC R905.2.8.5",
                mandatory=True,
                typical_value="Metal drip edge",
            ),
            "underlayment": CodeRequirement(
                topic="underlayment",
                requirement="Ice barrier plus underlayment required",
                citation="IRC R905.1.1",
                mandatory=True,
                typical_value="Synthetic underlayment recommended",
            ),
        },
        "GA": {
            "ice_barrier": CodeRequirement(
                topic="ice_barrier",
                requirement="Ice barrier required in northern counties where January mean temp is 25°F or less",
                citation="IRC R905.1.2 as adopted",
                mandatory=True,
                typical_value="Climate zone dependent",
            ),
            "drip_edge": CodeRequirement(
                topic="drip_edge",
                requirement="Drip edge required at eaves and rakes",
                citation="IRC R905.2.8.5",
                mandatory=True,
                typical_value="Metal drip edge",
            ),
            "underlayment": CodeRequirement(
                topic="underlayment",
                requirement="Single layer of underlayment for slopes 4:12 and greater",
                citation="IRC R905.1.1",
                mandatory=True,
                typical_value="ASTM D226 Type I",
            ),
        },
        "NC": {
            "ice_barrier": CodeRequirement(
                topic="ice_barrier",
                requirement="Ice barrier required in mountain counties and areas with mean January temp 25°F or less",
                citation="NC Building Code R905.1.2",
                mandatory=True,
                typical_value="Required in western NC",
            ),
            "drip_edge": CodeRequirement(
                topic="drip_edge",
                requirement="Drip edge required at eaves and rakes",
                citation="NC Building Code R905.2.8.5",
                mandatory=True,
                typical_value="Metal drip edge",
            ),
            "underlayment": CodeRequirement(
                topic="underlayment",
                requirement="Underlayment required; enhanced in coastal areas",
                citation="NC Building Code R905.1.1",
                mandatory=True,
                typical_value="Enhanced underlayment in coastal counties",
            ),
        },
        "OK": {
            "ice_barrier": CodeRequirement(
                topic="ice_barrier",
                requirement="Ice barrier required at eaves",
                citation="IRC R905.1.2 as adopted",
                mandatory=True,
                typical_value="24 inches past exterior wall",
            ),
            "drip_edge": CodeRequirement(
                topic="drip_edge",
                requirement="Drip edge required",
                citation="IRC R905.2.8.5",
                mandatory=True,
                typical_value="Metal drip edge",
            ),
            "fastening": CodeRequirement(
                topic="fastening",
                requirement="6 nails per shingle recommended due to high wind",
                citation="IRC R905.2.6 with local amendments",
                mandatory=True,
                typical_value="6 nails in high-wind areas",
            ),
        },
        "LA": {
            "ice_barrier": CodeRequirement(
                topic="ice_barrier",
                requirement="Not typically required due to climate",
                citation="LA State Building Code",
                mandatory=False,
                typical_value="Optional",
            ),
            "drip_edge": CodeRequirement(
                topic="drip_edge",
                requirement="Drip edge required at all roof edges",
                citation="LA State Building Code",
                mandatory=True,
                typical_value="Corrosion-resistant metal",
            ),
            "fastening": CodeRequirement(
                topic="fastening",
                requirement="Enhanced fastening in hurricane-prone areas",
                citation="LA State Building Code, Wind Design",
                mandatory=True,
                typical_value="6 nails per shingle in coastal areas",
            ),
        },
        "TN": {
            "ice_barrier": CodeRequirement(
                topic="ice_barrier",
                requirement="Ice barrier required at eaves in most areas",
                citation="IRC R905.1.2 as adopted",
                mandatory=True,
                typical_value="24 inches past exterior wall",
            ),
            "drip_edge": CodeRequirement(
                topic="drip_edge",
                requirement="Drip edge required at eaves and rakes",
                citation="IRC R905.2.8.5",
                mandatory=True,
                typical_value="Metal drip edge",
            ),
            "underlayment": CodeRequirement(
                topic="underlayment",
                requirement="Single layer of underlayment required",
                citation="IRC R905.1.1",
                mandatory=True,
                typical_value="ASTM D226 Type I",
            ),
        },
        "AZ": {
            "ice_barrier": CodeRequirement(
                topic="ice_barrier",
                requirement="Required only in high-elevation areas with snow",
                citation="IRC R905.1.2 as adopted",
                mandatory=False,
                typical_value="Flagstaff and mountain areas only",
            ),
            "drip_edge": CodeRequirement(
                topic="drip_edge",
                requirement="Drip edge required",
                citation="IRC R905.2.8.5",
                mandatory=True,
                typical_value="Metal drip edge",
            ),
            "underlayment": CodeRequirement(
                topic="underlayment",
                requirement="Single layer underlayment required",
                citation="IRC R905.1.1",
                mandatory=True,
                typical_value="ASTM D226 Type I",
            ),
        },
    }

    STATE_MAPPING: dict[str, str] = {
        "texas": "TX",
        "florida": "FL",
        "california": "CA",
        "colorado": "CO",
        "arizona": "AZ",
        "georgia": "GA",
        "north carolina": "NC",
        "oklahoma": "OK",
        "louisiana": "LA",
        "tennessee": "TN",
    }

    async def lookup(
        self,
        jurisdiction: str,
        topics: list[str],
    ) -> list[CodeRequirement]:
        state = self._parse_state(jurisdiction)

        if state not in self.CODES_DATABASE:
            return []

        results = []
        state_codes = self.CODES_DATABASE[state]

        for topic in topics:
            topic_normalized = topic.lower().replace(" ", "_").replace("-", "_")
            if topic_normalized in state_codes:
                results.append(state_codes[topic_normalized])

        return results

    def _parse_state(self, jurisdiction: str) -> str:
        jurisdiction_upper = jurisdiction.upper().strip()

        if len(jurisdiction_upper) == 2 and jurisdiction_upper in self.CODES_DATABASE:
            return jurisdiction_upper

        jurisdiction_lower = jurisdiction.lower().strip()
        if jurisdiction_lower in self.STATE_MAPPING:
            return self.STATE_MAPPING[jurisdiction_lower]

        state_pattern = r",\s*([A-Z]{2})(?:\s+\d{5})?(?:\s*$|\s*,)"
        match = re.search(state_pattern, jurisdiction)
        if match:
            found_state = match.group(1)
            if found_state in self.CODES_DATABASE:
                return found_state

        for state_code in self.CODES_DATABASE.keys():
            if (
                f" {state_code} " in f" {jurisdiction_upper} "
                or jurisdiction_upper.endswith(f" {state_code}")
            ):
                return state_code

        return ""

    def get_all_topics(self) -> list[str]:
        return [
            "ice_barrier",
            "drip_edge",
            "underlayment",
            "starter_strip",
            "ventilation",
            "fastening",
            "decking",
            "flashing",
        ]

    def get_supported_states(self) -> list[str]:
        return list(self.CODES_DATABASE.keys())
