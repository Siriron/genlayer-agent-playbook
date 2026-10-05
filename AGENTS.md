# AGENTS.md — operating manual for coding agents

You are building on **GenLayer** (Python contracts on GenVM, React + Vite frontends, StudioNet). This repository is your complete, pre-verified knowledge base. Do not re-derive anything it already settles; do not guess an SDK name it does not list — verify first (docs/knowledge/06).

Compatibility: `CLAUDE.md` and this file are identical in intent. If your tool reads a different filename (`.cursorrules`, `GEMINI.md`, `copilot-instructions.md`), point it here.

## 0. Read order

1. This file.
2. `docs/knowledge/01-ethics.md` — hard constraints, always.
3. For a **new build**: `02-concept-gate`, then `09-build-checklists`, then `templates/`.
4. For **any contract**: `03-contract-rules`, `04-nondet-bug-catalog`, `05-canonical-pattern`.
5. For **any frontend**: `07-frontend-sdk`, then `13-verification-retrospective` §13.3.
6. For **submitting**: `10-portal-rules`, `15-portal-results`, `16-acceptance-rejection-lessons`, `17-portal-submission-workflow`.
7. Full index: `docs/INDEX.md`. In the docs, "Project files" = `templates/`; "Claude" = you.

## 1. Non-negotiables (violating any is a failed build)

**Ethics (§1).** No riba, gambling/chance payout, speculation, predatory tokenomics, hidden incentives, admin abuse. Never build a generic staking/wagering primitive a third party could reuse as a betting pool. Allowed: a stake/slash mechanism whose outcome is a deterministic consequence of an evidence-based verdict.

**Contract (§3–§4).**
1. Line 1: `# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }`. Never `py-genlayer:test`.
2. `@allow_storage` + `@dataclass` for structs; `TreeMap` for key-value; views return `json.dumps(...)` strings; integers only, **no `float()` anywhere**.
3. `gl.vm.run_nondet_unsafe(leader_fn, validator_fn)` — **positional**; both are **nested functions** inside the `@gl.public.write` method, with **zero `self.`** in either.
4. `leader_fn` returns an already-parsed dict. `validator_fn(leaders_res)` checks `isinstance(leaders_res, gl.vm.Return)` first, reads `leaders_res.calldata`, **re-derives** by calling `leader_fn()`, and compares **every field the outcome depends on** (zero tolerance on discrete choices; tolerance only on values derived from a choice). Format-only or length-only checks are rejected.
5. `gl.storage.copy_to_memory(...)` every storage-backed value in the plain body **before** `run_nondet_unsafe`. Storage writes happen only after it returns.
6. Constants live at module level; a type-annotated class-body attribute is always storage.
7. Value moves use `.emit_transfer(value=...)`, never `.send()`. Prefer pull-based settlement (credit balance → separate `claim()` zeroes + persists, **then** transfers).
8. HTTP responses: `.status` / `.body` (never `.status_code`). Fetch failures degrade to a marker string, never evidence.
9. Timestamps: `_now_epoch_seconds()` from the skeletons (`gl.message_raw["datetime"]` is an ISO-8601 string). Do not `int()` it.
10. No `DynArray[...]()` construction on nested dataclass fields; use a delimiter-joined `str`.
11. Address-derived `TreeMap` keys: lowercase-normalize at every write and read.
12. Wrap every untrusted string with `_sanitize` + `_wrap_untrusted`. Never judge from submitter text alone; fetch evidence contract-side.
13. Trace every verdict/outcome value to the `leader_fn` branch that can emit it; delete unreachable values (disclosure does not excuse them).
14. Evidence must be structurally derived from a locked identifier — never a submitter-supplied URL — and the fetched record must echo the claimed identifier (§2, rules 0.7/0.8). Standing/control claims need a second independent channel. Time-based claims need evidence that carries historical timestamps (§16.2).
15. Lock every field the judgment depends on (spec, deadline, target) at the earliest write, before any party has information about the outcome.
16. Every fund path has a bounded exit (timeout, reclaim, or no-fault settlement). No funds locked forever.

**Frontend (§7).** React + Vite or Next.js only (no HTML-only frontends). `genlayer-js` subpaths: root, `/chains` (`studionet`), `/types` only. `account` is the plain wallet address string — **never** `createAccount(address)`. `provider: window.ethereum`; call `ensureChain()` before every write; `writeContract` needs `value: BigInt(0)`; parse `readContract` JSON; `waitForTransactionReceipt` with `{retries: 120, interval: 4000}`; surface an explorer link on timeout. Contract address = one plain constant in `src/config/chains.ts`; no `.env`/`.gitignore`. StudioNet only. Return created IDs to the caller instead of inferring from a global counter; every contract method must be reachable from the app.

**Tests (§14–§16).** Review is repository-only. Ship `tests/` that **execute the real contract** in direct mode (`pip install "genlayer-test==0.29.2"`, `pytest tests -q -p no:cacheprovider`, no `-s`). Static scans, hand-written Python models, deployment addresses, and transaction logs are not accepted proof. Run the tests before shipping; say in README/docs exactly what they do and do not prove.

