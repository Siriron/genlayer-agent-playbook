# Portal submission — {{PROJECT_NAME}}

Fill every field with final text (never "add a suitable title"). Count characters with
`python scripts/check_limits.py <field> "<text>"`. Leave section 04 (demo video) out.
A screenshot of the live form overrides this template (docs/knowledge/17).

**01 Identity**
1. Logo: "{{512x512 PNG, 128–2048 px, ≤ 2 MB, designed fresh for this app}}"
2. Project name: "{{NAME}}"
3. Primary tag: "{{one of: DeFi; AI & Agents; Prediction Markets; Dispute Resolution; Governance; Gaming; Marketplaces; Social; Identity/Reputation; Developer Tools; Other}}"
4. Secondary tag 1: "{{one precise topic valid for the primary tag; ask for a screenshot if the list is unknown}}"
   Secondary tag 2: leave empty

**02 One-liner** (≤ 180 chars): "{{...}}"

**03 Description** (≤ 1000 chars): "{{Name the actual contract methods, verdict options, evidence source, and the consensus need (who benefits from a false verdict). No generic intro.}}"

**05 How-to** (repeat "+ Add another step" per path)
- Path 1 — {{heading}}: "{{exact steps in the live app}}"
- Path 2 — {{heading}}: "{{exact steps}}"
- Path 3 — Reproduce without a wallet: "{{git clone, cd, pip install \"genlayer-test==0.29.2\", pytest tests -q -p no:cacheprovider; state what the tests prove and do not prove}}"

**06 Review verification**
- Expected verification outcome (≤ 500 chars): "{{what a steward should observe}}"
- Contract link 1: "{{exact explorer address URL}}"

**07 Project links**
- Website: "{{live Vercel URL — real, or say not deployed}}"
- GitHub: "{{repo URL}}"
