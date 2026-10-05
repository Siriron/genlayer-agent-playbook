# Knowledge index

Source of truth for building on GenLayer. Sections keep their original numbers so cross-references inside the documents still resolve (there is no section 8 in the source).

References to "Project files" inside the documents mean the files in [`../templates/`](../templates/).
References to "Claude" mean the coding agent reading them.

| # | File | Read it when |
|---|---|---|
| 1 | [Ethics](knowledge/01-ethics.md) | Before choosing any concept. Highest priority. |
| 2 | [Concept gate](knowledge/02-concept-gate.md) | Before writing any code for a new idea (four tests, rotation rule). |
| 3 | [Contract rules (TIER 1)](knowledge/03-contract-rules.md) | Writing or reviewing any contract. |
| 4 | [Nondet bug catalog](knowledge/04-nondet-bug-catalog.md) | Before first deploy of any contract with `run_nondet_unsafe`. Literal checklist. |
| 5 | [Canonical nondet pattern](knowledge/05-canonical-pattern.md) | Writing the nondet section of a contract. |
| 6 | [Debugging methodology](knowledge/06-debugging-methodology.md) | Any GenVM error; also the pre-handoff audit list. |
| 7 | [Frontend SDK](knowledge/07-frontend-sdk.md) | Any `genlayer-js` frontend work. |
| 9 | [Build checklists](knowledge/09-build-checklists.md) | Projects track (14 points) and Contracts track (6 points). |
| 10 | [Portal rules](knowledge/10-portal-rules.md) | Choosing a track, writing submissions, answering reviewers. |
| 11 | [Project tracker](knowledge/11-project-tracker.md) | Novelty check; reference implementations. |
| 12 | [Communication rules](knowledge/12-communication-rules.md) | Interaction conventions. |
| 13 | [Verification-depth retrospective](knowledge/13-verification-retrospective.md) | Novel storage patterns; frontend self-review. |
| 14 | [Official-source deltas](knowledge/14-official-source-deltas.md) | SDK facts that differ from docs/official examples; tooling. |
| 15 | [Portal results & staff feedback](knowledge/15-portal-results.md) | Current review standard (repository-only). |
| 16 | [Acceptance/rejection lessons](knowledge/16-acceptance-rejection-lessons.md) | Pre-submission red-team checklist (16.3). |
| 17 | [Portal submission workflow](knowledge/17-portal-submission-workflow.md) | Producing portal / contract submission text. |

## Templates

| File | Use |
|---|---|
| [`projects-track-skeleton.py`](../templates/projects-track-skeleton.py) | Start of every Projects-track contract. |
| [`contracts-track-skeleton.py`](../templates/contracts-track-skeleton.py) | Start of every Intelligent Contracts-track contract. |
| [`direct-mode-test-template.py`](../templates/direct-mode-test-template.py) | `tests/test_direct.py` that executes the real contract. |
| [`readme-template.md`](../templates/readme-template.md) | README for every Projects-track repo (GitHub-safe HTML). |
| [`portal-submission-template.md`](../templates/portal-submission-template.md) | Portal form fields, all sections. |
| [`contract-submission-template.md`](../templates/contract-submission-template.md) | Contracts-track title + description. |

## Scripts

| File | Use |
|---|---|
| [`scripts/audit_contract.py`](../scripts/audit_contract.py) | Mechanical nondet audit (greps + AST). |
| [`scripts/audit_all.sh`](../scripts/audit_all.sh) | Audit + `genvm-lint` + `pytest` in one command. |
| [`scripts/check_limits.py`](../scripts/check_limits.py) | Count text against portal character limits. |

## Freshness

Knowledge is current as of the Sep 20 2026 portal snapshot. The portal form, review standard, SDK runner hash, and fee/limit details can change: re-verify anything time-sensitive (a screenshot of the live form overrides section 17).
