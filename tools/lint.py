#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Requirements lint.

Usage: python tools/lint.py [--strict] [--root PATH]

Checks (all fail the build):
  L01 file validates against schema/requirement.schema.json (enums taken from vocab.yaml)
  L02 file-level set/area match every record id prefix
  L03 ids unique across the whole repository
  L04 every trace target exists (parents, satisfies, related)
  L05 PROC and IMPL records have >=1 `satisfies` pointing to a SOL record
  L06 SOL records have no `satisfies` (they are the top of the chain)
  L07 parents stay inside the same set
  L08 `procurement` block present iff set == PROC
  L09 PROC evaluated / priority should|could -> scoring required; qualification -> no scoring
  L10 statement: single sentence, contains ' shall ', no weasel words, no product names in SOL
  L11 record enum values exist in schema/vocab.yaml
  L12 allocated_to components exist in vocab
  L13 schema enums and id pattern match schema/vocab.yaml (vocab is the source of truth)
  L14 scoring weights sum to 1.0: area weights in vocab, and PROC weights within each area
Warnings (do not fail):
  W01 SOL record not evaluated by any PROC record (procurement coverage gap)
  W02 use_case referenced in traces does not appear in docs/02
  W03 SOL record not realised by any IMPL record (implementation coverage gap)
  W04 `must` SOL record without a mandatory or qualification PROC record (cannot disqualify)
  W05 statement contains more than one 'shall' (not atomic) -- reported only with --strict
  W06 area has a procurement weight in vocab but no scored PROC record (weight cannot be earned)
  W07 SOL hierarchy: a requirement that does not trace up to a goal (type: goal) through
      `parents`, or a goal without child requirements
