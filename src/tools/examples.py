from __future__ import annotations

from pydantic import BaseModel, Field


class SupplementExample(BaseModel):
    """A real-world supplement example with full context for k-shot learning."""

    example_id: str = Field(description="Unique identifier for the example")
    category: str = Field(
        description="Primary category (decking, ice_water_shield, etc.)"
    )
    supplement_type: str = Field(description="Type of supplement")
    carrier: str = Field(description="Insurance carrier")
    state: str = Field(description="State where claim occurred")
    original_estimate_excerpt: str = Field(
        description="Excerpt from original estimate showing what was/wasn't included"
    )
    photo_descriptions: list[str] = Field(
        description="Descriptions of photo evidence supporting the supplement"
    )
    line_item_description: str = Field(description="Description of the line item")
    supplement_request: str = Field(
        description="Full supplement request text as submitted to carrier"
    )
    justification: str = Field(description="Justification text used")
    code_citation: str | None = Field(default=None, description="Code citation if used")
    quantity: float = Field(description="Quantity requested")
    unit: str = Field(description="Unit of measurement")
    unit_price: float = Field(description="Price per unit")
    total_value: float = Field(description="Total value of supplement")
    success_factors: list[str] = Field(
        description="Key factors that contributed to approval"
    )
    outcome: str = Field(description="approved, partial, denied")
    outcome_notes: str | None = Field(default=None, description="Notes about outcome")
    tags: list[str] = Field(default_factory=list, description="Searchable tags")

    model_config = {"json_schema_serialization_defaults_required": True}


# Keyword scoring weights for retrieval
KEYWORD_WEIGHTS: dict[str, list[str]] = {
    "decking": [
        "deck",
        "decking",
        "osb",
        "plywood",
        "sheathing",
        "rot",
        "rotted",
        "water damage",
        "soft spots",
    ],
    "ice_water_shield": [
        "ice",
        "water",
        "shield",
        "barrier",
        "underlayment",
        "valley",
        "eave",
        "leak barrier",
    ],
    "drip_edge": ["drip", "edge", "eave", "rake", "perimeter", "metal edge"],
    "starter_strip": ["starter", "strip", "eave", "rake", "wind", "manufacturer"],
    "penetrations": [
        "pipe",
        "boot",
        "jack",
        "flashing",
        "chimney",
        "skylight",
        "vent",
        "penetration",
        "collar",
    ],
    "ventilation": [
        "vent",
        "ridge",
        "soffit",
        "attic",
        "intake",
        "exhaust",
        "nfa",
        "ventilation",
    ],
    "quantity": [
        "quantity",
        "measurement",
        "square",
        "waste",
        "factor",
        "underestimate",
        "increase",
    ],
}


