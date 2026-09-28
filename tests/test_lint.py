# SPDX-License-Identifier: MIT
"""Regression tests for tools/lint.py and tools/export.py.

Each test runs against a copy of the repository in a temporary directory, so the
real baseline is never modified.
"""
import csv, pathlib, re, shutil, sys
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from lint import lint          # noqa: E402
import export                  # noqa: E402


@pytest.fixture
def repo(tmp_path):
    for d in ("schema", "requirements", "docs"):
        shutil.copytree(ROOT / d, tmp_path / d)
    shutil.copy(ROOT / "VERSION", tmp_path / "VERSION")
    return tmp_path


def codes(res):
    return {m.split()[1] for m in res.errors}


def edit(path, old, new):
    text = path.read_text()
    assert old in text, f"fixture text not found in {path.name}: {old!r}"
    path.write_text(text.replace(old, new, 1))


def test_baseline_is_clean():
    res = lint(ROOT)
    assert res.errors == []
    assert len(res.records) > 0


def test_vocab_only_area_is_schema_drift(repo):
    edit(repo / "schema/vocab.yaml", "  COM:  {", "  INT:  { name: Integration, weight: 0 }\n  COM:  {")
    res = lint(repo)
    assert [m for m in res.errors if " L13 " in m and "properties/area" in m]
    assert [m for m in res.errors if " L13 " in m and "$defs/id pattern" in m]


def test_vocab_and_schema_updated_together_is_clean(repo):
    edit(repo / "schema/vocab.yaml", "  COM:  {", "  INT:  { name: Integration, weight: 0 }\n  COM:  {")
    edit(repo / "schema/requirement.schema.json", '"ORG","COM"]', '"ORG","INT","COM"]')
    edit(repo / "schema/requirement.schema.json", "ORG|COM)-", "ORG|INT|COM)-")
    assert lint(repo).errors == []


def test_schema_invalid_record_reports_instead_of_crashing(repo):
    f = repo / "requirements/procurement/arch.yaml"
    text = f.read_text()
    f.write_text(re.sub(r"\n    priority: must", "", text, count=1))
    res = lint(repo)
    assert {"L01", "L11"} <= codes(res)


@pytest.mark.parametrize("phrase,word", [
    ("and so on, etc.", "etc"),
    ("a fast; reliable path", "fast"),
    ("a (robust) path", "robust"),
    ("Easy path", "easy"),
    ("input and/or output", "and/or"),
])
def test_weasel_words_detected_with_any_punctuation(repo, phrase, word):
    edit(repo / "requirements/solution/com.yaml", "statement: The solution shall",
         f"statement: The solution shall use {phrase} and")
    assert any(f"weasel word '{word}'" in m for m in lint(repo).errors)


@pytest.mark.parametrize("phrase", ["a fast-track path", "a breakfast path", "an efficiently tuned path"])
def test_weasel_words_ignore_substrings(repo, phrase):
    edit(repo / "requirements/solution/com.yaml", "statement: The solution shall",
         f"statement: The solution shall use {phrase} and")
    assert not any("weasel word" in m for m in lint(repo).errors)


def test_area_scoring_weights_must_sum_to_one(repo):
    edit(repo / "requirements/procurement/pol.yaml", "weight: 1.0", "weight: 0.6")
    assert any(" L14 " in m and "POL scoring weights" in m for m in lint(repo).errors)


def test_vocab_area_weights_must_sum_to_one(repo):
    edit(repo / "schema/vocab.yaml", "weight: 0.25", "weight: 0.3")
    assert any(" L14 " in m and "area weights sum" in m for m in lint(repo).errors)


def test_must_without_passfail_proc_warns(repo):
    edit(repo / "requirements/procurement/lcm.yaml", "satisfies: [SOL-LCM-001]", "satisfies: [SOL-LCM-002]")
    res = lint(repo)
    assert res.errors == []
    assert any("SOL-LCM-001 W04" in m for m in res.warnings)


def test_baseline_statements_are_atomic():
    assert not any(" W05 " in m for m in lint(ROOT, strict=True).warnings)


def test_strict_reports_compound_statements(repo):
    edit(repo / "requirements/solution/com.yaml", "statement: The solution shall",
         "statement: The solution shall log exits and shall")
    assert not any(" W05 " in m for m in lint(repo).warnings)
    assert any("SOL-COM-001 W05" in m for m in lint(repo, strict=True).warnings)


def test_export_writes_all_formats(tmp_path):
    assert export.main(["--out", str(tmp_path)]) == 0
    for name in ("requirements.csv", "catalogue.md", "traceability.md", "scoring.md"):
        assert (tmp_path / name).stat().st_size > 0
    with (tmp_path / "requirements.csv").open(encoding="utf-8-sig") as f:
        assert len(list(csv.DictReader(f))) == len(lint(ROOT).records)


def test_export_refuses_inconsistent_baseline(repo, tmp_path):
    edit(repo / "requirements/procurement/pol.yaml", "weight: 1.0", "weight: 0.6")
    assert export.main(["--root", str(repo), "--out", str(tmp_path / "out")]) == 1


def test_requirement_not_tracing_to_a_goal_warns(repo):
    edit(repo / "requirements/solution/ops.yaml", "parents: [SOL-GOAL-005]\n", "")
    res = lint(repo)
    assert res.errors == []
    assert any("SOL-OPS-001 W07" in m for m in res.warnings)


def test_goal_without_children_warns(repo):
    edit(repo / "requirements/solution/obs.yaml", "parents: [SOL-GOAL-006, SOL-GOAL-007]", "parents: [SOL-GOAL-006]")
    edit(repo / "requirements/solution/com.yaml", "parents: [SOL-CAC-001, SOL-GOAL-007]", "parents: [SOL-CAC-001]")
    assert any("SOL-GOAL-007 W07" in m for m in lint(repo).warnings)


def test_goals_are_exempt_from_coverage_warnings():
    assert not any("SOL-GOAL-" in m and (" W01 " in m or " W03 " in m or " W04 " in m) for m in lint(ROOT).warnings)
