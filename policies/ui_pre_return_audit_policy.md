# UI Pre-Return Audit Policy

Atlas should not treat a UI, landing or web interface as "ready to return" only because the files exist and a generic audit passed.

Before stronger handoff claims, Atlas should run a final advisory/read-only review over the intent, brand, anti-generic signals and minimum evidence that support the UI direction.

## When this audit runs

- after `visual_intent_contract` and `brand_profile_schema` are available or inferred
- before Atlas treats a UI, landing or visible interface as ready for final return
- recommended for frontend apps, landing pages, public sites and UI-heavy fullstack work
- optional for backend-only or non-visual CLI/service work

## What this audit reviews

- visual intent contract presence and sufficiency
- brand profile presence and sufficiency
- CTA clarity and integrity
- above-the-fold clarity
- layout hierarchy and pacing
- typography coherence
- color strategy coherence
- motion and visual-density alignment
- anti-generic patterns
- responsive readiness
- accessibility basics
- evidence expectations and whether final readiness claims are actually supported

## Minimum evidence before stronger PASS claims

- explicit visual intent contract when the project is UI-facing
- explicit or clearly reviewed brand profile when the UI carries identity expectations
- evidence-backed checks for CTA clarity, hierarchy, responsive baseline and contrast
- explicit evidence expectations before Atlas treats the UI as ready

## Anti-patterns

- returning README/PDF-like UIs as finished product-facing surfaces
- default SaaS template outputs with generic hierarchy and no brand rationale
- claiming strong readiness while intent, brand or evidence is still weak
- relying on browser or screenshot assumptions without real browser evidence

## Relationship with other Atlas components

- `visual_intent_contract` defines the minimum directional contract
- `brand_profile_schema` defines the structured identity layer
- `design_intelligence_audit` provides the observable design signals
- `quality_gate_report` surfaces the final advisory posture and warnings

## Limits

- advisory and read-only in this stage
- does not generate UI
- does not touch files
- does not replace real browser QA
- does not activate MCPs
- does not run browser automation

## Escalation

Recommend explicit human clarification when:

- intent or brand signals are still weak
- the UI is public-facing and multiple readiness warnings remain
- the final claim would be stronger than the evidence supports

Recommend `decision-council` when:

- brand alignment and product goals conflict
- derivative/generic risk remains high
- there is disagreement between surface quality, brand posture and delivery pressure
