# README template — Projects track

Copy this whole structure for every new Projects-track README, then replace every `{{BRACKETED}}` placeholder. This is built entirely from HTML patterns GitHub's markdown sanitizer actually allows — confirmed directly against GitHub's real sanitization behavior before this template was written, not assumed. Do not add `<style>` blocks, `class`/`id` attributes, inline `style=` attributes, or `<script>` tags anywhere — GitHub strips all of these silently, so they will not break the page, they will just do nothing while making the source harder to read. Every visual color/badge element below uses shields.io image badges instead, which is the actual confirmed way color survives GitHub's rendering pipeline.

Verify this renders correctly on the actual repo page after pushing — a local raw-HTML preview (or an AI-generated preview) is not equivalent to GitHub's real sanitized output, per section 13's verification-depth lesson: check the primary source's real behavior, don't assume from a preview that isn't running the same pipeline.

---

```markdown
<div align="center">

<img src="{{FAVICON_OR_LOGO_URL}}" width="88" alt="{{PROJECT_NAME}} logo" />

# {{PROJECT_NAME}}

### {{ONE_LINE_TAGLINE — the same sentence as github-description.txt}}

<br />

![Status](https://img.shields.io/badge/status-{{live%20%7C%20building}}-{{brightgreen_or_yellow}}?style=flat-square)
![Networks](https://img.shields.io/badge/networks-StudioNet%20%2B%20Bradbury-blue?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square)
![Stack](https://img.shields.io/badge/stack-React%20%2B%20Vite%20%2B%20GenVM-{{BADGE_COLOR}}?style=flat-square)

<br />

**[Live App]({{VERCEL_URL}})** &nbsp;·&nbsp; **[Documentation](./docs/architecture.md)** &nbsp;·&nbsp; **[Smart Contract](./contracts/{{CONTRACT_FILE}}.py)**

</div>

<br />

---

## What this is

{{2-3 sentences. Plain prose, no jargon. What problem does this solve and for whom — this is the elevator pitch a reviewer reads in the first five seconds.}}

<br />

<div align="center">

| | |
|---|---|
| **Concept** | {{one phrase — e.g. "Staked freelance deliverable arbitration"}} |
| **Consensus need** | {{who benefits from a false verdict — the actual Test 1 answer, stated plainly}} |
| **Evidence source** | {{what gets fetched and judged — never user-submitted text alone}} |
| **Networks** | StudioNet + Bradbury |

</div>

<br />

---

## How it works

<div align="center">
<img src="{{ARCHITECTURE_DIAGRAM_OR_SCREENSHOT_URL}}" width="640" alt="{{PROJECT_NAME}} flow diagram" />
</div>

{{3-5 short numbered steps — the actual lifecycle, in order. Match docs/contracts.md's method table exactly; don't let this drift out of sync with the real contract.}}

1. {{Step one}}
2. {{Step two}}
3. {{Step three}}

<br />

<details>
<summary><b>The three(or however many)-way verdict, if applicable</b></summary>
<br />

{{If this contract has a non-binary verdict shape, explain it here. If it's binary or single-outcome, delete this whole details block — don't force the pattern where it doesn't fit.}}

</details>

<br />

---

## Deployed contracts

<div align="center">

| Network | Address | Explorer |
|---|---|---|
| StudioNet | `{{STUDIONET_ADDRESS}}` | [View]({{STUDIONET_EXPLORER_URL}}) |
| Bradbury | `{{BRADBURY_ADDRESS}}` | [View]({{BRADBURY_EXPLORER_URL}}) |

</div>

<br />

---

## Quick start

```bash
cd frontend
npm install
npm run dev
```

Run the contract tests (they execute the real contract under the GenVM SDK in direct mode):

```bash
pip install "genlayer-test==0.29.2"
pytest tests -q -p no:cacheprovider
```

Full deployment instructions: [`docs/deployment.md`](./docs/deployment.md)

<br />

---

## Project structure

```
contracts/{{CONTRACT_FILE}}.py    The GenVM contract
frontend/                          React + Vite app
docs/                              architecture.md, deployment.md, contracts.md, frontend.md
LICENSE                            MIT
```

<br />

---

## Status

<div align="center">

![Tested](https://img.shields.io/badge/{{what's%20confirmed%20live}}-tested-brightgreen?style=flat-square)
![Untested](https://img.shields.io/badge/{{what%20isn't}}-untested-yellow?style=flat-square)

</div>

{{One honest paragraph. What's actually been live-verified versus what's only theoretically correct. This is the single most important section for a reviewer's trust — do not round up. Match docs/deployment.md's testing-status section exactly; both should say the same thing.}}

<br />

---

<div align="center">

Built on [GenLayer](https://genlayer.com) · [Portal submission](https://portal.genlayer.foundation/)

</div>
```

---

## Notes on why each piece is here

- **`{{BADGE_COLOR}}`** is chosen fresh for each build (or set by the person for that exact build); do not reuse a color from an earlier README.
- **The badge row** is the only place color/visual polish survives GitHub's sanitizer intact, since it's rendering real remote images (shields.io), not styled HTML. Don't skip it just because it feels like a small detail — it's the actual mechanism for the "looks cool" instruction to work at all within GitHub's real constraints.
- **`<details><summary>`** is genuinely supported and is the right tool for anything long/optional (verdict explanations, edge-case notes) that would otherwise make the README feel bloated on first scroll — collapsed by default, expandable on demand.
- **The Quick start test block matters.** Review is repository-only: deployment addresses and transaction logs are not accepted as proof, so a reviewer must be able to reproduce your behavior by running the tests. Say in the Status section exactly what the tests prove and what they do not (they mock the web and the LLM).
- **The "Status" section is deliberately not decorative.** Every prior build in this project has had a real gap between "looks done" and "confirmed live" (see section 13) — the README should say plainly which parts of the app are which, using the same language as `docs/deployment.md`'s testing-status section, not softer marketing language that rounds an untested branch up to "working."
- **Do not invent the diagram/screenshot URLs** (`{{ARCHITECTURE_DIAGRAM_OR_SCREENSHOT_URL}}`, `{{FAVICON_OR_LOGO_URL}}`) as placeholder image links that don't resolve — either generate/export a real screenshot and reference its real repo-relative path (e.g. `./docs/assets/flow.png`), or remove the `<img>` block entirely rather than leave a broken image icon in a live README.
