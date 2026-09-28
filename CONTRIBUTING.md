# Contributing

Thank you for helping improve the baseline. Contributions from buyers, vendors, architects,
security specialists and procurement professionals are all welcome.

By contributing you agree that your contribution is licensed under the same terms as the
file you change: CC0 1.0 for requirements, documentation, schema and vocabulary, and MIT for
the tooling (see [README](README.md#license)).

## Ways to contribute

* **Report a problem with a requirement**: ambiguous, not verifiable, wrong standard
  reference, product-specific in a SOL record. Use the *Requirement change* issue template.
* **Propose a new requirement or area**: open an issue first so the placement (set, area,
  priority) can be agreed before you write it.
* **Improve the tooling**: lint rules, exports, tests.
* **Share how you used the baseline** in a real procurement: what worked, what vendors
  struggled with. This is the most valuable feedback for an alpha.

Vendors are welcome to contribute, but please keep SOL records solution-neutral and disclose
your affiliation in the pull request.

## Workflow

1. Fork and create a branch.
2. Set up the tools (Python 3.10 or later):

   ```bash
   pip install -r requirements-dev.txt
   pre-commit install          # optional: runs the lint before each commit
   ```

3. Make your change. For a new requirement, copy an existing record in the right
   `requirements/<set>/<area>.yaml`, take the next free ID and fill every field. A new SOL
   requirement needs a parent (`traces.parents`) that leads up to a goal in
   `requirements/solution/goal.yaml`. If you use an AI agent, point it to
   `.claude/skills/requirements-authoring/SKILL.md`.
4. Run the checks:

   ```bash
   python tools/lint.py             # must report 0 errors
   python tools/lint.py --strict    # new records should not add W05 (non-atomic) warnings
   pytest -q
   ```

5. Open a pull request using the template. The pull request is the review record for the
   requirement lifecycle (`draft` → `reviewed` → `approved`).

## Writing rules in short

The full rules are in [docs/03](docs/03-requirement-model.md#6-writing-rules).

* One requirement per record, one sentence, one *shall*, using an EARS template.
* Write in plain English and use the terms defined in `schema/vocab.yaml` and
  [docs/03](docs/03-requirement-model.md). Do not copy definitions from standards or other
  copyrighted sources; describe them in your own words and cite the source.
* No vague words (see `schema/vocab.yaml#weasel_words`), no "and/or", no product names in SOL.
* At least one acceptance criterion that someone other than the author can execute.
* Every PROC and IMPL record traces to at least one SOL record (`traces.satisfies`).
* Every `must` SOL record needs a `mandatory` or `qualification` PROC record.
* PROC scoring weights within an area sum to 1.0.
* IDs are never reused. Retire a record with `status: retired` instead of deleting it.

## IDs and parallel pull requests

IDs are sequential per set and area, so two open pull requests can pick the same number.
CI on the second one to merge will fail with L03. Rebase and renumber your records; mention
the renumbering in the pull request so reviewers can follow.

## Releases

The baseline follows [Semantic Versioning](https://semver.org/) for its *content*: a
**major** release changes the meaning of an existing requirement or removes one, a **minor**
release adds requirements or fields, a **patch** release fixes wording without changing
meaning. While the version is `0.x`, any release may change meaning. Record changes in
[CHANGELOG.md](CHANGELOG.md) and update `VERSION`.