class ExampleStore:
    EXAMPLES: list[SupplementExample] = [
        # ============================================================
        # DECKING EXAMPLES (4)
        # ============================================================
        SupplementExample(
            example_id="EX-001",
            category="decking",
            supplement_type="missing_line_item",
            carrier="State Farm",
            state="TX",
            original_estimate_excerpt="""ROOFING - STEEP
Remove Roofing - Comp. shingle    32 SQ    $45.00    $1,440.00
Roofing felt - 15 lb              32 SQ    $12.50    $400.00
Shingles - Comp., architectural   32 SQ    $195.00   $6,240.00
Drip edge - aluminum              245 LF   $2.85     $698.25
[NO DECKING LINE ITEMS INCLUDED]""",
            photo_descriptions=[
                "Photo 1: Close-up of exposed OSB decking at tear-off showing dark water staining and visible delamination in 3x4 ft area near plumbing vent",
                "Photo 2: Probe test showing soft, deteriorated wood fiber - probe penetrates 1/2 inch into decking surface",
                "Photo 3: Wide shot showing location of damaged area relative to plumbing penetration - water trail visible from vent to damaged zone",
            ],
            line_item_description='R&R OSB roof sheathing 7/16" - water damaged decking at plumbing penetration',
            supplement_request="""SUPPLEMENT REQUEST - DECKING REPLACEMENT

Claim: CLM-2024-78432
Item: OSB Roof Sheathing Replacement

During tear-off, water-damaged decking was discovered at the plumbing penetration area. The OSB sheathing shows significant delamination and loss of structural integrity.

Line Item: R&R OSB roof sheathing 7/16\"
Quantity: 6 sheets (SHT)
Unit Price: $48.00
Total: $288.00

This replacement is necessary to provide proper nail-holding capacity per GAF and Owens Corning installation requirements. Damaged decking cannot accept fasteners properly and will void manufacturer warranty.""",
            justification="Photo evidence shows water staining and delamination of OSB decking at plumbing penetration. Damaged decking discovered during tear-off must be replaced to provide proper nail-holding capacity per manufacturer installation requirements and IRC R803.2.1.1.",
            code_citation="IRC R803.2.1.1 - Structural wood sheathing shall be manufactured to resist racking and provide a nail base for attachment of roofing materials",
            quantity=6.0,
            unit="SHT",
            unit_price=48.00,
            total_value=288.00,
            success_factors=[
                "Clear photo documentation of water damage with visible delamination",
                "Probe test photos showing depth of deterioration",
                "Traceable water path from penetration to damage location",
                "Reference to manufacturer installation requirements",
                "Specific code citation for structural requirements",
            ],
            outcome="approved",
            outcome_notes="Full approval after desk adjuster reviewed photo evidence showing clear water damage pattern",
            tags=[
                "decking",
                "water_damage",
                "osb",
                "sheathing",
                "penetration",
                "tear_off",
                "rotted",
            ],
        ),
        SupplementExample(
            example_id="EX-002",
            category="decking",
            supplement_type="missing_line_item",
            carrier="Allstate",
            state="FL",
            original_estimate_excerpt="""ROOF REPLACEMENT
Tear off - comp shingle 1 layer   28 SQ    $42.00    $1,176.00
Felt - 30 lb (Florida code)       28 SQ    $18.00    $504.00
Shingles - dimensional            28 SQ    $210.00   $5,880.00
Ridge cap                         65 LF    $6.50     $422.50
[DECKING NOT ADDRESSED IN ORIGINAL SCOPE]""",
            photo_descriptions=[
                "Photo 1: Aerial drone image showing widespread dark staining pattern across north-facing slope - approximately 180 SF affected area",
                "Photo 2: Close-up of decking at tear-off showing fungal growth and wood fiber separation across multiple sheets",
                "Photo 3: Measurement photo with tape showing 12ft x 15ft damaged area with visible nail pull-through",
                "Photo 4: Cross-section of removed decking piece showing complete delamination of OSB layers",
            ],
            line_item_description='R&R OSB roof sheathing 7/16" - storm damage with subsequent water intrusion',
            supplement_request="""SUPPLEMENT REQUEST - EXTENSIVE DECKING REPLACEMENT

Claim: FL-2024-STM-8821
Item: OSB Roof Sheathing - Storm Damage Area

Storm damage allowed water intrusion over extended period prior to claim filing. North slope shows extensive decking deterioration affecting approximately 180 SF (5 full sheets + partials).

Line Items:
1. R&R OSB sheathing 7/16\" - 6 SHT @ $52.00 = $312.00
2. Decking labor - additional (included in #1)
3. H-clips for sheathing - 24 EA @ $0.85 = $20.40

Total Supplement: $332.40

Per Florida Building Code Section 1507.1, roof sheathing must be structurally sound and capable of supporting applied roofing materials. Damaged sheathing will not hold fasteners and presents life-safety risk.""",
            justification="Extensive storm damage with water intrusion affected north slope decking. Photos document 180 SF of deteriorated OSB with visible fungal growth, delamination, and nail pull-through. Replacement required per FBC 1507.1 for structural integrity and proper fastener retention.",
            code_citation="FBC 1507.1 - Roof deck shall be capable of supporting the roof covering materials and applied loads",
            quantity=6.0,
            unit="SHT",
            unit_price=52.00,
            total_value=332.40,
            success_factors=[
                "Drone imagery showing extent of damage pattern",
                "Measurement photos with clear dimensions",
                "Cross-section evidence of complete delamination",
                "Florida-specific code citation",
                "Link between storm damage and water intrusion timeline",
            ],
            outcome="approved",
            outcome_notes="Approved after field reinspection confirmed extent of damage matched photo documentation",
            tags=[
                "decking",
                "storm_damage",
                "osb",
                "florida",
                "extensive",
                "fungal",
                "water_damage",
            ],
        ),
        SupplementExample(
            example_id="EX-003",
            category="decking",
            supplement_type="missing_line_item",
            carrier="USAA",
            state="TX",
            original_estimate_excerpt="""ROOFING
Demo roofing                     25 SQ    $48.00    $1,200.00
Underlayment synthetic           25 SQ    $22.00    $550.00
Composition shingles             25 SQ    $188.00   $4,700.00
Starter and drip edge           INCLUDED
[NO PROVISIONS FOR DECKING REPAIR]""",
            photo_descriptions=[
                "Photo 1: Multiple scattered soft spots marked with spray paint - 8 locations identified across roof surface",
                'Photo 2: Detail of soft spot #1 near hip showing 18" diameter deteriorated area',
                "Photo 3: Detail of soft spot #4 at valley intersection with visible water staining",
                "Photo 4: Overview shot showing spray paint markings indicating all 8 affected locations",
            ],
            line_item_description="R&R OSB roof sheathing - scattered deteriorated areas discovered at tear-off",
            supplement_request="""SUPPLEMENT REQUEST - SCATTERED DECKING REPLACEMENT

Claim: USAA-TX-2024-12847
Item: OSB Decking Replacement - Multiple Locations

During roof tear-off, contractor discovered 8 scattered areas of deteriorated decking across the roof surface. Areas range from 12\" to 24\" diameter and are concentrated near penetrations and valley intersections.

Line Items:
1. OSB sheathing 7/16\" material - 4 SHT @ $45.00 = $180.00
2. Additional labor for scattered repair - 2 HR @ $65.00 = $130.00

Total Supplement: $310.00

Scattered repair requires additional labor due to non-contiguous work areas. Each location requires individual cutting, fitting, and blocking for proper support.""",
            justification="Eight scattered areas of deteriorated decking discovered during tear-off, concentrated near penetrations and valleys. Photo documentation shows each location marked and measured. Additional labor required for non-contiguous repairs per industry standard practice.",
            code_citation="IRC R803.2.1.1",
            quantity=4.0,
            unit="SHT",
            unit_price=45.00,
            total_value=310.00,
            success_factors=[
                "Systematic documentation with spray paint marking",
                "Individual photos of each affected area",
                "Overview photo showing distribution pattern",
                "Separate labor line item for scattered work",
                "Reasonable quantity based on area calculations",
            ],
            outcome="approved",
            outcome_notes="Labor line questioned initially but approved after explanation of scattered work efficiency loss",
            tags=["decking", "scattered", "multiple", "osb", "tear_off", "soft_spots"],
        ),
        SupplementExample(
            example_id="EX-004",
            category="decking",
            supplement_type="missing_line_item",
            carrier="Liberty Mutual",
            state="CO",
            original_estimate_excerpt="""STEEP ROOF - MAIN
Remove existing roofing          35 SQ    $50.00    $1,750.00
Ice & water at eaves             3 SQ     $125.00   $375.00
Synthetic underlayment           35 SQ    $20.00    $700.00
Architectural shingles           35 SQ    $205.00   $7,175.00
[PENETRATION AREAS NOT ADDRESSED FOR DECKING]""",
            photo_descriptions=[
                'Photo 1: Skylight frame showing water damage to surrounding decking - dark staining extends 8" in all directions from frame',
                "Photo 2: Plumbing vent with visible rust staining on adjacent decking indicating long-term water intrusion",
                'Photo 3: HVAC curb area showing soft decking confirmed by probe test - 6" affected radius',
                "Photo 4: All three penetration areas marked on roof diagram with affected square footage noted",
            ],
            line_item_description="R&R OSB roof sheathing - water damage at penetrations (skylight, plumbing, HVAC)",
            supplement_request="""SUPPLEMENT REQUEST - PENETRATION AREA DECKING

Claim: LM-CO-2024-44521
Item: Decking Replacement at Roof Penetrations

Water damage discovered at three roof penetrations during tear-off inspection:
1. Skylight - 4 SF affected (approximately 1/2 sheet)
2. Plumbing vent cluster - 2 SF affected (partial sheet)  
3. HVAC curb - 6 SF affected (approximately 1 sheet)

Line Items:
1. OSB sheathing 7/16\" - 3 SHT @ $48.00 = $144.00
2. Blocking/nailers for penetration framing - 16 LF @ $3.50 = $56.00

Total Supplement: $200.00

Penetration areas are prone to water intrusion from failed flashing. Damaged decking must be replaced to accept new flashing installation properly.""",
            justification="Water damage discovered at skylight, plumbing vent, and HVAC penetrations during tear-off. All three areas show evidence of long-term water intrusion with staining and soft decking confirmed by probe testing. Replacement required for proper flashing re-installation.",
            code_citation="IRC R903.2 - Flashings shall be installed at wall and roof intersections and at roof penetrations",
            quantity=3.0,
            unit="SHT",
            unit_price=48.00,
            total_value=200.00,
            success_factors=[
                "Documentation of each penetration type separately",
                "Probe test evidence for soft decking",
                "Reasonable quantity based on affected areas",
                "Blocking line item for proper repair",
                "Connection to flashing requirement",
            ],
            outcome="approved",
            outcome_notes="Full approval - penetration failures commonly cause decking damage",
            tags=[
                "decking",
                "penetration",
                "skylight",
                "plumbing",
                "hvac",
                "water_damage",
                "flashing",
            ],
        ),
        # ============================================================
        # ICE & WATER SHIELD EXAMPLES (3)
        # ============================================================
        SupplementExample(
            example_id="EX-005",
            category="ice_water_shield",
            supplement_type="code_requirement",
            carrier="Travelers",
            state="CO",
            original_estimate_excerpt="""ROOF COVERING
Felt underlayment 30#            28 SQ    $15.00    $420.00
Architectural shingles           28 SQ    $198.00   $5,544.00
Valley lining - rolled roofing   48 LF    $4.50     $216.00
[NO ICE BARRIER IN VALLEYS - FELT ONLY SPECIFIED]""",
            photo_descriptions=[
                "Photo 1: Valley intersection showing current condition - evidence of ice damming stains on fascia below valley",
                "Photo 2: Aerial view of roof showing two main valleys running full length of roof - 48 LF total",
                "Photo 3: Close-up of ice dam damage evidence at lower valley termination",
            ],
            line_item_description="Ice and water shield membrane - valleys per IRC R905.1.2",
            supplement_request="""SUPPLEMENT REQUEST - ICE BARRIER IN VALLEYS

Claim: TRV-CO-2024-91823
Item: Ice and Water Shield - Valley Application

Original estimate specified rolled roofing valley lining. Per IRC R905.1.2, ice barrier underlayment is required in valleys in areas where the mean January temperature is 25°F or less.

Property location: Denver metro area
Mean January temperature: 29.2°F (1991-2020 average)
HOWEVER: Property elevation 6,200 ft results in adjusted temperature of approximately 23°F

Line Item: Ice and water shield membrane - valleys
Quantity: 48 LF (converts to approximately 2.5 SQ at 36\" width)
Unit Price: $125.00/SQ
Total: $312.50

Code requirement applies at this elevation. Ice barrier provides superior protection against ice dam water intrusion compared to rolled roofing.""",
            justification="IRC R905.1.2 requires ice barrier in valleys where mean January temperature is 25°F or less. Property at 6,200 ft elevation has adjusted temperature below threshold. Original estimate specified inadequate rolled roofing valley treatment.",
            code_citation="IRC R905.1.2 - Ice barrier required in valleys in areas where mean January temperature is 25°F or less",
            quantity=2.5,
            unit="SQ",
            unit_price=125.00,
            total_value=312.50,
            success_factors=[
                "Elevation adjustment calculation for temperature",
                "Specific code citation with threshold",
                "Photo evidence of prior ice dam damage",
                "Clear comparison to original inadequate specification",
                "Accurate quantity conversion from LF to SQ",
            ],
            outcome="approved",
            outcome_notes="Approved after elevation temperature adjustment was explained - carrier agreed code applies",
            tags=[
                "ice_water_shield",
                "valley",
                "code_requirement",
                "ice_barrier",
                "colorado",
                "elevation",
            ],
        ),
        SupplementExample(
            example_id="EX-006",
            category="ice_water_shield",
            supplement_type="missing_line_item",
            carrier="State Farm",
            state="OK",
            original_estimate_excerpt="""ROOFING MATERIALS
Synthetic underlayment           30 SQ    $18.00    $540.00
Dimensional shingles             30 SQ    $192.00   $5,760.00
Starter strip                    185 LF   $1.25     $231.25
[NO ICE & WATER SHIELD AT EAVES - SYNTHETIC ONLY]""",
            photo_descriptions=[
                'Photo 1: Eave detail showing 24" overhang from exterior wall line to fascia edge',
                "Photo 2: Evidence of prior ice damming - paint bubbling on soffit directly below eave line",
                "Photo 3: Interior ceiling stain in room below eave indicating past water intrusion from ice dam",
            ],
            line_item_description='Ice and water shield membrane - eaves 24" minimum from exterior wall',
            supplement_request="""SUPPLEMENT REQUEST - EAVE ICE BARRIER

Claim: SF-OK-2024-66712
Item: Ice and Water Shield at Eaves

Original estimate omitted ice barrier at eaves, specifying synthetic underlayment only. Per IRC R905.1.2, ice barrier is required at eaves extending from the edge of the roof to a point at least 24 inches inside the exterior wall line.

Eave perimeter calculation:
- Front eave: 62 LF
- Rear eave: 62 LF  
- Side eaves: 28 LF x 2 = 56 LF
- Total perimeter: 180 LF
- Coverage at 3' width: 180 LF x 3 FT = 540 SF = 5.4 SQ

Line Item: Ice and water shield - eaves
Quantity: 5.5 SQ
Unit Price: $118.00/SQ
Total: $649.00

Photos document evidence of prior ice dam damage. Enhanced protection required per code.""",
            justification='IRC R905.1.2 requires ice barrier at eaves extending 24" past exterior wall line in applicable climate zones. Photos show evidence of prior ice dam damage including interior water staining and soffit paint damage. Original estimate inadequately specified synthetic underlayment only.',
            code_citation="IRC R905.1.2 - Ice barrier shall extend from eave edge to a point at least 24 inches inside the exterior wall line",
            quantity=5.5,
            unit="SQ",
            unit_price=118.00,
            total_value=649.00,
            success_factors=[
                "Perimeter calculation with dimensions",
                "Evidence of prior ice dam damage",
                "Interior water stain documentation",
                'Clear 24" requirement citation',
                "Proper quantity conversion math shown",
            ],
            outcome="approved",
            outcome_notes="Full approval - prior damage evidence strengthened code requirement argument",
            tags=[
                "ice_water_shield",
                "eave",
                "ice_barrier",
                "code_requirement",
                "ice_dam",
                "oklahoma",
            ],
        ),
        SupplementExample(
            example_id="EX-007",
            category="ice_water_shield",
            supplement_type="missing_line_item",
            carrier="Allstate",
            state="TX",
            original_estimate_excerpt="""ROOF SYSTEM
Remove and dispose roofing       34 SQ    $46.00    $1,564.00
15# felt paper                   34 SQ    $11.00    $374.00
3-tab composition shingles       34 SQ    $165.00   $5,610.00
Ridge cap                        72 LF    $5.75     $414.00
[NO ICE & WATER SHIELD ANYWHERE IN ESTIMATE]""",
            photo_descriptions=[
                "Photo 1: Full roof overview showing valleys, skylights, and chimney - multiple vulnerable areas",
                "Photo 2: Main valley detail - 38 LF running from ridge to gutter",
                "Photo 3: Secondary valley at garage intersection - 22 LF",
                "Photo 4: Chimney cricket showing complex geometry requiring enhanced protection",
            ],
            line_item_description="Ice and water shield membrane - valleys and penetrations",
            supplement_request="""SUPPLEMENT REQUEST - ICE & WATER SHIELD (MISSING FROM ESTIMATE)

Claim: ALL-TX-2024-33891
Item: Ice and Water Shield - Complete Installation

Original estimate specifies only 15# felt paper with no ice and water shield at any location. Industry standard and manufacturer requirements call for ice barrier at:

1. Valleys: 60 LF total (38 LF main + 22 LF secondary)
   Coverage: 60 LF x 3' width = 180 SF = 1.8 SQ

2. Chimney perimeter: 18 LF
   Coverage: 18 LF x 2' width = 36 SF = 0.4 SQ

3. Skylight perimeter: 12 LF  
   Coverage: 12 LF x 2' width = 24 SF = 0.25 SQ

Total: 2.45 SQ, rounded to 2.5 SQ

Line Item: Ice and water shield membrane
Quantity: 2.5 SQ
Unit Price: $115.00/SQ
Total: $287.50

GAF and Owens Corning both require ice barrier at valleys for warranty coverage. This is industry standard practice for quality roof installation.""",
            justification="Original estimate completely omitted ice and water shield, specifying only 15# felt paper. Industry standard requires ice barrier at valleys and penetrations. Manufacturer warranty requirements (GAF, Owens Corning) specify ice barrier installation at vulnerable areas for full warranty coverage.",
            code_citation="GAF System Plus Warranty Requirements; Owens Corning Preferred Contractor Specifications",
            quantity=2.5,
            unit="SQ",
            unit_price=115.00,
            total_value=287.50,
            success_factors=[
                "Itemized breakdown by location",
                "Square footage calculations shown",
                "Manufacturer warranty requirements cited",
                "Multiple vulnerable areas documented",
                "Photos of each application area",
            ],
            outcome="approved",
            outcome_notes="Approved based on manufacturer requirements and industry standard - carrier acknowledged 15# felt inadequate",
            tags=[
                "ice_water_shield",
                "valley",
                "chimney",
                "skylight",
                "manufacturer",
                "warranty",
                "missing",
            ],
        ),
        # ============================================================
        # DRIP EDGE EXAMPLES (2)
        # ============================================================
        SupplementExample(
            example_id="EX-008",
            category="drip_edge",
            supplement_type="missing_line_item",
            carrier="USAA",
            state="GA",
            original_estimate_excerpt="""STEEP ROOF
Tear off existing roof           27 SQ    $44.00    $1,188.00
Synthetic underlayment           27 SQ    $19.00    $513.00
Architectural shingles           27 SQ    $185.00   $4,995.00
Ridge vent                       42 LF    $11.00    $462.00
[NO DRIP EDGE LINE ITEM IN ESTIMATE]""",
            photo_descriptions=[
                "Photo 1: Existing eave edge showing no drip edge installed - shingles terminate at fascia",
                "Photo 2: Close-up of fascia board showing water damage and rot from lack of drip edge protection",
                "Photo 3: Rake edge similarly unprotected with visible water staining on rake board",
                "Photo 4: Measurement tape showing total eave run of 124 LF",
            ],
            line_item_description="Drip edge - aluminum Type D - eaves and rakes per IRC R905.2.8.5",
            supplement_request="""SUPPLEMENT REQUEST - DRIP EDGE INSTALLATION

Claim: USAA-GA-2024-55123
Item: Aluminum Drip Edge - Full Perimeter

Original estimate does not include drip edge at eaves or rakes. Per IRC R905.2.8.5, drip edge is required at both eaves and rakes of shingle roofs.

Perimeter measurement:
- Eave edges: 124 LF
- Rake edges: 96 LF
- Total perimeter: 220 LF

Line Item: Drip edge - aluminum - standard (Type D)
Quantity: 220 LF
Unit Price: $3.25/LF
Total: $715.00

Current installation has no drip edge, resulting in water damage to fascia and rake boards. Drip edge is code-required and prevents water intrusion at roof edges.""",
            justification="IRC R905.2.8.5 requires drip edge at both eaves and rakes. Original estimate completely omits drip edge. Photos show water damage to fascia from lack of drip edge protection. Full perimeter installation of 220 LF required for code compliance.",
            code_citation="IRC R905.2.8.5 - A drip edge shall be provided at eaves and rakes of shingle roofs",
            quantity=220.0,
            unit="LF",
            unit_price=3.25,
            total_value=715.00,
            success_factors=[
                "Clear code citation with specific section",
                "Photo evidence of damage from missing drip edge",
                "Accurate perimeter measurement",
                "Itemized eave vs rake quantities",
                "Reference to water protection function",
            ],
            outcome="approved",
            outcome_notes="Full approval - carrier acknowledged oversight in original estimate",
            tags=[
                "drip_edge",
                "missing",
                "code_requirement",
                "eave",
                "rake",
                "perimeter",
                "fascia",
            ],
        ),
        SupplementExample(
            example_id="EX-009",
            category="drip_edge",
            supplement_type="quantity_increase",
            carrier="State Farm",
            state="TX",
            original_estimate_excerpt="""ROOFING
Remove comp shingles              32 SQ    $45.00    $1,440.00
Felt 15#                          32 SQ    $12.00    $384.00
Comp shingles - 25 year           32 SQ    $175.00   $5,600.00
Drip edge - aluminum              140 LF   $2.85     $399.00
[DRIP EDGE QUANTITY FOR EAVES ONLY]""",
            photo_descriptions=[
                "Photo 1: Aerial view showing full roof perimeter with eaves and rakes marked",
                "Photo 2: Existing rake edge with damaged drip edge - bent and separated sections",
                "Photo 3: Measurement showing 68 LF front rake + 68 LF rear rake = 136 LF rakes",
                "Photo 4: Close-up of rake drip edge damage from storm impact",
            ],
            line_item_description="Drip edge - aluminum - additional quantity for rake edges",
            supplement_request="""SUPPLEMENT REQUEST - DRIP EDGE QUANTITY INCREASE

Claim: SF-TX-2024-88234
Item: Additional Drip Edge - Rake Edges

Original estimate includes 140 LF drip edge for eave edges only. Per IRC R905.2.8.5, drip edge is required at BOTH eaves AND rakes.

Actual measurements:
- Eave edges (included): 140 LF ✓
- Rake edges (not included): 136 LF
- Additional required: 136 LF

Line Item: Drip edge - aluminum (additional)
Quantity: 136 LF
Unit Price: $3.15/LF (matching original unit price)
Total: $428.40

Rake edges show storm damage to existing drip edge. Full replacement required at all roof edges per code requirements.""",
            justification="Original estimate quantity of 140 LF covers eave edges only. IRC R905.2.8.5 requires drip edge at both eaves and rakes. Additional 136 LF required for rake edges. Photos document storm damage to existing rake drip edge requiring replacement.",
            code_citation="IRC R905.2.8.5 - A drip edge shall be provided at eaves and rakes of shingle roofs",
            quantity=136.0,
            unit="LF",
            unit_price=3.15,
            total_value=428.40,
            success_factors=[
                "Clear breakdown of original vs required quantities",
                "Matched unit price to original estimate",
                "Specific code requirement for rakes",
                "Photo evidence of rake edge damage",
                "Measurement documentation",
            ],
            outcome="approved",
            outcome_notes="Approved after carrier verified rake edges were not measured in original inspection",
            tags=[
                "drip_edge",
                "quantity",
                "rake",
                "code_requirement",
                "measurement",
                "storm_damage",
            ],
        ),
        # ============================================================
        # STARTER STRIP EXAMPLES (2)
        # ============================================================
        SupplementExample(
            example_id="EX-010",
            category="starter_strip",
            supplement_type="missing_line_item",
            carrier="Liberty Mutual",
            state="FL",
            original_estimate_excerpt="""ROOF REPLACEMENT
Remove existing roof              26 SQ    $48.00    $1,248.00
Peel & stick underlayment         26 SQ    $85.00    $2,210.00
Impact resistant shingles         26 SQ    $245.00   $6,370.00
Ridge cap shingles                58 LF    $7.50     $435.00
[NO STARTER STRIP/STARTER COURSE IN ESTIMATE]""",
            photo_descriptions=[
                "Photo 1: Diagram of roof showing eave and rake perimeter where starter strip is required",
                "Photo 2: GAF installation instructions page showing starter strip requirement",
                "Photo 3: Current eave edge showing damaged starter course from wind lift",
            ],
            line_item_description="Starter strip shingles - eaves and rakes per manufacturer requirements",
            supplement_request="""SUPPLEMENT REQUEST - STARTER STRIP SHINGLES

Claim: LM-FL-2024-71234
Item: Starter Strip - Eaves and Rakes

Original estimate omits starter strip entirely. Per GAF installation instructions and FBC Section 1507.2.7.1, starter strip is required for proper shingle installation and wind resistance.

Perimeter calculation:
- Eave perimeter: 104 LF
- Rake perimeter: 88 LF
- Total starter required: 192 LF

Line Item: Starter strip shingles - universal
Quantity: 192 LF
Unit Price: $1.45/LF
Total: $278.40

In Florida high-wind zone, starter strip is essential for meeting HVHZ requirements. Provides adhesive bond line for first course and wind uplift resistance at edges.""",
            justification="Starter strip required per GAF installation requirements and FBC 1507.2.7.1 for proper shingle installation. Essential for wind resistance in Florida HVHZ. Original estimate completely omitted this required component at 192 LF total perimeter.",
            code_citation="FBC 1507.2.7.1 - Asphalt shingles shall be installed per manufacturer's printed instructions; GAF Installation Manual Section 4.2",
            quantity=192.0,
            unit="LF",
            unit_price=1.45,
            total_value=278.40,
            success_factors=[
                "Florida-specific code citation",
                "Manufacturer installation manual reference",
                "High-wind zone relevance",
                "Complete perimeter calculation",
                "Wind resistance function explained",
            ],
            outcome="approved",
            outcome_notes="Full approval - Florida carriers familiar with HVHZ starter requirements",
            tags=[
                "starter_strip",
                "missing",
                "manufacturer",
                "wind_resistance",
                "florida",
                "hvhz",
                "eave",
                "rake",
            ],
        ),
        SupplementExample(
            example_id="EX-011",
            category="starter_strip",
            supplement_type="quantity_increase",
            carrier="Farmers",
            state="OK",
            original_estimate_excerpt="""ROOFING - MAIN STRUCTURE
Tear off comp shingle            30 SQ    $42.00    $1,260.00
Felt underlayment                30 SQ    $14.00    $420.00
Dimensional shingles             30 SQ    $182.00   $5,460.00
Starter - eaves only             112 LF   $1.20     $134.40
[STARTER AT EAVES ONLY - RAKES NOT INCLUDED]""",
            photo_descriptions=[
                "Photo 1: Owens Corning installation guide showing starter required at both eaves AND rakes",
                "Photo 2: Existing rake edge showing wind damage to exposed shingle edge",
                "Photo 3: Measurement of rake edges - 42 LF each side x 2 = 84 LF total",
            ],
            line_item_description="Starter strip shingles - additional quantity for rake edges",
            supplement_request="""SUPPLEMENT REQUEST - STARTER STRIP QUANTITY INCREASE

Claim: FAR-OK-2024-44532
Item: Additional Starter Strip - Rake Edges

Original estimate includes 112 LF starter for eave edges only. Per Owens Corning TruDefinition installation requirements, starter strip is required at BOTH eaves and rakes for proper installation and wind resistance.

Current scope: 112 LF (eaves only) ✓
Additional required: 84 LF (rakes)

Line Item: Starter strip - rakes (additional)
Quantity: 84 LF  
Unit Price: $1.35/LF
Total: $113.40

Photos show wind damage at rake edges where starter was not previously installed. This contributed to shingle failure at roof perimeter.""",
            justification="Owens Corning installation requirements specify starter strip at both eaves and rakes. Original estimate covers eaves only. Additional 84 LF required for rake edges. Photos show wind damage at exposed rake edges indicating need for starter protection.",
            code_citation="Owens Corning TruDefinition Duration Installation Instructions - Section: Starter Strip Application",
            quantity=84.0,
            unit="LF",
            unit_price=1.35,
            total_value=113.40,
            success_factors=[
                "Specific manufacturer requirement cited",
                "Clear quantity breakdown (eaves vs rakes)",
                "Wind damage evidence at rakes",
                "Consistent pricing with original",
                "Direct reference to installation guide",
            ],
            outcome="approved",
            outcome_notes="Approved - manufacturer specs require rake application",
            tags=[
                "starter_strip",
                "quantity",
                "rake",
                "manufacturer",
                "wind_damage",
                "owens_corning",
            ],
        ),
        # ============================================================
        # PIPE BOOTS/PENETRATIONS EXAMPLES (3)
        # ============================================================
        SupplementExample(
            example_id="EX-012",
            category="penetrations",
            supplement_type="missing_line_item",
            carrier="State Farm",
            state="TX",
            original_estimate_excerpt="""ROOFING
Remove existing roof              28 SQ    $44.00    $1,232.00
Synthetic underlayment            28 SQ    $18.00    $504.00
Comp shingles - architect.        28 SQ    $195.00   $5,460.00
Step flashing                     32 LF    $8.00     $256.00
[NO PIPE BOOT/JACK REPLACEMENTS IN SCOPE]""",
            photo_descriptions=[
                "Photo 1: Overview showing 5 pipe penetrations on roof surface - 3 plumbing vents, 1 HVAC exhaust, 1 radon vent",
                "Photo 2: Close-up of plumbing vent #1 showing cracked and brittle rubber collar - daylight visible through crack",
                "Photo 3: Plumbing vent #2 with completely deteriorated rubber boot - metal collar exposed",
                "Photo 4: All 5 penetrations marked with arrows on roof diagram",
            ],
            line_item_description="Pipe jack/boot replacement - multiple penetrations with failed rubber collars",
            supplement_request="""SUPPLEMENT REQUEST - PIPE BOOT REPLACEMENTS

Claim: SF-TX-2024-23456
Item: Pipe Jack Boots - Multiple Penetrations

Original estimate does not include pipe boot replacements. All 5 roof penetrations have deteriorated rubber collars that cannot be reused.

Penetrations requiring boot replacement:
1. Plumbing vent - 2\" pipe - cracked rubber
2. Plumbing vent - 2\" pipe - missing rubber
3. Plumbing vent - 3\" pipe - brittle/cracked
4. HVAC exhaust - 4\" pipe - deteriorated
5. Radon vent - 3\" pipe - cracked collar

Line Items:
1. Pipe boot 2\" - 2 EA @ $38.00 = $76.00
2. Pipe boot 3\" - 2 EA @ $42.00 = $84.00
3. Pipe boot 4\" - 1 EA @ $48.00 = $48.00

Total: $208.00

Rubber collars are not reusable after roof tear-off and exposure. Replacement boots required to prevent water intrusion at penetrations.""",
            justification="All 5 roof penetrations have deteriorated, cracked, or missing rubber collars. Photos show daylight through cracks and complete rubber failure. Pipe boots cannot be reused after tear-off and must be replaced to prevent water intrusion. Industry standard practice is to replace all boots during re-roof.",
            code_citation="IRC R903.2.1 - Flashings shall be installed to prevent moisture from entering the wall or roof",
            quantity=5.0,
            unit="EA",
            unit_price=41.60,
            total_value=208.00,
            success_factors=[
                "Individual documentation of each penetration",
                "Photos showing specific damage type",
                "Size breakdown for accurate pricing",
                "Industry standard practice reference",
                "Clear water intrusion prevention rationale",
            ],
            outcome="approved",
            outcome_notes="Full approval - carriers generally accept boot replacement with photo evidence of deterioration",
            tags=[
                "pipe_boot",
                "penetration",
                "plumbing",
                "hvac",
                "rubber",
                "deteriorated",
                "flashing",
            ],
        ),
        SupplementExample(
            example_id="EX-013",
            category="penetrations",
            supplement_type="missing_line_item",
            carrier="Allstate",
            state="GA",
            original_estimate_excerpt="""STEEP ROOFING
Demo roofing                      35 SQ    $46.00    $1,610.00
Ice barrier at chimney            1 RL     $125.00   $125.00
Underlayment synthetic            35 SQ    $20.00    $700.00
Dimensional shingles              35 SQ    $188.00   $6,580.00
[CHIMNEY FLASHING NOT ADDRESSED - ONLY ICE BARRIER]""",
            photo_descriptions=[
                "Photo 1: Chimney with rusted and separated step flashing - 6 pieces visibly displaced",
                "Photo 2: Counter-flashing in mortar joints showing deteriorated caulk and gaps",
                "Photo 3: Cricket/saddle behind chimney showing damaged metal and debris accumulation",
                "Photo 4: Water stain on interior ceiling directly below chimney location",
            ],
            line_item_description="Chimney flashing system - complete replacement including step, counter, and cricket",
            supplement_request="""SUPPLEMENT REQUEST - CHIMNEY FLASHING SYSTEM

Claim: ALL-GA-2024-89234
Item: Complete Chimney Flashing Replacement

Original estimate includes ice barrier at chimney but no flashing replacement. Photos document failed chimney flashing system causing active water intrusion (interior ceiling stain documented).

Chimney dimensions: 36\" x 24\" masonry chimney

Flashing components required:
1. Step flashing - aluminum - 14 PC @ $9.50 = $133.00
2. Counter-flashing - aluminum - 10 LF @ $12.00 = $120.00
3. Counter-flashing reglet cutting - 10 LF @ $8.00 = $80.00
4. Cricket/saddle - aluminum - 1 EA @ $185.00 = $185.00
5. Sealant and fasteners - 1 EA @ $25.00 = $25.00

Total: $543.00

Complete flashing system replacement required due to rust, separation, and active water intrusion. Re-using failed flashing will result in continued leakage.""",
            justification="Complete chimney flashing system has failed with rusted step flashing, separated counter-flashing, and damaged cricket. Interior ceiling stain documents active water intrusion. Re-using existing flashing will perpetuate leak. Full replacement of step, counter, and cricket required per IRC R903.2.1.",
            code_citation="IRC R903.2.1 - Flashings shall be installed at wall and roof intersections; IRC R903.2.2 - Cricket required where chimney dimension perpendicular to slope is greater than 30 inches",
            quantity=1.0,
            unit="EA",
            unit_price=543.00,
            total_value=543.00,
            success_factors=[
                "Complete system approach vs. partial repair",
                "Interior water damage documentation",
                "Itemized component breakdown",
                "Chimney dimensions for cricket code",
                "Reglet cutting included",
            ],
            outcome="approved",
            outcome_notes="Approved after field reinspection confirmed flashing failure - interior stain was key evidence",
            tags=[
                "chimney",
                "flashing",
                "step_flashing",
                "counter_flashing",
                "cricket",
                "water_damage",
                "leak",
            ],
        ),
        SupplementExample(
            example_id="EX-014",
            category="penetrations",
            supplement_type="missing_line_item",
            carrier="USAA",
            state="CO",
            original_estimate_excerpt="""ROOF SYSTEM
Remove roofing                    22 SQ    $52.00    $1,144.00
Ice & water shield                4 SQ     $128.00   $512.00
Synthetic underlayment            22 SQ    $22.00    $484.00
Architectural shingles            22 SQ    $215.00   $4,730.00
[SKYLIGHT FLASHING NOT IN SCOPE]""",
            photo_descriptions=[
                'Photo 1: Skylight overview showing 30" x 48" fixed skylight with visible flashing deterioration',
                "Photo 2: Head flashing at top of skylight - separated from deck with visible gap",
                "Photo 3: Sill flashing at bottom showing rust and improper overlap with shingles",
                "Photo 4: Side apron flashing with step flashing integration failure",
            ],
            line_item_description="Skylight flashing kit - complete perimeter replacement",
            supplement_request="""SUPPLEMENT REQUEST - SKYLIGHT FLASHING REPLACEMENT

Claim: USAA-CO-2024-31567
Item: Skylight Flashing - Complete Replacement

Original estimate does not address skylight flashing. Current flashing shows deterioration at all four sides with separation, rust, and improper shingle integration.

Skylight size: 30\" x 48\" (Velux FCM fixed mount)

Flashing components:
1. Skylight flashing kit (Velux EDL kit) - 1 EA @ $165.00 = $165.00
2. Ice barrier around skylight perimeter - 1 SQ @ $125.00 = $125.00
3. Additional labor for skylight integration - 1.5 HR @ $65.00 = $97.50

Total: $387.50

Manufacturer (Velux) requires new flashing kit for proper integration with new roofing materials. Original flashing cannot be properly reused with new underlayment and shingles.""",
            justification="Skylight flashing shows deterioration at all four connection points. Velux manufacturer requires flashing kit replacement when re-roofing for proper integration and warranty coverage. Photos document separation at head, rust at sill, and step flashing failure at sides. Ice barrier around perimeter required per manufacturer specifications.",
            code_citation="Velux Installation Instructions for EDL Flashing Kit; IRC R903.2 - Flashing at roof penetrations",
            quantity=1.0,
            unit="EA",
            unit_price=387.50,
            total_value=387.50,
            success_factors=[
                "Manufacturer-specific flashing kit",
                "Documentation of all four sides",
                "Ice barrier at skylight perimeter",
                "Labor line for integration work",
                "Warranty coverage rationale",
            ],
            outcome="approved",
            outcome_notes="Approved with manufacturer flashing kit requirement accepted",
            tags=[
                "skylight",
                "flashing",
                "velux",
                "penetration",
                "manufacturer",
                "kit",
                "ice_barrier",
            ],
        ),
        # ============================================================
        # VENTILATION EXAMPLES (2)
        # ============================================================
        SupplementExample(
            example_id="EX-015",
            category="ventilation",
            supplement_type="missing_line_item",
            carrier="Travelers",
            state="TX",
            original_estimate_excerpt="""ROOF REPLACEMENT
Tear off existing shingles        38 SQ    $45.00    $1,710.00
Felt paper 15#                    38 SQ    $12.00    $456.00
Comp shingles - 3 tab             38 SQ    $165.00   $6,270.00
Box vents (re-install)            4 EA     $0.00     $0.00
[RIDGE VENT NOT IN SCOPE - BOX VENTS ONLY]""",
            photo_descriptions=[
                "Photo 1: Existing roof with 4 box vents visible - outdated ventilation system",
                "Photo 2: Ridge line showing 52 LF available for continuous ridge vent installation",
                "Photo 3: Attic interior showing inadequate air flow with moisture staining on sheathing",
                "Photo 4: Existing box vent close-up showing rust and deterioration",
            ],
            line_item_description="Ridge vent - continuous - with filter and end caps",
            supplement_request="""SUPPLEMENT REQUEST - RIDGE VENT SYSTEM

Claim: TRV-TX-2024-67891
Item: Continuous Ridge Vent - Upgrade from Box Vents

Original estimate specifies re-installation of existing box vents. Box vents are deteriorated and provide inadequate ventilation. Continuous ridge vent provides superior exhaust ventilation per IRC R806.2.

Attic calculation:
- Attic floor area: 1,900 SF
- Required NFA: 1 SF per 150 SF attic = 12.67 SF NFA required
- Ridge vent NFA: 18 SF NFA per LF average
- Available ridge: 52 LF (provides 9.36 SF NFA exhaust)
- Combined with soffit intake: Meets 1:150 requirement

Line Items:
1. Ridge vent - shingle-over style - 52 LF @ $14.00 = $728.00
2. Ridge vent end caps - 2 EA @ $12.00 = $24.00
3. Remove existing box vents and patch - 4 EA @ $35.00 = $140.00

Total: $892.00

Ridge vent provides better air flow distribution and eliminates potential leak points from multiple box vent penetrations.""",
            justification="Existing box vents are deteriorated and provide inadequate ventilation per IRC R806.2 calculations. Continuous ridge vent is industry standard upgrade providing superior exhaust ventilation. Attic shows moisture staining indicating current ventilation inadequacy. Ridge vent eliminates 4 penetration points reducing leak potential.",
            code_citation="IRC R806.2 - Minimum ventilation area shall be 1/150 of area of vented space; IRC R806.3 - Ventilation openings shall be protected",
            quantity=52.0,
            unit="LF",
            unit_price=14.00,
            total_value=892.00,
            success_factors=[
                "NFA calculation showing compliance",
                "Attic moisture documentation",
                "Removal of inferior system",
                "Reduced penetration points benefit",
                "Complete system approach",
            ],
            outcome="approved",
            outcome_notes="Approved as betterment with contractor covering upgrade difference - carrier paid equivalent box vent replacement value",
            tags=[
                "ridge_vent",
                "ventilation",
                "exhaust",
                "box_vent",
                "upgrade",
                "nfa",
                "attic",
            ],
        ),
        SupplementExample(
            example_id="EX-016",
            category="ventilation",
            supplement_type="missing_line_item",
            carrier="State Farm",
            state="FL",
            original_estimate_excerpt="""ROOFING - STEEP
Demo roofing                      30 SQ    $48.00    $1,440.00
Peel and stick underlayment       30 SQ    $88.00    $2,640.00
Impact resistant shingles         30 SQ    $265.00   $7,950.00
Ridge vent                        38 LF    $12.00    $456.00
[NO INTAKE VENTILATION IN SCOPE]""",
            photo_descriptions=[
                "Photo 1: Soffit area showing solid (non-vented) aluminum soffit panels",
                "Photo 2: Attic interior showing heat buildup indicators - discolored insulation",
                "Photo 3: Gable end with no existing vents visible",
                "Photo 4: Ridge vent specification showing exhaust NFA",
            ],
            line_item_description="Soffit intake vents - continuous strip vent for balanced ventilation",
            supplement_request="""SUPPLEMENT REQUEST - INTAKE VENTILATION

Claim: SF-FL-2024-78234
Item: Soffit Intake Vents - Balanced Ventilation System

Original estimate includes ridge vent (exhaust) but no intake ventilation. Current soffit is solid aluminum with no vents. Per IRC R806.2, balanced ventilation requires intake and exhaust in 50/50 ratio.

Ridge vent exhaust: 38 LF = 6.84 SF NFA
Required intake: 6.84 SF NFA minimum

Soffit vent installation:
- Available soffit run: 124 LF (2 eaves)
- Continuous soffit vent: 2.5\" x 96\" strips
- 12 strips required for balanced NFA

Line Items:
1. Continuous soffit vent strips - 12 EA @ $18.00 = $216.00
2. Soffit cutting labor - 12 EA @ $25.00 = $300.00
3. Insulation baffles - 24 EA @ $3.50 = $84.00

Total: $600.00

Without intake ventilation, ridge vent cannot function properly. Balanced system required for code compliance and to prevent moisture problems and premature shingle failure.""",
            justification="Original estimate includes ridge vent exhaust but no intake ventilation. Current solid soffit prevents air intake. IRC R806.2 requires balanced ventilation system with intake and exhaust. Without intake, ridge vent cannot create proper airflow, leading to moisture problems and voiding shingle manufacturer warranty.",
            code_citation="IRC R806.2 - Ventilation shall be balanced between intake and exhaust; IRC R806.3 - Cross ventilation required",
            quantity=12.0,
            unit="EA",
            unit_price=18.00,
            total_value=600.00,
            success_factors=[
                "Balanced ventilation calculation",
                "Solid soffit documentation",
                "NFA matching to ridge vent",
                "Insulation baffles included",
                "Manufacturer warranty reference",
            ],
            outcome="approved",
            outcome_notes="Approved after ventilation calculation review - carrier agreed balanced system required",
            tags=[
                "soffit_vent",
                "intake",
                "ventilation",
                "balanced",
                "nfa",
                "florida",
                "exhaust",
            ],
        ),
        # ============================================================
        # QUANTITY INCREASES EXAMPLES (2)
        # ============================================================
        SupplementExample(
            example_id="EX-017",
            category="quantity",
            supplement_type="quantity_increase",
            carrier="Allstate",
            state="TX",
            original_estimate_excerpt="""ROOFING MATERIALS
Remove existing roof              28 SQ    $44.00    $1,232.00
Felt 15#                          28 SQ    $12.00    $336.00
Comp shingles - dimensional       28 SQ    $188.00   $5,264.00
[SHINGLE QUANTITY BASED ON FOOTPRINT ONLY]""",
            photo_descriptions=[
                "Photo 1: Aerial measurement showing complex roof geometry with 8 hips, 4 valleys, and 2 dormers",
                "Photo 2: Pitch measurement showing 8/12 slope on main structure, 6/12 on dormers",
                "Photo 3: Satellite measurement overlay with actual square footage calculations",
                "Photo 4: Contractor measurement diagram showing 33 actual squares",
            ],
            line_item_description="Additional shingle squares - actual roof measurement vs. footprint estimate",
            supplement_request="""SUPPLEMENT REQUEST - SHINGLE QUANTITY INCREASE

Claim: ALL-TX-2024-55667
Item: Additional Shingles - Measurement Correction

Original estimate of 28 SQ appears based on building footprint or approximate measurement. Actual roof measurement with pitch factor shows 33 SQ.

Measurement breakdown:
- Main roof footprint: 2,200 SF
- Pitch factor (8/12): 1.202
- Actual main roof: 2,644 SF
- Dormer additions: 380 SF
- Total roof area: 3,024 SF = 30.24 SQ
- Waste factor (10% for complex geometry): 3.0 SQ
- Total required: 33.24 SQ, rounded to 33 SQ

Original estimate: 28 SQ
Additional required: 5 SQ

Line Item: Comp shingles - dimensional (additional)
Quantity: 5 SQ
Unit Price: $188.00/SQ (matching original)
Total: $940.00

Complex roof geometry with multiple hips and valleys requires additional material. Underestimated quantity will result in contractor material shortfall.""",
            justification="Original estimate of 28 SQ is based on footprint measurement without proper pitch factor application. Actual roof measures 30.24 SQ at 8/12 pitch plus 10% waste for complex geometry (8 hips, 4 valleys, 2 dormers). Additional 5 SQ required to complete project without material shortfall.",
            code_citation="NRCA Roofing Manual - Steep Slope Section: Material Estimation Guidelines",
            quantity=5.0,
            unit="SQ",
            unit_price=188.00,
            total_value=940.00,
            success_factors=[
                "Pitch factor calculation shown",
                "Waste factor justified by complexity",
                "Satellite measurement documentation",
                "Matched unit pricing to original",
                "Clear math breakdown",
            ],
            outcome="approved",
            outcome_notes="Approved after reinspection confirmed 8/12 pitch and complex geometry - original adjuster used wrong pitch factor",
            tags=[
                "quantity",
                "shingles",
                "measurement",
                "pitch",
                "waste_factor",
                "complex",
                "underestimate",
            ],
        ),
        SupplementExample(
            example_id="EX-018",
            category="quantity",
            supplement_type="quantity_increase",
            carrier="Liberty Mutual",
            state="OK",
            original_estimate_excerpt="""ROOFING
Tear off and dispose              25 SQ    $46.00    $1,150.00
Synthetic underlayment            25 SQ    $20.00    $500.00
Architectural shingles            25 SQ    $195.00   $4,875.00
Waste factor                      NOT INCLUDED
[NO WASTE FACTOR IN SHINGLE QUANTITY]""",
            photo_descriptions=[
                "Photo 1: Roof overview showing 6 valleys requiring cuts and waste",
                "Photo 2: Multiple dormers with complex flashing integration",
                "Photo 3: Hip roof design with cuts required at every hip line",
                "Photo 4: NRCA waste factor guide page showing 15% for complex roofs",
            ],
            line_item_description="Shingle waste factor - additional material for complex roof cuts",
            supplement_request="""SUPPLEMENT REQUEST - WASTE FACTOR ADDITION

Claim: LM-OK-2024-88123
Item: Shingle Waste Factor - Complex Roof

Original estimate includes no waste factor for shingle installation. Industry standard waste factor for complex roof geometry is 10-15%.

Complexity factors present:
- 6 valleys (cuts at each course)
- Hip roof design (cuts at 8 hip lines)
- 3 dormers with integration cuts
- 2 skylights with cuts around
- Multiple penetrations

NRCA guidelines recommend:
- Simple gable: 5-7% waste
- Moderate complexity: 8-10% waste
- Complex (this roof): 12-15% waste

Calculation:
- Base shingle quantity: 25 SQ
- Waste factor (12%): 3 SQ
- Additional required: 3 SQ

Line Item: Architectural shingles - waste factor
Quantity: 3 SQ
Unit Price: $195.00/SQ
Total: $585.00""",
            justification="Original estimate includes no waste factor for shingle installation. Roof has 6 valleys, 8 hip lines, 3 dormers, and 2 skylights requiring extensive cuts. NRCA guidelines recommend 12-15% waste for complex roof geometry. 12% waste factor (3 SQ) is minimum industry standard for this roof configuration.",
            code_citation="NRCA Roofing Manual - Material Estimating: Waste factors range from 5% for simple gable to 15%+ for complex cut-up roofs",
            quantity=3.0,
            unit="SQ",
            unit_price=195.00,
            total_value=585.00,
            success_factors=[
                "NRCA waste factor guideline reference",
                "Itemized complexity factors",
                "Conservative 12% vs full 15%",
                "Photos of cut-requiring features",
                "Industry standard practice argument",
            ],
            outcome="approved",
            outcome_notes="Approved at 10% waste factor (2.5 SQ) - carrier countered at lower percentage but acknowledged waste required",
            tags=[
                "quantity",
                "waste_factor",
                "complex",
                "valleys",
                "hips",
                "cuts",
                "nrca",
            ],
        ),
        # ============================================================
        # ADDITIONAL HIGH-VALUE EXAMPLES (2)
        # ============================================================
        SupplementExample(
            example_id="EX-019",
            category="decking",
            supplement_type="missing_line_item",
            carrier="Travelers",
            state="GA",
            original_estimate_excerpt="""ROOFING
Remove comp shingles              30 SQ    $45.00    $1,350.00
Felt underlayment                 30 SQ    $13.00    $390.00
Dimensional shingles              30 SQ    $192.00   $5,760.00
Drip edge                         215 LF   $3.00     $645.00
[PLYWOOD DECKING NOT IN ORIGINAL SCOPE]""",
            photo_descriptions=[
                "Photo 1: Large section of plywood decking at tear-off showing delamination along entire valley line - approximately 8 feet",
                "Photo 2: Close-up of delaminated plywood with separated veneer layers",
                "Photo 3: Soft probing test showing complete loss of structural integrity",
                "Photo 4: Water damage pattern tracing from failed valley flashing to affected decking area",
            ],
            line_item_description='R&R Plywood roof decking 1/2" CDX - valley water damage',
            supplement_request="""SUPPLEMENT REQUEST - PLYWOOD DECKING REPLACEMENT

Claim: TRV-GA-2024-34521
Item: Plywood Decking - Valley Water Damage

During tear-off, significant plywood delamination discovered along main valley line. Failed valley flashing allowed long-term water intrusion damaging approximately 32 SF of decking.

Damage area calculation:
- Length along valley: 8 LF
- Width of damage: 4 FT average
- Affected area: 32 SF = 1 full sheet equivalent

Line Items:
1. Plywood CDX 1/2\" 4x8 sheets - 2 SHT @ $58.00 = $116.00
2. Additional blocking/nailers - 8 LF @ $4.00 = $32.00

Total: $148.00

Delaminated plywood cannot hold fasteners and must be replaced for proper shingle installation. Valley location makes this area prone to water damage from flashing failures.""",
            justification="Plywood decking along valley line shows complete veneer delamination from water intrusion at failed valley flashing. Two sheets required for proper repair of 32 SF affected area. Blocking included for proper edge support. Delaminated plywood provides no fastener holding capacity per IRC R803.2.",
            code_citation="IRC R803.2 - Plywood structural panels shall meet PS 1 or PS 2 standards for structural integrity",
            quantity=2.0,
            unit="SHT",
            unit_price=58.00,
            total_value=148.00,
            success_factors=[
                "Clear delamination documentation",
                "Water trail from valley flashing",
                "Accurate area calculation",
                "Blocking for proper repair",
                "PS 1/PS 2 standard reference",
            ],
            outcome="approved",
            outcome_notes="Full approval - valley water damage is common and well-documented cause of decking failure",
            tags=[
                "decking",
                "plywood",
                "valley",
                "delamination",
                "water_damage",
                "cdx",
            ],
        ),
        SupplementExample(
            example_id="EX-020",
            category="ice_water_shield",
            supplement_type="code_requirement",
            carrier="USAA",
            state="CO",
            original_estimate_excerpt="""ROOF SYSTEM - STEEP
Remove existing                   40 SQ    $48.00    $1,920.00
Synthetic underlayment            40 SQ    $22.00    $880.00
Dimensional shingles              40 SQ    $198.00   $7,920.00
Ice barrier eaves                 6 SQ     $125.00   $750.00
[ICE BARRIER AT EAVES ONLY - VALLEYS NOT INCLUDED]""",
            photo_descriptions=[
                "Photo 1: Two main valleys visible from aerial view - 38 LF and 42 LF respectively",
                "Photo 2: Snow accumulation pattern photo from previous winter showing valley ice dam formation",
                "Photo 3: Interior ceiling stain below valley intersection - evidence of past ice dam leakage",
                "Photo 4: Climate zone map showing property in Zone 5 (ice barrier required)",
            ],
            line_item_description="Ice and water shield membrane - valleys per IRC R905.1.2 climate zone requirement",
            supplement_request="""SUPPLEMENT REQUEST - VALLEY ICE BARRIER

Claim: USAA-CO-2024-22789
Item: Ice and Water Shield - Valley Application

Original estimate includes ice barrier at eaves but omits valleys. Per IRC R905.1.2, ice barrier is required in valleys in Climate Zone 5 and above where property is located.

Valley measurements:
- Main valley A: 38 LF
- Main valley B: 42 LF  
- Total valley: 80 LF

Coverage calculation:
- 80 LF x 36\" (3 FT) width = 240 SF = 2.4 SQ

Line Item: Ice and water shield - valleys
Quantity: 2.5 SQ
Unit Price: $125.00/SQ (matching eave price)
Total: $312.50

Interior staining below valley documents history of ice dam leakage. Enhanced protection at valleys required by code and to prevent future water intrusion.""",
            justification="Property located in Climate Zone 5 where IRC R905.1.2 requires ice barrier in valleys. Original estimate covered eaves but omitted valleys. Photos document 80 LF of valley and interior ceiling staining from previous ice dam water intrusion. Valley ice barrier required for code compliance and leak prevention.",
            code_citation="IRC R905.1.2 - Ice barriers required in valleys in areas where mean January temperature is 25°F or less (Climate Zones 5, 6, 7, 8)",
            quantity=2.5,
            unit="SQ",
            unit_price=125.00,
            total_value=312.50,
            success_factors=[
                "Climate zone documentation",
                "Previous ice dam damage evidence",
                "Interior water stain photos",
                "Matched unit price to eave application",
                "Valley measurement accuracy",
            ],
            outcome="approved",
            outcome_notes="Full approval - climate zone requirement clearly applicable and prior damage documented",
            tags=[
                "ice_water_shield",
                "valley",
                "code_requirement",
                "climate_zone",
                "colorado",
                "ice_dam",
            ],
        ),
    ]

    async def retrieve(
        self,
        query: str,
        carrier: str | None = None,
        supplement_type: str | None = None,
        category: str | None = None,
        state: str | None = None,
        limit: int = 3,
    ) -> list[SupplementExample]:
        """Retrieve examples matching query with enhanced keyword scoring."""
        query_lower = query.lower()
        query_terms = query_lower.split()

        scored_examples: list[tuple[float, SupplementExample]] = []

        for example in self.EXAMPLES:
            score = self._score_example(
                example,
                query_lower,
                query_terms,
                carrier,
                supplement_type,
                category,
                state,
            )
            if score > 0:
                scored_examples.append((score, example))

        scored_examples.sort(key=lambda x: x[0], reverse=True)
        return [ex for _, ex in scored_examples[:limit]]

    def _score_example(
        self,
        example: SupplementExample,
        query_lower: str,
        query_terms: list[str],
        carrier: str | None,
        supplement_type: str | None,
        category: str | None,
        state: str | None,
    ) -> float:
        """Enhanced scoring with keyword weights and multiple matching strategies."""
        score = 0.0

        # Exact filter matches (high weight)
        if carrier and example.carrier.lower() == carrier.lower():
            score += 3.0
        if supplement_type and example.supplement_type == supplement_type:
            score += 2.5
        if category and example.category == category:
            score += 2.5
        if state and example.state.upper() == state.upper():
            score += 2.0

        # Category keyword matching (check query against category keywords)
        for cat, keywords in KEYWORD_WEIGHTS.items():
            if example.category == cat:
                for keyword in keywords:
                    if keyword in query_lower:
                        score += 1.5  # Strong match for category-specific keywords
                        break

        # Build searchable text from all relevant fields
        searchable_parts = [
            example.line_item_description.lower(),
            example.justification.lower(),
            example.supplement_request.lower(),
            example.original_estimate_excerpt.lower(),
            " ".join(example.photo_descriptions).lower(),
            " ".join(example.tags),
            " ".join(example.success_factors).lower(),
        ]
        searchable_text = " ".join(searchable_parts)

        # Term matching with position bonus
        for term in query_terms:
            if len(term) < 3:
                continue  # Skip short terms

            if term in searchable_text:
                score += 1.0

                # Bonus for term in line item description
                if term in example.line_item_description.lower():
                    score += 0.5

                # Bonus for term in justification
                if term in example.justification.lower():
                    score += 0.3

            # Tag matching (exact tag match worth more)
            for tag in example.tags:
                if term == tag:
                    score += 1.0
                elif term in tag:
                    score += 0.5

        # Outcome weighting
        if example.outcome == "approved":
            score += 0.75
        elif example.outcome == "partial":
            score += 0.35

        # Bonus for examples with code citations when query suggests code need
        code_terms = ["code", "irc", "required", "requirement", "fbc", "nrca"]
        if example.code_citation and any(ct in query_lower for ct in code_terms):
            score += 1.0

        return score

    def get_by_id(self, example_id: str) -> SupplementExample | None:
        """Get a specific example by ID."""
        for example in self.EXAMPLES:
            if example.example_id == example_id:
                return example
        return None

    def get_by_type(self, supplement_type: str) -> list[SupplementExample]:
        """Get all examples of a specific supplement type."""
        return [ex for ex in self.EXAMPLES if ex.supplement_type == supplement_type]

    def get_by_category(self, category: str) -> list[SupplementExample]:
        """Get all examples in a specific category."""
        return [ex for ex in self.EXAMPLES if ex.category == category]

    def get_by_carrier(self, carrier: str) -> list[SupplementExample]:
        """Get all examples for a specific carrier."""
        return [ex for ex in self.EXAMPLES if ex.carrier.lower() == carrier.lower()]

    def get_by_state(self, state: str) -> list[SupplementExample]:
        """Get all examples from a specific state."""
        return [ex for ex in self.EXAMPLES if ex.state.upper() == state.upper()]

    def get_approved_examples(self) -> list[SupplementExample]:
        """Get all approved examples for learning patterns."""
        return [ex for ex in self.EXAMPLES if ex.outcome == "approved"]

    def get_all_tags(self) -> list[str]:
        """Get all unique tags across examples."""
        tags: set[str] = set()
        for example in self.EXAMPLES:
            tags.update(example.tags)
        return sorted(tags)

    def get_all_categories(self) -> list[str]:
        """Get all unique categories."""
        return sorted(set(ex.category for ex in self.EXAMPLES))

    def get_success_factors_by_category(self, category: str) -> list[str]:
        """Get all success factors for a category to understand patterns."""
        factors: list[str] = []
        for ex in self.EXAMPLES:
            if ex.category == category and ex.outcome == "approved":
                factors.extend(ex.success_factors)
        return factors
