# SPDX-License-Identifier: MIT
"""Checks on the documentation that the requirement lint does not cover."""
import pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[1]
BLOCK = re.compile(r"```mermaid\n(.*?)```", re.S)


def sequence_blocks():
    for md in sorted(ROOT.glob("docs/*.md")):
        for i, block in enumerate(BLOCK.findall(md.read_text()), 1):
            if block.lstrip().startswith("sequenceDiagram"):
                yield md.name, i, block


def test_docs_contain_sequence_diagrams():
    assert list(sequence_blocks())


def test_sequence_diagrams_have_no_semicolons():
    # Mermaid treats ";" as a statement separator in sequence diagrams, so a semicolon inside a
    # message breaks the whole diagram on GitHub. Use a comma, or the entity #59; if one is needed.
    bad = [f"{name} block {i}: {line.strip()}" for name, i, block in sequence_blocks()
           for line in block.splitlines() if ";" in line.replace("#59;", "")]
    assert not bad, "\n".join(bad)


def test_sequence_diagrams_have_no_raw_angle_brackets():
    # GitHub may treat <word> as an HTML tag and drop it; use #lt; and #gt; or rephrase.
    bad = [f"{name} block {i}: {line.strip()}" for name, i, block in sequence_blocks()
           for line in block.splitlines() if re.search(r"<[A-Za-z/]", line)]
    assert not bad, "\n".join(bad)
