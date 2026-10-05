## 13. Recourse build retrospective — verification-depth discipline (Aug 2026)

This section exists because Recourse's `spec_items` field failed three separate live Studio deploys before landing on a working pattern, and the frontend build separately shipped two real bugs (one Rules-of-Hooks violation, one `.ts`/`.tsx` extension mismatch) that were only caught by a deliberate static self-review pass run *after* the whole frontend was already written. Read this before starting the next build — it is not a postmortem to skim, it is where the next build's process actually changes.

### 13.1 The core failure pattern: verification depth escalated only after live failures, not before them

Every one of the three `spec_items` attempts failed at a different, deeper level of the same underlying question ("how do you get a populated `DynArray[str]` onto a nested `@allow_storage` dataclass field") — full detail now lives in section 4's Bug 7, so it isn't repeated here. The escalation pattern across the three attempts is the actual lesson:

1. **Attempt 1** was based on generalizing a doc excerpt to a case it didn't actually demonstrate. Failed live.
2. **Attempt 2** was based on pattern-matching a confirmed-working example (`TreeMap`'s `inmem_allocate` usage) to a different type without confirming the analogy held. Failed live, differently.
3. **Attempt 3** — the fix that shipped — only arrived at after fetching and reading GenLayer's actual `generate.html` SDK source directly, which settled a question doc prose alone had left ambiguous.

**The lesson is not "always get it right the first time."** GenVM's API surface has real, confirmed internal inconsistencies (see section 6, point 3) and gaps no doc example covers — a `DynArray` field on a nested dataclass had no confirmed working example anywhere across official docs, the SDK reference, or any deployed contract found during this build. Some amount of live iteration is genuinely unavoidable for a first-of-its-kind pattern.

**The lesson is: escalate to primary source (actual SDK source code, not doc prose or doc examples) as step one for any genuinely novel storage/type pattern, not as a last resort after two live failures.** Fetching `generate.html` directly and reading the real `old_init`/codegen logic settled attempt 3's question in one search. That same search, run *before* attempt 1, would likely have prevented both failed attempts. Concretely: if a pattern isn't demonstrated in a confirmed *working* example elsewhere in this document, and it involves a container type interacting with a nested (not top-level contract) storage field, fetch the SDK's actual source (`sdk.genlayer.com` module pages, or search for the class name + `github`) before writing code that depends on your best guess of how it behaves.

### 13.2 Test the single highest-risk, never-before-executed line in isolation — before wiring six functions around it

`spec_items` construction was one line, but it was load-bearing for `create_engagement`, and every other write method in the contract assumed engagements already existed. The three failures were each discovered only when the *whole* `create_engagement` function was tested, meaning every retry re-tested five other lines that were never actually in question.

**Process change:** when a contract has one genuinely novel, unconfirmed pattern (a storage shape with no working precedent in this document), isolate it. Write the smallest possible write function that exercises *only* that pattern — construct the record, store it, read it back — and confirm it in Run and Debug before writing the surrounding lifecycle. This is the same principle section 3's "Fastest way to test a contract" already states for contract-vs-frontend iteration speed; apply it one level deeper, to sub-function granularity, for any single pattern flagged as unconfirmed.

### 13.3 Frontend: run the static self-review pass *as an explicit, separate step* — not as a side effect of "writing carefully"

Two real bugs shipped in the first draft of Recourse's frontend:
- `ActionForm.tsx` called `useState` inside a conditional branch (`if (actionKey === 'accept_engagement')`) — a genuine React Rules of Hooks violation, not a style nit.
- `useGenLayer.ts` was converted from a plain hook into a context provider containing real JSX (`return <Context.Provider>...`) but kept the `.ts` extension, which would have failed the Vite/TypeScript build outright.

Both were caught, but only because a deliberate, separate static review pass was run *after* the entire frontend was already written — grepping for conditional hook calls, grepping every `.ts` file for JSX syntax, cross-checking every import against every real export, checking brace balance file-by-file. Neither bug was caught while the file was actually being written, which means "write carefully" is not sufficient on its own.

**Process change, mandatory on every future frontend build, not optional:** after the frontend is fully written and before presenting it, run this exact sequence as its own step (this is now section 9.1 checklist item 11, verbatim):
1. Grep every `.ts`/`.tsx` file's local imports against the real exports of whatever they import from (catches phantom imports and stale references after refactors).
2. Grep for hook calls (`use[A-Z]`) appearing after a conditional (`if (`) at matching or greater indentation within the same function — a proxy for Rules of Hooks violations. A short Python/awk script, not manual reading, since manual reading already missed both bugs once in this build.
3. Grep every `.ts` (not `.tsx`) file for JSX-like patterns (`return <[A-Za-z]`) — any hit needs a rename to `.tsx`.
4. Check brace balance per file as a cheap proxy for structural syntax breaks, if a real `tsc`/build check isn't available.
5. Sweep for `console.log`, `TODO`/`FIXME`, `localhost`, and placeholder/fabricated URLs (an invented `og:url` or an unconfirmed "live at X" string counts as a placeholder even if it doesn't match a literal grep for the word "placeholder" — check meta tags and README claims by hand, not just by pattern).

### 13.4 Don't assume a domain's fetch behavior — verify it, even for well-known domains

A test designed to force an `"unverifiable"` verdict used `https://example.com/this-path-does-not-exist-404`, assuming an arbitrary path on `example.com` would 404 or fail to fetch. It doesn't — `example.com` resolves *any* path to its real IANA placeholder page, so `_fetch_text` returned real (if irrelevant) content, and the model correctly returned `"non_compliant"` instead of `"unverifiable"`. This cost a full wasted multi-minute consensus cycle and required starting a fresh engagement.

The fix — a `.invalid`-TLD URL, IETF-reserved to never resolve — worked on the first retry.

**Process change:** when a test needs to force a *specific* failure mode (not just "any error"), verify the exact mechanism will produce that mode, don't assume it from the domain's general reputation for being a placeholder/example domain. `.invalid`, `.test`, `.example`, and `.localhost` are the IETF-reserved TLDs that are actually guaranteed never to resolve — prefer these over improvising a plausible-sounding broken URL on a real domain.

### 13.5 What already worked and should be treated as required process, not optional discipline

- Re-running the full nondet-bug-catalog audit (section 4) after *any* change touching storage or settlement paths — including a one-branch bugfix, not just full new contracts — via literal `grep` plus a small indentation-scope-aware script for the `self.`-inside-nondet-closure check specifically, since a plain grep can't distinguish closure scope from the rest of the file.
- Flagging genuine uncertainty explicitly in shipped comments (e.g. a `formatGen`-style comment stating a display convention was never confirmed against a real transaction) rather than presenting a guess as settled fact. This costs nothing and means a future reader — human or Claude — knows exactly what still needs checking instead of trusting something unverified.
- Requesting the actual live transaction detail (stderr, full JSON) at every step of manual testing, rather than accepting a paraphrase — this is section 6 point 2's rule, and it's the only reason the three `spec_items` failures were each diagnosed correctly on the first read rather than guessed at again.
- Closing the loop on a portal-review fix with an actual repository-level lifecycle test, run live, rather than a code change alone — staff asked for proof the terminal state and both transfers were reachable, not just that the bug was patched, and producing that proof (not just the patch) is what actually closes a review cycle.
