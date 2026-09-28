# Changelog

All notable changes to this baseline are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/) for requirement content (see
[CONTRIBUTING](CONTRIBUTING.md#releases)).

## [0.1.0-alpha.1] - 2026-09-28

First public alpha. Requirement content is `draft` and may change in any release.

### Added

- Reference architecture, use cases UC-01 to UC-07 and requirement model (docs/01–03).
- Critical assessment of the requirements-as-code approach, alternatives and roadmap
  (docs/04).
- 128 requirements: SOL 53 (including 7 goals), PROC 33, IMPL 42, across 12 areas.
- Procurement records so that every `must` SOL requirement has a pass/fail check, including
  minimum-bar records PROC-GW-003, PROC-LCM-003, PROC-POL-002 and PROC-POL-003.
- Area procurement weights in `schema/vocab.yaml` (`areas.*.weight`).
- Lint checks L13 (schema/vocabulary drift), L14 (scoring weights sum to 1.0), W03 (no IMPL
  record), W04 (`must` without pass/fail PROC), W05 (non-atomic statement, `--strict`) and
  W06 (area weight that cannot be earned).
- `tools/export.py`: CSV, requirement catalogue, traceability matrix and scoring sheet.
- Seven goal records (`type: goal`, area GOAL) at the top of the SOL requirement hierarchy,
  with every other SOL requirement linked up to one; lint check W07 enforces this.
- Set definitions (purpose, scope, extent) for SOL, PROC and IMPL, a meaning for every
  vocabulary value, requirement roles and the `legal` requirement type in `schema/vocab.yaml`.
- docs/03: concept table, mapping of every requirement and set property to a lint check or
  review step, and references.
- `.claude/skills/requirements-authoring`: instructions for AI agents that write or review
  requirements in this repository.
- Regression tests for the tooling, CI on Python 3.10 and 3.13, pre-commit hook.
- Licences (MIT for tooling, CC0 1.0 for content), contribution guide, code of conduct,
  security policy, issue and pull request templates, `CITATION.cff`.
- CI runs on pushes to `main` and on pull requests, with GitHub Actions pinned to commit SHAs
  (kept current by Dependabot).

### Changed

- The whole project is in plain English: requirement type is the field `type` (values such as
  `system`, `cybersecurity`, `goal`), level values are `goal`, `top_level`, `system` and
  `component`, and the schema and vocabulary carry English names and meanings only.
- `traces.derives_from` renamed to `traces.parents` (a *derived requirement* usually means one
  created to fill a gap, not one obtained from a parent); "non-functional" wording removed;
  SOL described as product-neutral rather than solution-neutral.

- Split 20 compound `must` statements into atomic records. The original ID keeps the main
  concern; the split-off part has a new ID:
  - SOL: SEC-007 → SEC-008 (break-glass), SEC-006 → SEC-009 (identity propagation),
    SEC-004 → SEC-010 (dynamic client registration), SEC-003 → SEC-011 (step-up),
    SEC-001 → SEC-012 (allowed grants), GW-002 → GW-004 (rate limits and header
    allow-lists), DATA-002 → DATA-003 (masking), CAC-003 → CAC-004 (drift detection),
    DEVX-001 → DEVX-003 (portal self-service), OPS-002 → OPS-003 (failure alerting).
  - IMPL: ARCH-001 → ARCH-003, CAC-001 → CAC-005, CAC-003 → CAC-006, GW-001 → GW-003,
    SEC-001 → DATA-002, SEC-003 → SEC-006, SEC-004 → SEC-007, SEC-005 → SEC-008.
  - PROC: SEC-001 → SEC-009 and CAC-001 → CAC-003 (pass/fail minimum and scored depth are
    now separate records; the scoring moved to the new IDs).
- Split the 9 remaining compound `should` statements the same way: SOL-DATA-001 → DATA-004
  (per-request consent enforcement), SOL-DEVX-002 → DEVX-004 (conformance gate), SOL-GW-003 →
  GW-005 (obligation enforcement), SOL-LCM-002 → LCM-004 (breaking-change classification),
  SOL-LCM-003 → LCM-005 (portal sunset display); IMPL-DATA-001 → DATA-004, IMPL-GW-002 →
  GW-004, IMPL-LCM-001 → LCM-003, IMPL-OBS-001 → OBS-002.
- Reworded 8 statements that describe one behaviour into a single *shall*: SOL-GW-001,
  SOL-LCM-001, SOL-POL-002, IMPL-CAC-002, IMPL-ORG-002, IMPL-ORG-003, IMPL-POL-001,
  IMPL-OPS-001.
- CI fails when `tools/lint.py --strict` reports a non-atomic statement (W05).
- Added PROC-CAC-004, PROC-DEVX-002 (scored; DEVX weight can now be earned) and IMPL-DATA-003,
  IMPL-DEVX-001, IMPL-DEVX-002, IMPL-LCM-002, IMPL-OPS-002, IMPL-SEC-009 and IMPL-SEC-010 so that
  no split-off requirement lost coverage; IMPL-LCM-002 also closes the gap on SOL-LCM-002.
- Re-pointed `traces.satisfies` of existing PROC and IMPL records to the half they evaluate
  or realise.

- W01 now reports only missing procurement coverage; missing implementation coverage is W03.
- PROC scoring weights rebalanced so each area sums to 1.0: PROC-SEC-001 0.4 → 0.6,
  PROC-SEC-002 0.3 → 0.4, PROC-CAC-001 0.5 → 1.0, PROC-POL-001 0.6 → 1.0.

### Fixed

- Lint no longer crashes on schema-invalid records.
- Vague-word check now matches words followed by any punctuation (for example `etc.`).
