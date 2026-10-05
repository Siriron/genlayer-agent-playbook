#!/usr/bin/env python3
"""
audit_contract.py — automates the mechanical half of the mandatory pre-handoff nondet audit
(docs/knowledge/06 point 8, docs/knowledge/04, docs/knowledge/03).

Usage:  python scripts/audit_contract.py path/to/contract.py

Exit code 0 = no mechanical failures; 1 = at least one FAIL. WARN items need human review.
This script does NOT replace:
  * `genvm-lint check <contract.py>`  (run it too; must pass with no errors)
  * the verdict-enum reachability trace (list every verdict value, name the leader_fn branch producing it)
  * the unit/direct-mode tests (`pytest tests -q -p no:cacheprovider`)
"""
import ast
import re
import sys

PIN = 'py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6'
fails, warns = [], []


def fail(msg):
    fails.append(msg)


def warn(msg):
    warns.append(msg)


def code_lines(src):
    """(lineno, text) with full-line comments removed and trailing comments stripped (naive but adequate)."""
    for n, line in enumerate(src.splitlines(), 1):
        s = line.strip()
        if s.startswith("#"):
            continue
        yield n, re.sub(r"\s+#.*$", "", line)


def main(path):
    src = open(path, encoding="utf-8").read()
    first = src.splitlines()[0] if src else ""

    # 1. pinned pragma
    if PIN not in first:
        fail(f"line 1 must be the pinned runner comment ({PIN}); got: {first[:100]!r}")
    if "py-genlayer:test" in src:
        fail('"py-genlayer:test" found — rejected by current Studio (absent_runner_comment)')

    # 2. textual greps (Bug 3, Bug 1, TIER 1 float rule, Bug 2 keywords, Bug 7, Bug 8)
    for n, line in code_lines(src):
        if re.search(r"\.send\(", line):
            fail(f"L{n}: .send( — does not exist on ContractAt; use .emit_transfer(value=...)  [Bug 3]")
        if "status_code" in line:
            fail(f"L{n}: status_code — SDK Response has .status; status_code is always None  [Bug 1]")
        if re.search(r"\bfloat\(", line):
            fail(f"L{n}: float( — banned anywhere nondet-reachable, even transiently  [TIER 1]")
        if re.search(r"run_nondet_unsafe\s*\([^)]*(leader_fn|validator_fn)\s*=", line):
            fail(f"L{n}: run_nondet_unsafe called with keyword args — must be positional  [Bug 2]")
        if re.search(r"json\.loads\(\s*(leaders_res|result|leader_data|my_data)\b", line):
            fail(f"L{n}: json.loads on an already-decoded nondet value  [Bug 2]")
        if re.search(r"DynArray\[[^\]]*\]\s*\(", line) or re.search(r"inmem_allocate\(\s*DynArray", line):
            fail(f"L{n}: explicit DynArray construction raises live  [Bug 7]")
        if re.search(r'message_raw\[[\'"]datetime[\'"]\]', line) and re.search(r"\bint\(", line):
            fail(f"L{n}: int() on message_raw['datetime'] — it is an ISO-8601 string  [Bug 8]")
        if "datetime.datetime.now" in line:
            warn(f"L{n}: datetime.now() — Bug 12 alternative is spec-supported but not live-confirmed; default is _now_epoch_seconds()")
        if "gl.message.sender_account" in line or "gl.UserError" in line or "gl.get_webpage" in line or "gl.exec_prompt" in line:
            fail(f"L{n}: wrong SDK name (use sender_address / gl.vm.UserError / gl.nondet.web.get / gl.nondet.exec_prompt)  [section 14]")
        if "eq_principle.prompt_comparative" in line:
            warn(f"L{n}: prompt_comparative — its principle must name exactly the keys in the canonical output, verdict first  [section 16.2]")
        if "strict_eq" in line:
            fail(f"L{n}: strict_eq on LLM output — consensus always fails")

    # 3. AST checks
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        fail(f"does not parse as Python (template placeholders left in?): {e}")
        return report()

    # 3a. self inside leader_fn / validator_fn (Bug 6) and storage reads in them (Bug 4)
    nondet_names = {"leader_fn", "validator_fn"}
    found_nondet = False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in nondet_names:
            found_nondet = True
            for sub in ast.walk(node):
                if isinstance(sub, ast.Name) and sub.id == "self":
                    fail(f"L{sub.lineno}: `self` referenced inside {node.name}  [Bug 6/Bug 4]")
                if isinstance(sub, ast.Attribute) and isinstance(sub.value, ast.Name) and sub.value.id == "gl" and sub.attr == "storage":
                    warn(f"L{sub.lineno}: gl.storage used inside {node.name} — copy_to_memory belongs in the plain body before run_nondet_unsafe")
            # validator must check gl.vm.Return
            if node.name == "validator_fn":
                txt = ast.get_source_segment(src, node) or ""
                if "gl.vm.Return" not in txt:
                    fail(f"L{node.lineno}: validator_fn never checks isinstance(leaders_res, gl.vm.Return)  [Bug 2]")
                if "leaders_res.calldata" not in txt:
                    warn(f"L{node.lineno}: validator_fn does not read leaders_res.calldata")
                if "leader_fn()" not in txt:
                    warn(f"L{node.lineno}: validator_fn does not call leader_fn() — leader-output-only validators are rejected (re-derive and compare)")
    # run_nondet_unsafe presence
    uses_nondet = "run_nondet_unsafe" in src
    if uses_nondet and not found_nondet:
        warn("run_nondet_unsafe used but no nested leader_fn/validator_fn found — if they are named differently or are methods, re-check Bug 6 by hand")
    if uses_nondet and "copy_to_memory" not in src:
        fail("run_nondet_unsafe used but gl.storage.copy_to_memory never called  [Bug 4]")

    # 3b. nested helper containing gl.nondet.* (lint E010) and unreachable module helpers
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name not in nondet_names:
            # nested function inside a method?
            pass
    for cls in [n for n in tree.body if isinstance(n, ast.ClassDef)]:
        for meth in [m for m in cls.body if isinstance(m, ast.FunctionDef)]:
            for inner in [i for i in ast.walk(meth) if isinstance(i, ast.FunctionDef) and i is not meth and i.name not in nondet_names]:
                seg = ast.get_source_segment(src, inner) or ""
                if "gl.nondet" in seg:
                    fail(f"L{inner.lineno}: nested helper `{inner.name}` contains gl.nondet.* — genvm-lint E010; inline into leader_fn or hoist to module level")
        # 3c. class-body annotated attributes (Bug 5)
        for stmt in cls.body:
            if isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
                warn(f"L{stmt.lineno}: class-body annotated attribute `{ast.unparse(stmt.target)}` has a default value — if it is a constant it must live at module level  [Bug 5]")

    # 3d. module-level helpers that call gl.nondet but nothing reaches them -> E010 (heuristic)
    called = {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            seg = ast.get_source_segment(src, node) or ""
            if "gl.nondet" in seg and node.name not in called:
                fail(f"L{node.lineno}: module helper `{node.name}` uses gl.nondet.* but is never called — genvm-lint E010; delete or uncomment-only-when-used")

    # 3e. address-keyed maps: Bug 10 reminder
    if re.search(r"TreeMap\[\s*str\s*,", src) and re.search(r"sender_address|as_hex|Address", src):
        warn("TreeMap[str, ...] with Address-derived keys: confirm .lower() normalization at EVERY write and read site  [Bug 10]")

    # 3f. emit_transfer ordering reminder
    if "emit_transfer" in src:
        warn("emit_transfer present: confirm balance is zeroed AND persisted before the transfer, and a test asserts exact amount + recipient  [rule 11]")

    # 3g. verdict reachability reminder
    if re.search(r"_VALID_VERDICTS|_OUTCOME_ORDER|VALID_VERDICTS", src):
        warn("Enumerated verdict/outcome present: trace every value to the leader_fn branch that can produce it (delete unreachable values)  [section 2]")

    report()


def report():
    print("=== audit_contract.py ===")
    for m in fails:
        print("FAIL ", m)
    for m in warns:
        print("WARN ", m)
    print(f"--- {len(fails)} FAIL, {len(warns)} WARN ---")
    print("Also run: genvm-lint check <contract.py>  and  pytest tests -q -p no:cacheprovider")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1])
