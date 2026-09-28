# 04 — Approach assessment

A critical review of *requirements as code* for this baseline: what works, what does not,
which alternatives were considered, and what should change. Written for release
0.1.0-alpha.1 (128 requirements: SOL 53 including 7 goals, PROC 33, IMPL 42). Numbers below are from that
release; re-run `python tools/lint.py --strict` to reproduce them.

## 1. Verdict

**Keep the approach; fix the content discipline.** Plain YAML records, a JSON Schema and a
small domain-specific lint are a good fit for an open, forkable, vendor-neutral baseline of
this size. The weaknesses found were mostly in the *content* (compound statements, repeated
magic numbers, verification cost) and in *checks the lint did not yet make*, not in the
choice of format. No wholesale restructuring is needed. Several fixes are already in this
release (§4); the rest is the roadmap (§5).

## 2. What works

| Strength | Why it matters here |
|---|---|
| One record = one YAML object with explicit fields | Reviewable in a pull request, diffable, and trivially parsed by scripts and AI agents. |
| Three sets (SOL / PROC / IMPL) with mandatory `satisfies` traces | Separates *what* from *how it is bought* from *how it is delivered*, and the lint makes orphaned procurement or delivery requirements impossible. |
| Controlled vocabulary in plain English | Every allowed value is defined once, follows ISO/IEC/IEEE 29148 concepts, and is checked by the lint. |
| Wording lint (single sentence, *shall*, no vague words, no product names in SOL) | Catches the most common defects of tender requirements before review. |
| Git as the lifecycle tool | Status changes are commits, reviews are pull requests: no separate tool, licence or database. |

## 3. Weaknesses found

### 3.1 Fixed in 0.1.0-alpha.1

| Finding | Evidence | Fix |
|---|---|---|
| Schema enums and vocabulary could drift apart; the README claimed the schema was generated from the vocabulary, which was not true. | A new area added to `vocab.yaml` only failed with an unrelated schema error. | Vocabulary is the source of truth; lint validates with vocabulary enums and L13 fails on drift. |
| Coverage check was one-sided. | W01 passed when a SOL record had an IMPL record but was never evaluated in procurement. | W01 (no PROC) and W03 (no IMPL) are now separate. |
| Four `must` SOL records could only lose points, never disqualify an offer. | SOL-GW-001, SOL-LCM-001, SOL-POL-001 and SOL-POL-002 were covered only by `evaluated` PROC records. | Mandatory minimum-bar records PROC-GW-003, PROC-LCM-003, PROC-POL-002 and PROC-POL-003; new check W04. |
| Scoring weights did not add up. | Weights in CAC summed to 0.5, POL to 0.6, SEC to 0.7; area weights existed only as a prose table. | Area weights moved to `vocab.yaml`; L14 enforces sums of 1.0; SEC, CAC and POL rebalanced proportionally. |
| 10 % of the total score could not be earned. | DEVX and OPS carry weight but had no scored PROC record. | Reported as W06; DEVX closed with PROC-DEVX-002, OPS still open (§5). |
| No output a procurement officer can use. | Only YAML existed. | `tools/export.py` writes CSV, catalogue, traceability matrix and scoring sheet. |
| The lint crashed on some schema-invalid records and missed vague words followed by punctuation. | `KeyError: 'priority'`; `etc.` passed. | Defensive checks and whole-word matching, with regression tests in `tests/`. |
| The model had gaps against established requirements-engineering concepts. | No goal records although docs/03 claimed them, so the hierarchy had no top and traceability to stakeholder needs was only the one-way `source` text; the parent field was called `derives_from`, although a *derived requirement* usually means one created to fill a gap; "non-functional" was used although it classifies little; sets had no definition of purpose and extent. | Seven goal records (area GOAL) with every SOL requirement linked up to one (W07); field renamed to `parents`; set definitions (purpose, scope, extent) in the vocabulary; docs/03 maps every requirement and set property to a lint check or a review step. |
| The model mixed two languages. | Field names, type and level values and labels were partly in Swedish. | Everything is plain English: `type`, `level` and all vocabulary values, labels and documentation. |
| Statements were not atomic. | 27 `must` and 10 `should` statements contained more than one *shall*; a vendor meeting half of one was neither clearly compliant nor clearly not. | 29 split into separate records (the original ID keeps the main concern, the split-off part gets a new ID), 8 that describe one behaviour reworded into a single *shall*; new PROC/IMPL records added so that no split-off requirement lost coverage. CI now fails on W05. |

### 3.2 Still open

1. **Atomicity is only checked heuristically.** Every statement now has one *shall* (W05 is
   zero and CI enforces it), but the count misses compounds written with one *shall* and a list
   of verbs or objects (for example PROC-SEC-005 and PROC-DEVX-002 each assess two SOL
   requirements in one demonstration). Atomicity still needs human review.
