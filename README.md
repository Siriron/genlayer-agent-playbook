<div align="center">

# GenLayer Agent Playbook

### Everything a coding agent needs to build, test, audit, and submit GenLayer projects without relearning it.

<br />

![Type](https://img.shields.io/badge/type-agent%20knowledge%20base-blueviolet?style=flat-square)
![Network](https://img.shields.io/badge/network-StudioNet-blue?style=flat-square)
![Runner](https://img.shields.io/badge/py--genlayer-1jb45...-informational?style=flat-square)
![Knowledge](https://img.shields.io/badge/knowledge-Sep%202026-orange?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square)

<br />

**[Agent manual](./AGENTS.md)** &nbsp;·&nbsp; **[Knowledge index](./docs/INDEX.md)** &nbsp;·&nbsp; **[Templates](./templates/)** &nbsp;·&nbsp; **[Audit scripts](./scripts/)**

</div>

<br />

---

## What this is

A production-grade knowledge base for building on [GenLayer](https://genlayer.com): Python intelligent contracts on GenVM, React + Vite frontends, and portal submissions. It distills a full build history, every confirmed GenVM runtime bug with its fix, the evidence-binding rules that survived staff review, and the exact reasons real submissions were accepted or rejected.

Point a coding agent at this repository and it starts from the settled answers instead of rediscovering each failure live.

<br />

<div align="center">

| | |
|---|---|
| **For** | Coding agents (Claude Code, Cursor, Copilot, Codex, Gemini) and the builders directing them |
| **Entry point** | [`AGENTS.md`](./AGENTS.md) (mirrored as [`CLAUDE.md`](./CLAUDE.md)) |
| **Covers** | Ethics gate, concept evaluation, contract rules, 12-bug nondet catalog, frontend SDK, checklists, portal rules, review lessons |
| **Ships** | 2 contract skeletons, a direct-mode test suite template, README template, 3 audit/limit scripts |
| **Target** | GenLayer StudioNet only |

</div>

<br />

---

## How an agent should use it

1. Load [`AGENTS.md`](./AGENTS.md) as the standing instruction file.
2. For any new idea, run the **concept gate** ([`02`](./docs/knowledge/02-concept-gate.md)) before writing code.
3. Start the contract from a skeleton in [`templates/`](./templates/); write tests from the direct-mode template.
4. Run `bash scripts/audit_all.sh contracts/<file>.py` (mechanical audit + `genvm-lint` + `pytest`).
5. Finish with the red-team checklist ([`16.3`](./docs/knowledge/16-acceptance-rejection-lessons.md)) and the portal workflow ([`17`](./docs/knowledge/17-portal-submission-workflow.md)).

<br />

<details>
<summary><b>The sixteen hard rules, condensed</b></summary>
<br />

1. Pinned runner on line 1; never `py-genlayer:test`.
2. `run_nondet_unsafe(leader_fn, validator_fn)` positional; both nested; zero `self.`.
3. `leader_fn` returns a parsed dict; `validator_fn` checks `gl.vm.Return`, reads `.calldata`, re-derives, compares every decision-bearing field.
4. `copy_to_memory` before the nondet call; storage writes only after.
5. Module-level constants; annotated class attributes are storage.
6. `emit_transfer`, never `.send()`; pull-based settlement; bounded exit for every fund path.
7. `.status`, not `.status_code`; fetch failures become markers, never evidence.
8. No `float()`; integer-only timestamp parser.
9. No explicit `DynArray` construction on nested fields.
10. Lowercase-normalize Address-derived keys everywhere.
11. Sanitize and wrap all untrusted text; fetch evidence contract-side.
12. Every verdict value maps to a reachable `leader_fn` branch.
13. Evidence derived from a locked identifier and echoed back; second channel for control claims.
14. Evidence must be able to speak to the time the claim concerns.
15. Lock the judged fields before any party knows the outcome.
16. Tests execute the real contract; run them before shipping.

</details>

<br />

---

## Repository map

```
AGENTS.md                              Operating manual for coding agents
CLAUDE.md                              Mirror of AGENTS.md
README.md                              This file
LICENSE                                MIT
github-description.txt                 Repo description (195/350 characters)
docs/
  INDEX.md                             Table of contents with "read it when" guidance
  knowledge/
    01-ethics.md                       Non-negotiable constraints
    02-concept-gate.md                 Four tests, rules 0.7/0.8, rotation, reachability
    03-contract-rules.md               TIER 1 rules, validator rigor, pre-handoff checks
    04-nondet-bug-catalog.md           Bugs 1-12, graded-outcome ladder, design principles
    05-canonical-pattern.md            Live-tested nondet contract template
    06-debugging-methodology.md        Verify-don't-guess process and audit list
    07-frontend-sdk.md                 genlayer-js, wallet, ensureChain, receipts
    09-build-checklists.md             14-point Projects, 6-point Contracts
    10-portal-rules.md                 Tracks, rejection categories, review responses
    11-project-tracker.md              Prior builds and reference implementations
    12-communication-rules.md          Interaction conventions
    13-verification-retrospective.md   Escalate to primary source; isolate risky lines
    14-official-source-deltas.md       SDK facts vs. official examples; tooling
    15-portal-results.md               Repository-only review standard
    16-acceptance-rejection-lessons.md Why each repo passed or failed; red-team list
    17-portal-submission-workflow.md   Portal form fields and output format
templates/
  projects-track-skeleton.py           Projects-track contract skeleton
  contracts-track-skeleton.py          Intelligent Contracts-track skeleton
  direct-mode-test-template.py         Direct-mode tests that run the real contract
  readme-template.md                   GitHub-safe README template
  portal-submission-template.md        All portal form fields
  contract-submission-template.md      Contracts-track title + description
scripts/
  audit_contract.py                    Mechanical nondet audit (grep + AST)
  audit_all.sh                         Audit + genvm-lint + pytest
  check_limits.py                      Portal character-limit counter
```

<br />

---

## Quick start

```bash
git clone <this-repo-url> genlayer-agent-playbook
cd genlayer-agent-playbook

# audit any contract
python scripts/audit_contract.py path/to/contract.py

# full gate (needs: pip install genvm-linter "genlayer-test==0.29.2")
bash scripts/audit_all.sh contracts/my_contract.py

# count submission text
python scripts/check_limits.py oneliner "Your one-liner here"
```

To use it in a new project, copy `AGENTS.md`, `CLAUDE.md`, `docs/`, `templates/`, and `scripts/` into the project root (or add this repository as a submodule) and tell the agent to read `AGENTS.md` first.

<br />

---

## Status

<div align="center">

![Verified](https://img.shields.io/badge/audit%20script-self--tested-brightgreen?style=flat-square)
![Unverified](https://img.shields.io/badge/skeletons%20%26%20test%20template-not%20re--run%20here-yellow?style=flat-square)

</div>

This is documentation plus tooling, not a deployed app. What is and is not confirmed:

- `scripts/audit_contract.py` was run against a deliberately broken contract (9 failures flagged) and against the canonical pattern in `05` (0 failures). It is a mechanical check; it does not replace `genvm-lint`, the verdict-reachability trace, or tests.
- The skeletons contain `{{PLACEHOLDERS}}` and are templates, not runnable contracts. The test template is documented in the source notes as a passing 24-test suite against the corrected Projects skeleton; it was not re-executed when this repository was assembled.
- Bugs 11 and 12 are open questions, not rules. Newer runner hash, portal form details, and review standards change; re-verify anything time-sensitive.
- Knowledge reflects the Sep 2026 portal snapshot. Private account details were removed.

<br />

---

<div align="center">

Built for [GenLayer](https://genlayer.com) builders · MIT licensed

</div>
