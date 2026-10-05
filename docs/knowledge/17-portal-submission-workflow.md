## 17. Portal submission workflow (standing instructions from the person running this project, Sep 20 2026)

**Triggers and outputs**
- **"Give me portal submission"** (after an app is built): immediately give every field of the current portal form for that specific app, filled with the exact final text, numbered by form section, each value in quotes, ready to paste. Leave section 04 (demo video) out. A primary tag is required. Secondary tags are optional in the form and their options depend on the primary tag; still choose **one** that fits it (fill Tag 1 only; Tag 2 stays empty). Never write "add a suitable title"; write the title.
- **Section 05 (how-to) can need several paths.** Give each relevant path as its own step ("Path 1", "Path 2", ...) built from the app's real functionality. Use the form's "+ Add another step" for each.
- **"Give me contract submission"**: unchanged. Only a Title and a Description (under 1000 characters). Do not apply the portal-submission fields to it.
- **"Full app" means the complete app**: functionality, UI, logic and structure, not a demo.
- **Screenshots of the form are the source of truth.** A newer screenshot overrides anything below.
- **"Make an inspired version" of a repo or an accepted project:** research it deeply first (core idea, product logic, architecture, user flow, features, weaknesses, why it was likely accepted, how the parts work together), then design and build an original project. Never copy source, UI, text, branding or names, and never make cosmetic changes to an existing project. The reference's acceptance guarantees nothing about ours.
- **Normal order:** idea or reference, research, own design, build, portal submission, then contract submission if asked.

**The form as of Sep 20 2026 (from screenshots)**
| Section | Field | Limit / rule |
|---|---|---|
| 01 Identity | Logo | PNG, JPEG or WebP; 128-2048 px; max 2 MB |
| | Project name | required |
| | Primary tag | required; list below |
| | Secondary tags (Tag 1, Tag 2) | optional in the form; "up to two precise topics within the primary tag"; the options change with the primary tag chosen. Standing rule: always give one (Tag 1) |
| 02 One-liner | Describe the project in one line | max 180 characters |
| 03 Description | What is this project? | max 1000 characters |
| 04 Demo video | YouTube or X direct post link | optional; leave out |
| 05 How-to | Optional heading + instruction, repeatable | "Write the exact path": what the visitor does, step by step |
| 06 Review verification | Expected verification outcome | max 500 characters; visible only to the project owner and stewards |
| | Contract link 1..n | optional; exact explorer address URLs (Studio, Studio Dev, Bradbury or Asimov); "+ Add another deployment" |
| 07 Project links | Website | required before review |
| | GitHub | field present; Projects need the repo URL |

**Primary tags:** DeFi; AI & Agents; Prediction Markets; Dispute Resolution; Governance; Gaming; Marketplaces; Social; Identity/Reputation; Developer Tools; Other.
**Known secondary tags:** under Dispute Resolution — Evidence Assessment, Escrow Claims, Moderation Appeals, License Claims, Appeal Review, Jury Selection. The lists under the other primary tags have not been seen; ask for a screenshot rather than guessing a tag.

**How this connects to the rest of this document (added while filing the instructions, not part of the person's instructions)**
- **The concept gate and the nondet audit still run before any build**, including an "inspired version". An inspired concept still has to pass Test 3 against the tracker and the live portal; a lightly modified copy of an accepted project falls under the plagiarism rejection category in section 10. Inspiration transfers principles (evidence binding, bounded exits, test structure), not the concept.
- **Review is repository-only (section 15), so section 06's outcome and section 05's paths should include a route a steward can reproduce without a wallet:** the repository test command (`pytest tests -q -p no:cacheprovider`) and what it proves, alongside the live-app path. Do not rely on transaction logs as proof.
- **Character limits are counted, not estimated,** before the text is handed over: 180 for the one-liner, 1000 for the description, 500 for the expected outcome.
- **Logo:** produce a PNG at 512x512 (inside 128-2048 px, well under 2 MB) designed fresh for that app; per the standing design rule, no earlier build's look is reused.