2. **Parameters are repeated as literals.** "60 seconds" appears 10 times across SOL, PROC
   and IMPL records; similar for 24 hours, 15 minutes and 6 months. A buyer who changes the
   revocation target must find and edit every occurrence consistently.
3. **Verification cost may be disproportionate.** 19 of 20 `mandatory` PROC records require
   a buyer-run demonstration or test. That is expensive for bidders and evaluators and, in
   public procurement law (in Sweden, the Public Procurement Act), must be justified against the
   proportionality principle.
   The baseline does not yet say *when* each check happens (tender, shortlist, or contract
   acceptance).
4. **`source` duplicates `traces.satisfies`** on 36 of 75 PROC/IMPL records, so the two can
   silently diverge.
5. **The priority scale is top-heavy.** 32 of 46 SOL requirements (goals excluded) and 86 of
   128 records overall are `must`. Prioritisation is of limited use when most requirements get
   the highest level, and a scale only works if everyone using it agrees what each level means. Before a tender, the buyer should re-prioritise against its own
   stakeholder needs; a three-level scale where most items are `must` gives evaluators little
   to work with.
6. **Owners and standards are free text.** Ten owner values overlap (`security-team`,
   `security-architecture`, `ciso`; `platform-team`, `platform-operations`) and 29 standard
   strings have no canonical form, so filtering by owner or standard is unreliable.
7. **Sequential IDs collide in parallel pull requests.** Two contributors adding the next
   PROC-SEC record both pick the same number; each PR passes CI and L03 only fails after the
   second merge.
8. **SOL subjects are mixed.** Excluding goals, 35 SOL statements use "The solution", 11 name a component
   ("the gateway", "the portal"). Component subjects are fine for `level: component`, but 7 such
   records are marked `system` or `top_level`.

## 4. Alternatives considered

| Option | Fit for this baseline | Verdict |
|---|---|---|
| Word / Excel tender documents | What procurement teams and tender platforms expect, but no traceability, no lint, merge-hostile. | Keep as an **output** (CSV export), not as the source. |
| Commercial RM tools (DOORS, Jama, Polarion) | Strong traceability and review workflows, but licensed, closed and not forkable; wrong for an open-source baseline. | Support via a ReqIF export if a buyer needs it. |
| **StrictDoc** | Closest open-source match: text-based, traceability, HTML, ReqIF and Excel export, custom grammars. Would replace most of `export.py`. Lacks the domain rules (three sets, scoring weights, Swedish vocabulary) without custom code. | Best migration target if the baseline outgrows the custom tooling. |
| **Doorstop** | YAML file per requirement in Git; avoids merge conflicts and ID collisions; weaker publishing. | Its one-file-per-item layout is worth adopting if contributor volume grows. |
| **sphinx-needs** | Excellent rendered documentation and needs tables; requirements live inside prose, which makes them harder for scripts and agents to consume. | Good for a published handbook generated from the YAML, not as the source. |
| **OSCAL** (NIST) | The SOL set resembles a control catalogue; OSCAL would enable compliance tooling. Heavy for the current size. | Candidate export format later. |
| ReqIF | Exchange format, not an authoring format. | Export target, direct mapping from the YAML fields. |

**Decision:** keep YAML + JSON Schema + lint as the source of truth. Re-evaluate and consider
StrictDoc when any of these becomes true: more than ~300 requirements; the tooling exceeds
~1,000 lines; a buyer needs ReqIF round-trips; or several organisations maintain forks and
need structured merges.

## 5. Roadmap (proposed)

Ordered by value to a buyer using the baseline.

1. **Review atomicity by hand** where one *shall* covers a list (see §3.2 item 1); W05 cannot
   catch those.
2. **Add a `verification_stage`** to PROC records (`tender` self-declaration, `shortlist`
   demonstration, `contract` acceptance test) and move most demonstrations out of the tender
   stage to reduce bidder cost.
3. **Introduce named parameters** (e.g. `revocation_latency: 60 s`) in one file, referenced
   from statements and resolved by the lint and export, so a buyer tunes the baseline in one
   place.
4. **Close remaining coverage gaps**: a scored record for OPS (W06), PROC for SOL-POL-003
   (W01), IMPL for SOL-COM-001 (W03).
5. **Re-prioritise** SOL requirements against the buyer's stakeholder needs before use (§3.2
   item 5), and consider a four-level scale.
6. **Controlled lists for owners and standards** in `vocab.yaml`, checked by the lint.
7. **Deprecate `source` on PROC/IMPL** in favour of `traces.satisfies`.
8. **ReqIF and HTML exports**, or a StrictDoc export, once the content is stable.
9. **ID allocation guidance** (or one file per record) before opening to many contributors.
