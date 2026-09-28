# APIM Requirements — an open requirements-as-code baseline for API management

[![CI](https://github.com/jimpe606-maker/apim-requirements/actions/workflows/ci.yml/badge.svg)](https://github.com/jimpe606-maker/apim-requirements/actions/workflows/ci.yml)
![Version](https://img.shields.io/badge/version-0.1.0--alpha.1-orange)
![Status](https://img.shields.io/badge/status-alpha-orange)
![Content licence](https://img.shields.io/badge/content-CC0--1.0-green)
![Tooling licence](https://img.shields.io/badge/tooling-MIT-green)

A vendor-neutral reference architecture and a structured, checked set of requirements for
**procuring and implementing an API management (APIM) platform** built on **zero trust**,
**OAuth 2.1 / FAPI 2.0** and **configuration as code** (no click-ops: every change goes
through CI/CD, with linting and policy checks).

Use it as a starting point for your own tender, architecture review or platform backlog:
fork it, adjust priorities and weights to your context, run the checks, and export the
result to the formats your procurement process needs.

> **Alpha.** All 128 requirements are `draft`. They have been checked by tooling, not yet by
> an independent peer and security review. Expect wording, IDs and weights to change before
> 1.0. See [docs/04](docs/04-approach-assessment.md) for known weaknesses and the roadmap.

## Who it is for

| You are | Start with |
|---|---|
| A buyer preparing a tender | `build/scoring.md` and `build/requirements.csv` after running the export, then the PROC records |
| An architect | [docs/01 — Reference architecture](docs/01-reference-architecture.md) and the SOL records |
| A platform or delivery team | [docs/02 — Use cases](docs/02-use-cases-sequences.md) and the IMPL records |
| A vendor | The SOL and PROC records, to see what is asked and how it is verified |
| An AI agent or script | `.claude/skills/requirements-authoring/SKILL.md`, then `schema/requirement.schema.json`, `schema/vocab.yaml` and `requirements/**.yaml` |

## Quick start

Requires Python 3.10 or later.

```bash
pip install -r requirements.txt
python tools/lint.py             # schema, IDs, traces, wording, coverage and scoring checks
python tools/export.py           # writes build/requirements.csv, catalogue.md, traceability.md, scoring.md
```

`python tools/lint.py --strict` also lists statements that bundle several requirements.

## How the baseline is organised

Each concern is written three times, once per **requirement set**, with a
different subject and verb:

| Set | Question it answers | Subject and verb | Count |
|---|---|---|---|
| **SOL** Solution | *What* must the system be or do? A hierarchy from 7 goals down to component level; product-neutral. | "The solution shall provide…" | 53 |
| **PROC** Procurement | *How* is an offer qualified, checked and scored against SOL? | "The offer shall demonstrate / be scored on…" | 33 |
| **IMPL** Implementation | *How* does the buyer's organisation realise and operate it? | "The pipeline / team shall…" | 42 |

Every PROC and IMPL record traces to at least one SOL record, and every `must` SOL record has
a pass/fail PROC record that can disqualify an offer. Example chain:

```
SOL-GW-001    The gateway shall forward a request only after validating the access token and its sender constraint (DPoP or mTLS) …
 ├─ PROC-GW-003   mandatory: every invalid token or failed proof → HTTP 401, else the offer is rejected
 ├─ PROC-SEC-002  evaluated: 0–5 points for how natively the product does it
 ├─ IMPL-SEC-001  the pipeline applies the FAPI 2.0 policy bundle to every API classified as sensitive
 └─ IMPL-CAC-002  the pipeline lints the contract and verifies policy before deployment
```

SOL is one requirement hierarchy: seven **goals** (area GOAL, for example *zero-trust access to
every API* and *every change made as reviewed code*) at the top, and every other SOL requirement
linked to its parent with `traces.parents`, so each requirement can be traced up to the stakeholder
need behind it.

Requirements are grouped in twelve **areas** (ARCH, GW, SEC, LCM, DEVX, CAC, POL, OBS, OPS,
DATA, ORG, COM), each with a procurement weight in `schema/vocab.yaml`. Concepts follow
ISO/IEC/IEEE 29148. The full model is in
[docs/03 — Requirement model](docs/03-requirement-model.md).

## Repository layout

```
docs/
  01-reference-architecture.md   components C1–C17, context diagram, trust boundaries, standards
  02-use-cases-sequences.md      UC-01 … UC-07 as sequence diagrams with step descriptions
  03-requirement-model.md        requirement model: concepts, sets, fields, writing rules, properties
  04-approach-assessment.md      critique of the approach, alternatives, roadmap
schema/
  requirement.schema.json        JSON Schema for a requirement file
  vocab.yaml                     controlled vocabulary (EN/SV) and area weights: source of truth
requirements/
  solution/goal.yaml             SOL goals (top of the hierarchy)
  solution/*.yaml                SOL records, one file per area
  procurement/*.yaml             PROC records
  implementation/*.yaml          IMPL records
tools/
  lint.py                        checks L01–L14 (errors) and W01–W07 (warnings)
  export.py                      CSV, catalogue, traceability matrix, scoring sheet
tests/                           regression tests for the tooling
.claude/skills/
  requirements-authoring/        instructions for AI agents that write or review requirements
```

## Using it for your own procurement

1. Fork the repository.
2. Adjust `priority` on SOL records and `weight` on areas (`schema/vocab.yaml`) and PROC
   records to your context. The lint keeps weights consistent.
3. Remove or retire (`status: retired`) what does not apply; add what is missing.
4. Run `python tools/lint.py` until it reports 0 errors, then `python tools/export.py`.
5. Import `build/requirements.csv` into your tender platform or spreadsheet.

The baseline does not replace legal review. Check requirements, verification methods and
scoring against the procurement law that applies to you (in Sweden, the Public Procurement Act) — in particular the
proportionality of requiring live demonstrations; see
[docs/04 §3.2](docs/04-approach-assessment.md#32-still-open).

## Status

`python tools/lint.py` → 128 requirements, 0 errors, 3 warnings. The warnings are known gaps,
each a good first contribution:

* No scored PROC record for the OPS area, so its 5 % weight cannot be earned (W06).
* No PROC record for SOL-POL-003 (W01).
* No IMPL record for SOL-COM-001 (W03).

Every statement has exactly one *shall* (`--strict` reports no W05, and CI enforces it);
statements that bundle a list under one *shall* still need human review. See the [roadmap](docs/04-approach-assessment.md#5-roadmap-proposed) and
[CHANGELOG](CHANGELOG.md).

## Contributing

Contributions from buyers, vendors, architects and security specialists are welcome. Read
[CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md). Report
requirements that could lead to insecure systems privately, as described in
[SECURITY.md](SECURITY.md).

## License

Free to use for any purpose, commercial or not, including copying requirements into your
own tender documents.

| What | Licence | Attribution required |
|---|---|---|
| Requirements, documentation, schema and vocabulary (`requirements/`, `docs/`, `schema/`, Markdown files) | [CC0 1.0 Universal](LICENSE-CONTENT) (public domain dedication) | No |
| Tooling and tests (`tools/`, `tests/`, `.github/`) | [MIT](LICENSE) | Keep the licence notice when redistributing the code |

Attribution is appreciated but never required for the content.

Third-party material: referenced standards (ISO, IETF, OpenID Foundation and others) and other
sources listed in [docs/03 §11](docs/03-requirement-model.md#11-references) remain under their
own terms; no text from them is reproduced here.
