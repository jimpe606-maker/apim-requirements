# 03 — Requirement model

This document is the baseline's requirement model: it sets out what a requirement record looks
like, which attributes it has, and which rules apply. Concepts follow ISO/IEC/IEEE 29148 (see
§11).

## 1. Concepts and how the baseline applies them

| Concept | How the baseline applies it | Where |
|---|---|---|
| System of interest | The system being specified: the API management solution *and* its lifecycle processes. It is a socio-technical system — gateway, control plane, authorization server, pipelines *and* the platform team. | docs/01 |
| Stakeholder need → goal | Each stakeholder need is expressed as a goal record (`type: goal`, area GOAL) at the top of the SOL hierarchy; `source` names the need. | requirements/solution/goal.yaml |
| Requirement hierarchy | SOL is one hierarchy: goals → the top-level requirement of each area → system and component requirements, each linked to its parent with `traces.parents`. Lint W07 checks that every SOL requirement traces up to a goal. | field, lint |
| Decomposition and refinement | The two ways a child requirement is obtained from its parent: splitting it into several, or adding detail. Both are recorded as `traces.parents`. The field is deliberately not called *derives_from*: a *derived requirement* usually means one created to fill a gap, not one obtained from a parent. | field |
| Requirement set | Three sets, **SOL**, **PROC** and **IMPL**, each defined by its purpose, scope and extent in `schema/vocab.yaml#sets`. A requirement also belongs to other groupings, such as its area or its type. | vocab |
| Requirement type | `type` holds the record's primary type (goal, system, quality, cybersecurity, information_security, process, organizational, assurance, regulatory, legal). A requirement can fit several categories; the field records the one most useful for filtering. | field |
| Level of detail | `level`: goal → top_level (top of an area's sub-hierarchy) → system → component. | field |
| Allocation | `allocated_to` names the system elements (components C1…C17, or `ORG` for the organisation) that realise the requirement. | field |
| Priority | `priority` on the ordered scale must / should / could, expressing the buyer's priority. `must` means not negotiable. | field |
| Acceptance criteria | `acceptance_criteria[]` state what must be true for the requirement to count as met; `verification` names the method. | fields |
| Purpose and source | `rationale` holds the purpose (the effect the requirement should achieve); `source` holds the stakeholder or document it comes from. | fields |
| Identifier, status, owner | `id`, `status`, `owner` (the person or team accountable for the requirement). The Git history is the revision history. | fields |
| Traceability | Upwards: `parents` to a goal, `source` to the need. Across sets: `satisfies` from PROC/IMPL to SOL. Downwards: `allocated_to` to system elements, `use_cases` to docs/02. Lint fails on links to records that do not exist. | lint |
| Requirement creep | Adding requirements that no agreed need calls for. Prevented by "no PROC/IMPL without a SOL requirement to satisfy" (L05), "every SOL requirement traces to a goal" (W07), and `status` + `owner`. | lint |
| Notation | Statements are written in constrained natural language using EARS templates (§6). | writing rules |
| Buyer and supplier | The *buyer* procures the solution; the *supplier* (or vendor) submits an offer. | docs |

## 2. Solution vs procurement vs implementation — the rule

The **same concern is written three times, with three different subjects and verbs**:

| Set | Subject | Verb | Example (configuration as code) |
|---|---|---|---|
| SOL | *The solution* | shall **provide / support / expose** | The solution shall expose 100 % of its configuration (APIs, policies, plans, clients) as versioned, diff-able text artefacts applied through an API. |
| PROC | *The offer* | shall **demonstrate / be scored on** | The offer shall be scored on the degree to which configuration can be applied declaratively without console interaction: full = 5, partial = 2, console-only = 0. |
| IMPL | *The delivery / the organisation / the pipeline* | shall **do / operate / own** | Every production change shall be applied by the CI/CD pipeline from a merged, signed commit; human write access to the console shall be disabled. |

Consequences:

* SOL is **product-neutral**: it never names a product and is the only set procurement can score against. It is not *solution-free*: where the buyer needs it, SOL deliberately constrains the solution (open standards, interfaces, protocols such as DPoP or OpenTelemetry). Such constraints are legitimate when the buyer cannot accept an offer without them, and stating them early saves suppliers from evaluating options that would be rejected. The aim is to avoid *unnecessary* constraints, which is a review concern.
* PROC exists to make SOL **discriminating in a market**: each PROC record says *what evidence* is required and *how points are awarded*. Every `must` SOL requirement maps to at least one `mandatory` or `qualification` PROC record (pass/fail, lint W04); `should`/`could` map to `evaluated` records with a scale. Where a `must` capability is also worth grading, write two records — a `mandatory` minimum bar and an `evaluated` record for depth — linked with `traces.related` (e.g. PROC-GW-003 → PROC-SEC-002).
* IMPL says **how** the buyer's organisation and delivery realise SOL: pipeline stages, gates, roles, runbooks, training. IMPL records are typically process requirements ("the pipeline shall lint…"), organisation requirements (roles, ownership) or measurable quality targets ("deployment lead time ≤ 1 day"). The terms *functional* and *non-functional* are avoided because they are defined only against each other and classify few requirements usefully.

## 3. Three dimensions on every requirement

`layer` — **technology / process / organization** — cuts across all sets and areas, so a
filter such as `set=IMPL layer=organization` yields the operating-model work package,
and `set=PROC layer=technology area=SEC` yields the security scoring sheet.

## 4. Requirement areas

Twelve areas are used for both procurement scoring and delivery work packages
(see `schema/vocab.yaml#areas`): ARCH, GW, SEC, LCM, DEVX, CAC, POL, OBS, OPS,
DATA, ORG, COM. The procurement weight of each area is the `weight` attribute in
`schema/vocab.yaml#areas` (the source of truth; lint L14 checks that area weights sum to 1.0
and that the `scoring.weight` values of the PROC records within an area also sum to 1.0).
The baseline distribution for a zero-trust, CaC-first project (adjust per context):

| Area | Weight | Why |
|---|---|---|
| SEC | 25 % | FAPI 2.0 / zero trust is the discriminating capability. |
| CAC | 20 % | Declarative, API-first management is a hard architectural constraint. |
| GW | 10 % | Enforcement depth (sender-constrained tokens, schema validation). |
| POL | 10 % | Policy-as-code, lint, verification, impact analysis. |
| LCM, DEVX | 5 % each | Contract-first lifecycle, consumer self-service as code. |
| OBS, DATA | 5 % each | Audit, tamper evidence, PII controls. |
| ARCH, OPS | 5 % each | Plane separation, deployment options, resilience. |
| COM | 5 % | Licensing, support, exit. |
| ORG | 0 % | Buyer-side organisation; realised by IMPL, not scored. |

Offer score = Σ over scored PROC records of (points awarded / max points) × area weight ×
weight in area. `python tools/export.py` writes the resulting evaluation sheet to
`build/scoring.md`. An area with a weight but no scored record is reported as W06.

## 5. Record format

```yaml
set: SOL
area: CAC
requirements:
  - id: SOL-CAC-001
    title: All configuration as versioned text artefacts
    layer: technology
    type: system
    level: top_level
    priority: must
    statement: The solution shall expose ... through a documented API.
    rationale: Purpose, the effect the requirement should achieve.
    source: The stakeholder or document it comes from, e.g. a standard clause.
    acceptance_criteria:
      - Observable, testable condition 1
    verification: demonstration
    allocated_to: [C2, C4]
    traces:
      parents: [SOL-GOAL-003]
      use_cases: [UC-01, UC-02]
      standards: [...]
    status: draft
    owner: platform-architecture
```

`procurement:` is required on PROC records and forbidden elsewhere (lint).

## 6. Writing rules

Statements are written in constrained natural language: plain English sentences built from
EARS templates (Easy Approach to Requirements Syntax), which fix the sentence structure and leave
slots for the system-specific parts.

1. One requirement, one sentence, active voice, one **shall**. Use the EARS templates:
   *ubiquitous* ("The solution shall…"), *event-driven* ("When …, the gateway shall…"),
   *state-driven* ("While …, … shall…"), *unwanted behaviour* ("If …, then … shall…").
   Goals (`type: goal`) state an effect or state to achieve or maintain.
2. No weasel words (list in vocab). No "and/or". No product names in SOL.
3. Every requirement has ≥1 acceptance criterion that a tester or evaluator can execute
   without asking the author.
4. `should`/`could` PROC records carry a scale; `must` records are pass/fail. A capability
   that needs both a minimum bar and grading gets two records (see §2), for example
   PROC-SEC-001 (certification, pass/fail) and PROC-SEC-009 (breadth, scored).
5. IDs are never reused; retire with `status: retired`, keep the record.

## 7. ID scheme

`<SET>-<AREA>-<NNN>` e.g. `IMPL-CAC-002`. Numbers are sequential per (set, area).

## 8. Lifecycle

`draft` → `reviewed` (peer + security review) → `approved` (owner + procurement or steering)
→ `retired`. State changes are commits; the pull request is the
review record, and the Git history is the requirement's revision history.

## 9. Tooling

`tools/lint.py` enforces the rules above (run `--strict` to also flag non-atomic statements);
`tools/export.py` produces CSV, catalogue, traceability and scoring views in `build/`.
See [04 — Approach assessment](04-approach-assessment.md) for why the baseline uses
plain YAML with a custom lint, and when to move to StrictDoc, Doorstop, sphinx-needs,
ReqIF or OSCAL instead.

## 10. Requirement and set properties

The qualities a good requirement and a good requirement set should have (from ISO/IEC/IEEE
29148 and requirements-engineering practice), and how the baseline supports each. *Review*
means a human (or an AI agent following `.claude/skills/requirements-authoring`) must judge it;
the lint cannot.

### A single requirement

| Property | Practical test | Support in this baseline |
|---|---|---|
| Atomic | Could a supplier or team meet half of it? If so, split it. | One *shall* per statement (W05, `--strict`; heuristic, enforced in CI) + review. |
| Unambiguous | Would two evaluators read it the same way? | Vague-word list (L10) + review. |
| Explicit | Is anything in the statement a reason or background rather than the requirement itself? Move it to `rationale`. | Review. |
| Complete | Can a reader act on the record without asking the author? | All attributes required by the schema (L01) + review. |
| Feasible | Is there evidence the market or the organisation can deliver it? | Review; PROC evidence. |
| Correct | Are the facts in it right (standards, RFC numbers, protocol names), and does it avoid contradicting itself? | Schema and wording rules (L01, L10) + review. |
| Measurable | Does it name a number, threshold or observable state? | Acceptance criteria with thresholds + review. |
| Necessary | Which goal would suffer if it were removed? | Every SOL requirement traces to a goal (W07); every PROC/IMPL record satisfies SOL (L05). |
| Verifiable | Could someone other than the author check it and get a clear yes or no? | ≥1 acceptance criterion and a verification method (L01) + review. |
| Suitable notation | Does it follow one of the EARS templates in §6? | Writing rules (§6) + review. |

### A requirement set

| Property | Practical test | Support in this baseline |
|---|---|---|
| Complete | Is every stakeholder need covered by some requirement? | Coverage warnings W01 and W03; review against the goals. |
| Consistent | Do any two requirements conflict, or use two names for one thing? | Unique IDs (L03), controlled vocabulary (L11, L13); conflicts need review. |
| Maintainable | Can a requirement be added or retired without restructuring the set? | One file per set and area, stable IDs, lint and tests in CI. |
| Bounded | Is anything present that no goal asks for? | L05 and W07 (no requirement without a parent or a SOL requirement to satisfy). |
| Traceable | Can each requirement's links up and down be followed? | L04, L05, L07, W07; traceability matrix from `tools/export.py`. |
| Trustworthy | Have the people accountable for it reviewed and approved it? | `status` reaches `approved` only after peer and security review. |
| Well-defined | Is it clear what the set is for and what it covers? | Set definition per set in `schema/vocab.yaml#sets`. |

## 11. References

The requirement model follows the concepts of ISO/IEC/IEEE 29148 (requirements engineering) and
ISO/IEC/IEEE 15288 (system life cycle processes). Its concept model was also checked, in
September 2026, against *Svensk kravterminologi* (a Swedish requirements terminology,
https://www.kravterminologi.se, © Patrik Sternudd). No text from these sources is reproduced in
this repository, and they are not covered by its licence.
