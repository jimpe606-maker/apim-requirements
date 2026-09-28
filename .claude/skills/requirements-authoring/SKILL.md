---
name: requirements-authoring
description: Write, review, split or change requirement records in this repository (requirements/**.yaml) so they follow the baseline's requirement model and ISO/IEC/IEEE 29148 practice. Use when adding or editing SOL, PROC or IMPL records, reviewing a requirement pull request, answering "is this a good requirement?", closing lint warnings, or choosing requirement terms.
---

# Requirements authoring

This skill encodes the requirement model of this repository. The authoritative description is
`docs/03-requirement-model.md`; read it first when a rule below seems ambiguous. The lint
(`tools/lint.py`) enforces what can be checked mechanically; this skill covers the judgement the
lint cannot make.

## Language and terms

* Write in **plain English**. Use the terms and values defined in `schema/vocab.yaml` and
  `docs/03`; do not introduce synonyms (one name per concept).
* Do not copy definitions from standards (ISO/IEC/IEEE 29148 and others) or other copyrighted
  sources into the repository or into answers. Describe concepts in your own words and cite the
  source; when the exact wording matters, point the user to the source.
* Avoid *functional / non-functional requirement*; say process requirement, quality
  requirement, or describe the behaviour. Say *goal* for a requirement that states a high-level
  objective to achieve.
* Say *cybersecurity* (deliberate attack) or *safety* (accidental harm) rather than a bare
  *security* when the difference matters.

## The model in one screen

* Three requirement sets, each with a set definition in `schema/vocab.yaml#sets`:
  * **SOL**: what the solution shall be or do. A hierarchy: goals (`type: goal`, area GOAL)
    → area top-level requirements → system and component requirements, linked child → parent
    with `traces.parents` (decomposition or refinement). Product-neutral, but may constrain the
    solution to open standards and interfaces when the buyer needs it.
  * **PROC**: how an offer is checked pass/fail or scored against SOL. `traces.satisfies` → SOL.
  * **IMPL**: how the buyer's organisation realises SOL. `traces.satisfies` → SOL.
* Every non-goal SOL requirement traces up to a goal (W07). Every `must` SOL requirement has a
  `mandatory` or `qualification` PROC record (W04) and should have an IMPL record (W03).
* `rationale` = purpose (the effect to achieve). `source` = the stakeholder or artefact it comes
  from, as specific as possible. Do not mix the two.
* `priority` is the buyer's priority on the ordinal scale must / should / could. `must` means
  not negotiable; use it sparingly (see `docs/04` on the top-heavy scale).

## Writing a requirement

1. **Find its place.** Which set? Which goal or parent does it refine? If there is no parent,
   either it belongs under an existing goal or it is requirement creep: ask.
2. **Take the next free ID** `<SET>-<AREA>-<NNN>` in that file; never reuse a retired ID.
3. **Write the statement** in one sentence with exactly one *shall*, using an EARS template:
   * ubiquitous: `The <subject> shall <response>.`
   * event-driven: `When <trigger>, the <subject> shall <response>.`
   * state-driven: `While <state>, the <subject> shall <response>.`
   * unwanted behaviour: `If <condition>, then the <subject> shall <response>.`
   * goal: `The solution shall <effect or state to achieve or maintain>.`
   Subjects by set: SOL "the solution" or a component; PROC "the offer"; IMPL the pipeline,
   team or function that acts.
4. **Write acceptance criteria** that someone other than the author can execute: observable
   result, threshold, and conditions. At least one per record.
5. **Set the attributes**: `type` (primary category), `level`, `layer`, `verification`,
   `allocated_to` (C1–C17 or ORG), `owner`, `status: draft`.
6. **Add traces**: `parents` (SOL), `satisfies` (PROC/IMPL), `use_cases`, `standards`.
7. **For PROC**: `must` → `kind: mandatory` (pass/fail, no scoring) or `qualification`;
   `should`/`could` → `kind: evaluated` with a scale. If a must-have capability also deserves
   grading, write two records (pass/fail minimum + scored depth) linked with `traces.related`.
   Keep scoring weights in an area summing to 1.0.

## Review checklist

Answer each question for every changed record (the properties are described in `docs/03` §10).

| Property | Question to ask |
|---|---|
| atomic | Could a supplier or team fulfil half of it? Then split it, keeping the original ID for the main concern. |
| unambiguous | Would two evaluators read it the same way? Remove vague words and undefined abbreviations. |
| explicit | Does the statement contain only what is required, with reasons moved to `rationale`? |
| complete | Can the requirement be understood from the record alone (with its attributes)? |
| feasible | Is there evidence the market or the organisation can achieve it? |
| correct | Is it free of contradictions and factual errors (standards, RFC numbers, protocol names)? |
| measurable / verifiable | Does each acceptance criterion name an observable result and a threshold? |
| necessary | Does it trace to a goal, and would removing it leave a stakeholder need unmet? |
| suitable notation | Does it follow an EARS template with one *shall*? |

For the whole set, also check that no two requirements contradict each other, that each
phenomenon is named the same way everywhere, and that nothing was added without a parent.

## Splitting and rewording

* **Split** when the parts could be met, verified or failed independently. The original ID keeps
  the main concern; the split-off part gets the next free ID. Move each acceptance criterion
  to the half it tests. Re-point `satisfies` of PROC/IMPL records to the half they cover, and
  add PROC/IMPL records so the new half does not lose coverage.
* **Reword** into one *shall* when both verbs describe one behaviour (splitting would create a
  requirement that makes no sense alone).
* Record every change of meaning in `CHANGELOG.md`.

## Verify before finishing

```bash
python tools/lint.py            # must report 0 errors; explain any new warning
python tools/lint.py --strict   # changed records must add no W05
pytest -q                       # when tooling changed
python tools/export.py          # optional: check build/traceability.md for the new records
```

Report the lint result, list new and changed IDs, and state any judgement call (priority,
split versus reword, parent choice) so the human reviewer can check it.