Goals (type: goal) are realised through their children, so W01, W03 and W04 skip them.
"""
import argparse, json, re, sys, pathlib
from dataclasses import dataclass, field
import yaml
from jsonschema import Draft202012Validator

DEFAULT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA_FILE = "schema/requirement.schema.json"
PRODUCT_NAMES = re.compile(r"\b(apigee|kong|tyk|mulesoft|gravitee|azure apim|aws api gateway|okta|auth0|keycloak|ping|curity|forgerock|wso2|3scale)\b", re.I)
RECORD_ENUMS = (("layer", "layers"), ("type", "types"), ("level", "levels"),
                ("priority", "priorities"), ("verification", "verification_methods"), ("status", "statuses"))


@dataclass
class Result:
    records: dict = field(default_factory=dict)   # id -> (relative file, record, set)
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    vocab: dict = field(default_factory=dict)

    def err(self, f, rid, code, msg): self.errors.append(f"{f}:{rid or '-'} {code} {msg}")
    def warn(self, f, rid, code, msg): self.warnings.append(f"{f}:{rid or '-'} {code} {msg}")


def load_schema(root, vocab, res):
    """Return the schema with enums replaced by vocab values; report drift as L13."""
    schema = json.loads((root / SCHEMA_FILE).read_text())
    req = schema["$defs"]["requirement"]["properties"]
    enum_sources = {                      # schema path -> (schema node, vocab key)
        "properties/set":                     (schema["properties"]["set"], "sets"),
        "properties/area":                    (schema["properties"]["area"], "areas"),
        "$defs/requirement/.../layer":        (req["layer"], "layers"),
        "$defs/requirement/.../type":         (req["type"], "types"),
        "$defs/requirement/.../level":        (req["level"], "levels"),
        "$defs/requirement/.../priority":     (req["priority"], "priorities"),
        "$defs/requirement/.../verification": (req["verification"], "verification_methods"),
        "$defs/requirement/.../status":       (req["status"], "statuses"),
        "$defs/requirement/.../procurement/kind": (req["procurement"]["properties"]["kind"], "procurement_kinds"),
    }
    for path, (node, key) in enum_sources.items():
        expected = list(vocab[key])
        if set(node.get("enum", [])) != set(expected):
            res.err(SCHEMA_FILE, None, "L13", f"{path} enum {node.get('enum')} != vocab.{key} {expected}")
        node["enum"] = expected
    id_pattern = f"^({'|'.join(vocab['sets'])})-({'|'.join(vocab['areas'])})-[0-9]{{3}}$"
    m = re.fullmatch(r"\^\((.*)\)-\((.*)\)-\[0-9\]\{3\}\$", schema["$defs"]["id"]["pattern"])
    if not m or set(m[1].split("|")) != set(vocab["sets"]) or set(m[2].split("|")) != set(vocab["areas"]):
        res.err(SCHEMA_FILE, None, "L13", f"$defs/id pattern != vocab sets/areas, expected {id_pattern}")
    schema["$defs"]["id"]["pattern"] = id_pattern
    return schema


def load_records(root, schema, res):
    validator = Draft202012Validator(schema)
    for f in sorted((root / "requirements").rglob("*.yaml")):
        rel = f.relative_to(root)
        data = yaml.safe_load(f.read_text())
        for e in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
            res.err(rel, None, "L01", f"schema: {'/'.join(map(str, e.path))}: {e.message}")
        if not isinstance(data, dict): continue
        s, a = data.get("set"), data.get("area")
        for r in data.get("requirements") or []:
            if not isinstance(r, dict): continue          # already reported by L01
            rid = r.get("id", "")
            if not rid.startswith(f"{s}-{a}-"):
                res.err(rel, rid, "L02", f"id prefix does not match file set/area {s}-{a}")
            if rid in res.records:
                res.err(rel, rid, "L03", f"duplicate id (also in {res.records[rid][0]})")
            res.records[rid] = (rel, r, s)


def check_record(rid, rel, r, s, ctx, res, strict):
    vocab = res.vocab
    # records that failed L01 are still checked, so read every field defensively
    tr = r.get("traces") if isinstance(r.get("traces"), dict) else {}
    for key in ("parents", "satisfies", "related"):
        for t in tr.get(key, []) or []:
            if t not in res.records:
                res.err(rel, rid, "L04", f"{key} -> {t} does not exist")
            elif key == "satisfies":
                if not t.startswith("SOL-"):
                    res.err(rel, rid, "L05", f"satisfies must point to SOL, got {t}")
                ctx["covered"][s].add(t)
                if s == "PROC" and isinstance(r.get("procurement"), dict) \
                        and r["procurement"].get("kind") in ("mandatory", "qualification"):
                    ctx["covered"]["PROC-passfail"].add(t)
            elif key == "parents" and not t.startswith(s + "-"):
                res.err(rel, rid, "L07", f"parents must stay in set {s}, got {t}")
    if s in ("PROC", "IMPL") and not tr.get("satisfies"):
        res.err(rel, rid, "L05", "PROC/IMPL record must satisfy >=1 SOL requirement")
    if s == "SOL" and tr.get("satisfies"):
        res.err(rel, rid, "L06", "SOL record must not have satisfies")

    has_proc = "procurement" in r
    if s == "PROC" and not has_proc:
        res.err(rel, rid, "L08", "PROC record requires procurement block")
    if s != "PROC" and has_proc:
        res.err(rel, rid, "L08", "procurement block only allowed in PROC")
    if has_proc:
        proc = r["procurement"] if isinstance(r["procurement"], dict) else {}
        kind, scoring = proc.get("kind"), proc.get("scoring")
        if kind == "evaluated" and not scoring:
            res.err(rel, rid, "L09", "evaluated requirement needs scoring")
        if kind == "qualification" and scoring:
            res.err(rel, rid, "L09", "qualification requirement is pass/fail, remove scoring")
        if r.get("priority") == "must" and kind == "evaluated":
            res.err(rel, rid, "L09", "priority must => kind mandatory or qualification")
        if r.get("priority") != "must" and kind == "mandatory":
            res.err(rel, rid, "L09", "kind mandatory => priority must")
        if isinstance(scoring, dict) and isinstance(scoring.get("weight"), (int, float)):
            area = rid.split("-")[1] if rid.count("-") == 2 else "?"
            ctx["weights"].setdefault(area, []).append((rid, scoring["weight"]))

    st = r.get("statement") if isinstance(r.get("statement"), str) else ""
    if " shall " not in st:
        res.err(rel, rid, "L10", "statement must use 'shall'")
    if len(re.findall(r"[.!?](\s|$)", st.replace("e.g.", "eg").replace("i.e.", "ie"))) > 1:
        res.err(rel, rid, "L10", "statement must be a single sentence")
    low = st.lower()
    for w in ctx["weasel"]:
        # whole word or phrase, whatever punctuation follows ("etc.", "fast;", "robust)")
        if re.search(rf"(?<![\w-]){re.escape(w)}(?![\w-])", low):
            res.err(rel, rid, "L10", f"weasel word '{w}'")
    if s == "SOL" and PRODUCT_NAMES.search(st):
        res.err(rel, rid, "L10", "SOL statement must not name a product")
    if strict and len(re.findall(r"\bshall\b", st)) > 1:
        res.warn(rel, rid, "W05", "statement contains more than one 'shall'; consider splitting")

    for fld, key in RECORD_ENUMS:
        if r.get(fld) not in vocab[key]:
            res.err(rel, rid, "L11", f"{fld}={r.get(fld)} not in vocab.{key}")
    for c in r.get("allocated_to") or []:
        if c not in vocab["components"]:
            res.err(rel, rid, "L12", f"allocated_to {c} not in vocab.components")
    for uc in tr.get("use_cases", []) or []:
        if f"## {uc}" not in ctx["uc_text"]:
            res.warn(rel, rid, "W02", f"{uc} not found in docs/02")


def check_weights(ctx, res):
    area_weights = {a: (v or {}).get("weight") for a, v in res.vocab["areas"].items()}
    missing = [a for a, w in area_weights.items() if not isinstance(w, (int, float))]
    if missing:
        res.err("schema/vocab.yaml", None, "L14", f"areas without numeric weight: {', '.join(missing)}")
    elif abs(sum(area_weights.values()) - 1.0) > 1e-6:
        res.err("schema/vocab.yaml", None, "L14", f"area weights sum to {sum(area_weights.values()):.3f}, expected 1.0")
    for area, w in area_weights.items():
        if isinstance(w, (int, float)) and w > 0 and area not in ctx["weights"]:
            res.warn("schema/vocab.yaml", None, "W06", f"area {area} has weight {w} but no scored PROC record")
    for area, items in sorted(ctx["weights"].items()):
        total = sum(w for _, w in items)
        if abs(total - 1.0) > 1e-6:
            ids = ", ".join(f"{rid}={w}" for rid, w in items)
            res.err(f"requirements/procurement/{area.lower()}.yaml", None, "L14",
                    f"{area} scoring weights sum to {total:.3f}, expected 1.0 ({ids})")


def check_hierarchy(res):
    """W07: every SOL requirement traces up to a goal; every goal has children."""
    sol = {rid: r for rid, (_, r, s) in res.records.items() if s == "SOL" and r.get("status") != "retired"}
    def parents(rid):
        tr = sol[rid].get("traces") if isinstance(sol[rid].get("traces"), dict) else {}
        return [p for p in tr.get("parents", []) or [] if p in sol]
    def reaches_goal(rid, seen=()):
        if sol[rid].get("type") == "goal":
            return True
        return any(p not in seen and reaches_goal(p, seen + (rid,)) for p in parents(rid))
    children = {p for rid in sol for p in parents(rid)}
    for rid, r in sol.items():
        rel = res.records[rid][0]
        if r.get("type") == "goal":
            if rid not in children:
                res.warn(rel, rid, "W07", "goal has no child requirements")
        elif not reaches_goal(rid):
            res.warn(rel, rid, "W07", "requirement does not trace up to a goal through parents")


def lint(root=DEFAULT_ROOT, strict=False):
    root = pathlib.Path(root)
    res = Result()
    res.vocab = yaml.safe_load((root / "schema/vocab.yaml").read_text())
    schema = load_schema(root, res.vocab, res)
    load_records(root, schema, res)
    ctx = {
        "uc_text": (root / "docs/02-use-cases-sequences.md").read_text(),
        "weasel": [w.lower() for w in res.vocab["weasel_words"]],
        "covered": {"PROC": set(), "IMPL": set(), "PROC-passfail": set()},
        "weights": {},
    }
    for rid, (rel, r, s) in res.records.items():
        check_record(rid, rel, r, s, ctx, res, strict)
    check_weights(ctx, res)
    check_hierarchy(res)
    for rid, (rel, r, s) in res.records.items():
        if s != "SOL" or r.get("status") == "retired" or r.get("type") == "goal":
            continue
        if rid not in ctx["covered"]["PROC"]:
            res.warn(rel, rid, "W01", "SOL requirement not evaluated by any PROC record")
        if rid not in ctx["covered"]["IMPL"]:
            res.warn(rel, rid, "W03", "SOL requirement not realised by any IMPL record")
        if r.get("priority") == "must" and rid in ctx["covered"]["PROC"] \
                and rid not in ctx["covered"]["PROC-passfail"]:
            res.warn(rel, rid, "W04", "must requirement has no mandatory or qualification PROC record")
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--strict", action="store_true", help="also report W05 (non-atomic statements)")
    ap.add_argument("--root", type=pathlib.Path, default=DEFAULT_ROOT, help="repository root")
    args = ap.parse_args(argv)
    res = lint(args.root, args.strict)
    counts = {}
    for _, _, s in res.records.values():
        counts[s] = counts.get(s, 0) + 1
    version = (args.root / "VERSION").read_text().strip() if (args.root / "VERSION").exists() else "unversioned"
    print(f"baseline {version}: {len(res.records)} requirements: "
          + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    for w in res.warnings: print("WARN ", w)
    for e in res.errors: print("ERROR", e)
    print(f"{len(res.errors)} error(s), {len(res.warnings)} warning(s)")
    return 1 if res.errors else 0


if __name__ == "__main__":
    sys.exit(main())
