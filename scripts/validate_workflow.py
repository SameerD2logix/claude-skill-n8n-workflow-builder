#!/usr/bin/env python3
"""Validate an n8n workflow export (JSON) before importing it.

Checks
  - structure: "nodes" list and "connections" object exist
  - every node has name, type, typeVersion, position [x, y]; names are unique
  - connections only reference nodes that exist, with sane output indexes
  - exactly one trigger node (warning if several, error if none)
  - nodes that nothing connects to (orphans)
  - hardcoded secrets in parameters (API keys, bearer tokens, passwords)
  - simple cycles that would loop forever without a Wait/IF/limit

Usage: python validate_workflow.py workflow.json [--json]
Exit code 0 = no errors, 1 = errors. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass

SECRET_PATTERNS = [
    (re.compile(r"sk-ant-[A-Za-z0-9_-]{10,}"), "Anthropic API key"),
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "API secret key"),
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]{20,}"), "Bearer token"),
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"), "GitHub token"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS access key"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"), "Slack token"),
]
SECRET_KEYS = re.compile(r"(?i)^(password|passwd|api[_-]?key|secret|token|access[_-]?token)$")
LOOP_BREAKERS = ("wait", ".if", ".switch", "splitinbatches", "limit", "filter")


@dataclass
class Finding:
    level: str
    node: str
    message: str


def is_trigger(node_type: str) -> bool:
    t = node_type.lower()
    return t.endswith("trigger") or t.endswith(".webhook") or t.endswith(".cron") or "formtrigger" in t


def walk_params(value, path=""):
    """Yield (path, key, string_value) for every string inside parameters."""
    if isinstance(value, dict):
        for k, v in value.items():
            yield from ((p, kk, vv) for p, kk, vv in walk_params(v, f"{path}.{k}" if path else k))
            if isinstance(v, str):
                yield (f"{path}.{k}" if path else k, k, v)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from walk_params(v, f"{path}[{i}]")


def validate(wf: dict) -> list[Finding]:
    out: list[Finding] = []
    nodes = wf.get("nodes")
    conns = wf.get("connections")
    if not isinstance(nodes, list) or not isinstance(conns, dict):
        return [Finding("error", "-", 'Workflow needs a "nodes" list and a "connections" object')]

    names: dict[str, dict] = {}
    for i, n in enumerate(nodes):
        name = n.get("name") or f"#{i}"
        for field in ("name", "type", "typeVersion", "position"):
            if field not in n:
                out.append(Finding("error", name, f"Missing '{field}'"))
        pos = n.get("position")
        if pos is not None and not (isinstance(pos, list) and len(pos) == 2 and all(isinstance(v, (int, float)) for v in pos)):
            out.append(Finding("error", name, "position must be [x, y] numbers"))
        if name in names:
            out.append(Finding("error", name, "Duplicate node name (connections use names, so this breaks wiring)"))
        names[name] = n

        for path, key, val in walk_params(n.get("parameters", {})):
            if val.startswith("={{") or val.startswith("{{"):
                continue  # expressions are fine
            for rx, label in SECRET_PATTERNS:
                if rx.search(val):
                    out.append(Finding("error", name, f"Hardcoded {label} in parameters.{path}: use n8n credentials"))
                    break
            else:
                if SECRET_KEYS.match(key) and len(val) >= 8:
                    out.append(Finding("warning", name, f"parameters.{path} looks like a secret: use n8n credentials"))

    triggers = [n for n, d in names.items() if is_trigger(str(d.get("type", "")))]
    if not triggers:
        out.append(Finding("error", "-", "No trigger node: the workflow can never start on its own"))
    elif len(triggers) > 1:
        out.append(Finding("warning", "-", f"{len(triggers)} triggers ({', '.join(triggers)}): consider one per workflow"))

    edges: dict[str, set[str]] = {n: set() for n in names}
    targeted: set[str] = set()
    for src, kinds in conns.items():
        if src not in names:
            out.append(Finding("error", src, "Connection from a node that does not exist"))
            continue
        for kind, outputs in (kinds or {}).items():
            for out_idx, targets in enumerate(outputs or []):
                for t in targets or []:
                    dst = t.get("node")
                    if dst not in names:
                        out.append(Finding("error", src, f"Output {out_idx} ({kind}) points to missing node '{dst}'"))
                        continue
                    edges[src].add(dst)
                    targeted.add(dst)

    for n, d in names.items():
        if n not in triggers and n not in targeted and not str(d.get("type", "")).endswith("stickyNote"):
            out.append(Finding("warning", n, "Orphan node: nothing connects to it"))

    # cycle detection (DFS); a cycle is OK only if it contains a loop-breaker node
    state: dict[str, int] = {}

    def dfs(node: str, stack: list[str]) -> None:
        state[node] = 1
        stack.append(node)
        for nxt in edges.get(node, ()):
            if state.get(nxt) == 1:
                cycle = stack[stack.index(nxt):]
                types = " ".join(str(names[c].get("type", "")).lower() for c in cycle)
                if not any(b in types for b in LOOP_BREAKERS):
                    out.append(Finding("error", nxt, f"Endless loop: {' -> '.join(cycle + [nxt])}"))
            elif state.get(nxt) is None:
                dfs(nxt, stack)
        stack.pop()
        state[node] = 2

    for n in names:
        if state.get(n) is None:
            dfs(n, [])
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    with open(args.file, encoding="utf-8") as fh:
        wf = json.load(fh)
    findings = validate(wf)
    errors = sum(f.level == "error" for f in findings)
    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        for f in findings:
            print(f"[{f.level.upper():7}] {f.node}: {f.message}")
        print(f"{len(wf.get('nodes', []))} nodes, {errors} error(s), {len(findings) - errors} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