## 2. Workflows

### A. New Projects-track build
1. **Concept gate** (§2): Test 1 consensus necessity (name who benefits from a false verdict), Test 2 evidence verifiability (≥1 fixed, external, independently authoritative leg; rules 0.7/0.8; binding), Test 3 novelty vs. `docs/knowledge/11-project-tracker.md` and the live portal, Test 4 depth. Apply genre/mechanism rotation vs. the last build. Fail → stop and say why; do not build.
2. Audit a comparable real contract's source if one is reachable, before writing code (§2).
3. Pick shape/verdict/evidence-binding decisions from `templates/projects-track-skeleton.py`'s docstring; list every verdict value with its producing branch.
4. Write the contract from the skeleton; delete unused fields/functions; state deliberate gaps.
5. Tests from `templates/direct-mode-test-template.py`: one test per real branch, per validator-compared field, per fund path, per HTTP failure.
6. Run `bash scripts/audit_all.sh contracts/<file>.py` (audit + `genvm-lint` + `pytest`). Fix all FAIL items; review WARN items by hand.
7. Frontend per §7 and the 14-point checklist (§9.1), including the explicit static self-review pass (§13.3).
8. Docs (`architecture.md`, `deployment.md`, `contracts.md`, `frontend.md`) and README from `templates/readme-template.md` — must match the real build exactly.
9. Red-team with §16.3; every answer must point to a named test.
10. Hand off. Your part ends at handoff; deployment, live testing, pushing, and submission are the person's sequence. If an unconfirmed pattern (Bugs 11/12) is relevant, mention the isolated test once, briefly.

### B. New Intelligent Contracts-track contract
Single technique, reusable primitive, no frontend (§10.1, §9.2). Start from `templates/contracts-track-skeleton.py`. Reject concepts that are extracted from a Projects build, or that are learning exercises. Full §3–§6 rigor still applies. Output: contract + title + description (< 1000 chars, counted).

### C. Debugging a deployed contract
Get the real stderr/traceback first. Verify any SDK name against primary sources before using it (§6). Test the single riskiest unconfirmed line in isolation (§13.2). Declare a fix only when the failure signal is gone. Re-run the full audit for any storage/settlement change. Hold docs until the person confirms the contract is final.

### D. "Make an inspired version" of a repo or accepted project
Research deeply first (idea, logic, architecture, flow, weaknesses, why accepted). Then design and build an **original** project — no copied source, UI, text, names; no cosmetic edits. The concept gate still runs. Transfer principles, not the concept.

### E. Portal / contract submission text
"Give me portal submission" → every form field of the current form, filled with final quoted text, numbered by section, section 04 omitted, one secondary tag (Tag 1), several how-to paths including a wallet-free reproduction path. "Give me contract submission" → title + description only. Count characters with `scripts/check_limits.py`. Notes must name real method names, verdict options, and evidence sources; generic intros are a rejection category.

### F. Responding to "More information needed"
State exactly what changed (function, condition, new behavior) tied to the original feedback; state what proves it (a named test); include updated links inline (§10).

## 3. Communication and output conventions

- Direct and practical. No hype, no filler, no encouragement, no preamble. Treat the person as a competent collaborator.
- Deliver complete solutions in one response. On a pasted error: fix + explanation together, no clarifying questions unless a choice is consequential and hard to reverse.
- Never present an unverified claim as confirmed. Mark uncertainty in comments. Do not round "untested" up to "working" in any README or doc.
- Design (colors, typography, theme, layout) is decided fresh for every build; never reuse or record an earlier build's look unless the person specifies one for that build.
- No fabricated or placeholder URLs (og:url, live links, images). If not deployed, say so.
- Check every message for an actually attached file before assuming one exists.

## 4. Tools in this repository

| Command | Purpose |
|---|---|
| `python scripts/audit_contract.py <contract.py>` | Greps + AST for Bugs 1–8, 10, E010 patterns, validator shape. FAIL = fix; WARN = review by hand. |
| `bash scripts/audit_all.sh <contract.py>` | Above + `genvm-lint check` + `pytest tests`. |
| `python scripts/check_limits.py <field> "<text>"` | Character limits: oneliner 180, description 1000, outcome 500, contract-description 1000, github-description 350. |

The audit script does not replace the verdict-reachability trace or a real run of the tests.

## 5. Known open questions (do not treat as settled)

- Bug 11 (plain list literal into a nested `DynArray` slot) and Bug 12 (`datetime.now()` equals the transaction time on all validators) are supported by SDK source/spec but not live-confirmed. Defaults stay: delimiter-joined `str`, `_now_epoch_seconds()`.
- Newer runner hash `5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng` is not adopted; keep `1jb45…`.
- The portal form, tag lists under non-Dispute-Resolution primary tags, and review standard change over time; a screenshot of the live form overrides §17.
- Seven of the eight previously audited contracts carry the `status_code` fetch bug (§14); fix it in every new build and before any resubmission.
