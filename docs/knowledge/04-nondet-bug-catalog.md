## 4. CONFIRMED GenVM NONDET BUG CATALOG — mandatory pre-deploy audit, read before writing ANY nondet code

This section exists because Copyleft's `resolve_dispute` function went through six sequential, confirmed bugs across six days (Jul 17-22 2026) before working cleanly end-to-end, Recourse's `create_engagement` separately surfaced a seventh, structurally distinct bug (Bug 7, below) in Aug 2026, and SentinelSLA's live testing (Aug 2026) surfaced three more, structurally distinct from all seven before them (Bugs 8, 9, and 10, below). Each bug was invisible until the previous ones were fixed and let execution reach further into the same code path — a contract "working" through one write function's early stages does not mean the whole function is verified end to end. Every one of these ten items must be checked against every future contract with a `run_nondet_unsafe` call, before first deploy, not reactively after an error. Treat this as a literal checklist, not background reading.

### Bug 1 — `gl.nondet.web.get()` returns a `Response` object, never a plain string

**Symptom:** `TypeError: 'Response' object is not iterable` (or similar), typically inside a text-processing function like `_sanitize` that tried to do `for ch in text`.

**Root cause:** `gl.nondet.web.get(url)` returns a `Response` object with a `.body` (bytes) field and a **`.status`** (int) field — never a plain string, ever, regardless of what the fetched content actually is. **Correction (Sep 2026, confirmed against SDK source):** this entry previously said `.status_code`. The SDK's `Response` dataclass (`gl/nondet/web.py`) has exactly three fields — `status`, `headers`, `body` — and `status_code` appears nowhere in the SDK. Code that reads `getattr(response, "status_code", None)` gets `None` every time, so its `>= 400` check never fires and an HTTP 404/500 body is silently treated as real evidence. Official docs pages that show `.status_code` are wrong on this point; the official `write-contract` skill uses `.status`. Audit every shipped contract for `status_code`.

**Confirmed fix — the `_fetch_text` helper, live-tested and working:**
```python
def _fetch_text(url: str) -> str:
    if not url:
        return "[no URL provided]"
    try:
        response = gl.nondet.web.get(url)
        status = getattr(response, "status", None)
        if status is not None and status >= 400:
            return f"[fetch failed: HTTP {status}]"
        body = getattr(response, "body", None)
        if body is None:
            return "[fetch failed: empty response]"
        if isinstance(body, bytes):
            return body.decode("utf-8", errors="replace")
        if isinstance(body, str):
            return body
        return "[fetch failed: unrecognized response format]"
    except Exception:
        return "[fetch failed: unreachable or errored]"
```
This degrades a missing/dead/erroring fetch to a clear marker string the model can reason about, rather than raising — appropriate when the contract's design wants a missing fetch to count as evidence against whoever cited it (confirmed correct design choice for Copyleft). If a contract's design instead wants to hard-fail the whole transaction on a bad fetch, raise `gl.vm.UserError(f"fetch failed: HTTP {status}")` instead of returning a marker string — both are valid GenLayer patterns, matching the officially documented "Handling HTTP Errors" pattern for the raise variant.

**Confirmed via:** docs.genlayer.com/developers/intelligent-contracts/features/web-access, .../non-determinism, .../features/calling-llms (3+ independent official pages, each showing `response.body.decode("utf-8")` explicitly).

### Bug 2 — `run_nondet_unsafe`'s validator receives a wrapper object; `leader_fn` must return an already-parsed value

**Symptom:** `json.loads()` crashes — either because it's called on a value that's already a decoded dict, or because it's called directly on a `gl.vm.Return` wrapper object. On-chain this shows as every validator erroring identically (all showing `execution_result: "ERROR"`), and the transaction finalizing as `Undetermined` even though nothing about the actual judgment logic was wrong.

**Root cause, in full:**
- `leader_fn()` must return the actual parsed value (e.g. a `dict`, via `gl.nondet.exec_prompt(prompt, response_format="json")`) — never a raw JSON string for the caller to `json.loads()` again.
- `validator_fn(leaders_res)` receives its argument as a `gl.vm.Return | gl.vm.UserError | gl.vm.VMError` wrapper, NOT the plain value. `isinstance(leaders_res, gl.vm.Return)` MUST be checked first. The actual leader value lives at `leaders_res.calldata` — already decoded, never a string.
- The top-level `gl.vm.run_nondet_unsafe(...)` call itself returns that same plain decoded type directly (a dict here) — never a JSON string to be `json.loads()`'d by the caller.
- `run_nondet_unsafe(leader_fn, validator_fn)` must be called positionally, never as `leader_fn=`/`validator_fn=` keyword arguments — a separately-confirmed fatal bug where passing them as keywords raises `TypeError: run_nondet_unsafe() got some positional-only arguments passed as keyword arguments` at execution time, with unanimous validator "agreement that the contract errored" but the write silently never happening.

**Confirmed correct pattern (verbatim from GenLayer's own canonical WizardOfCoin example, cross-checked against the price-oracle example on the non-determinism page and a real deployed contract found on the explorer using an identical structure):**
```python
def leader_fn():
    result = gl.nondet.exec_prompt(prompt, response_format="json")
    return result  # already a dict — never a string

def validator_fn(leaders_res) -> bool:
    if not isinstance(leaders_res, gl.vm.Return):
        return False  # leader errored — disagree, force rotation
    leader_data = leaders_res.calldata  # already decoded
    my_data = leader_fn()  # call the function directly, never self.leader_fn()
    return leader_data["some_field"] == my_data["some_field"]

result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
# result is the dict directly — NEVER json.loads(result)
```

**Internal documentation inconsistency, confirmed:** GenLayer's own docs contain at least one example (`custom_consensus_example`, a sentiment-scoring snippet on the non-determinism page) that uses a different, less-safe pattern (`isinstance(leader_result, Exception)` instead of `isinstance(leaders_res, gl.vm.Return)`, treating the result as a raw value with no `.calldata` access). Do not follow that pattern. When official examples conflict, trust the one confirmed by the most independent sources — here, the `gl.vm.Return`/`.calldata` pattern is confirmed by the canonical WizardOfCoin example, the price-oracle example on the same page, the error-handling page's own `Result` type documentation, the calling-llms page, and a real accepted contract found on the explorer. The lone outlier snippet is very likely stale or illustrative-only.

**Confirmed via:** the WizardOfCoin canonical example, docs.genlayer.com/developers/intelligent-contracts/features/error-handling, .../non-determinism, .../features/calling-llms, and a real deployed "Faults"-pattern contract on explorer-studio.genlayer.com.

### Bug 3 — `gl.get_contract_at(address).send(amount)` does not exist

**Symptom:** `AttributeError: '_ContractAt' object has no attribute 'send'`. This only surfaces once a contract actually reaches its settlement/payout code — meaning it can hide silently for a long time if earlier bugs (like Bug 2) prevent execution from ever reaching that far. On Copyleft, this bug was completely invisible until Bug 2 was fixed and a dispute successfully resolved for the first time.

**Root cause:** `.send()` is not a real method on the `ContractAt` proxy object. It was never verified against documentation before use — a plausible-sounding method name borrowed from general Ethereum/web3 intuition, not GenLayer's actual API.

**Confirmed correct fix, per GenLayer's official "Working with Balances" documentation, full worked `TokenForwarder` example:**
```python
class TokenForwarder(gl.Contract):
    vault_contract: Address
    def __init__(self, vault_contract: str):
        self.vault_contract = Address(vault_contract)

    @gl.public.write.payable
    def forward(self) -> None:
        vault = gl.get_contract_at(self.vault_contract)
        amount = gl.message.value
        vault.emit_transfer(value=amount)  # pure "nameless" GEN transfer, no method call

    @gl.public.write.payable
    def donate_twice(self) -> bool:
        vault = gl.get_contract_at(self.vault_contract)
        amount = gl.message.value
        if self.balance < amount:  # self.balance = the CURRENT contract's own GEN balance
            return False
        vault.emit(value=amount * 2).save(self.address)  # value-ATTACHED method call — different from emit_transfer
        return True
```
- `.emit_transfer(value=amount)` — for a pure value transfer with no method call (this is what almost every settlement/slash/refund function needs).
- `.emit(value=amount).method_name(args)` — for calling an actual named method on another contract while attaching value. Different from `emit_transfer`.
- `self.balance` — a valid attribute for reading the current contract's own GEN balance.
- `gl.ContractAt(address)` is an older (v0.1.0-era) alias for `gl.get_contract_at(address)` — both construct the same proxy; `gl.get_contract_at` is the current confirmed name, matching this project's established TIER 1 rule.
- Before deploying any contract that transfers value, grep for `.send(` on any `get_contract_at()`/`ContractAt()` result and replace with `.emit_transfer(value=...)`. Never assume a plausible method name exists without checking the "Working with Balances" doc page directly.

**Confirmed via:** GenLayer's official "Working with Balances" documentation page, full `TokenForwarder` worked example.

---

### Bug 4 — storage-backed objects (e.g. a record read from a `TreeMap`) cannot be used directly inside a nondet block

**Symptom:** `UserWarning: Detected pickling storage class. Reading storage in nondet mode is not supported`, printed to stderr. This is a warning, not a hard crash — GenVM falls back to an unsupported pickling mechanism that may "mostly work" but is explicitly documented as not guaranteed-correct, meaning results could be subtly inconsistent across different validator nodes even though execution appears to complete.

**Root cause:** reading `self.some_storage_field[key]` (e.g. `self.disputes[dispute_id]`) directly from within a function that executes inside `run_nondet_unsafe` (i.e., `leader_fn` or `validator_fn`, or anything they call) crosses a storage-backed object into the nondet block, which GenVM's runtime cannot safely handle.

**Confirmed fix, per GenLayer's official storage documentation, exact code example:**
```python
storage_x = self.some_field           # storage-backed, a "view," not real data
memory_x = gl.storage.copy_to_memory(storage_x)   # a genuine in-memory copy

def my_nondet_function():
    # print(storage_x)   # Error - storage not accessible inside nondet!
    print(memory_x)      # Works — this is a real, safe, in-memory value
```
**Rule:** read the storage-backed record ONCE in the plain deterministic body of the write method (before calling `run_nondet_unsafe`), call `gl.storage.copy_to_memory(...)` on it, and pass only the memory copy into the leader/validator logic. Never let `leader_fn`/`validator_fn` (or anything they call) touch a storage-backed field directly.

**Confirmed via:** docs.genlayer.com/developers/intelligent-contracts/storage, explicit code example matching this exact scenario.

### Bug 5 — a class-body attribute with a type annotation is ALWAYS a storage field, even if meant as a constant

**Symptom:** the exact same `UserWarning: Detected pickling storage class...` warning persisted even after Bug 4 was fully fixed — the dispute record itself was correctly memory-copied, yet the warning reappeared identically on the very next redeploy. This was the most subtle bug in the whole catalog, because the culprit didn't look anything like "storage."

**Root cause:** a value declared like this, inside the contract class body —
```python
class MyContract(gl.Contract):
    CHARTER: str = "some fixed instruction text for the LLM..."
```
— is treated by GenVM as a genuine persistent storage field, per GenLayer's own storage documentation: "All persistent fields must be declared in the class body and annotated with types." This is true regardless of programmer intent — even though `CHARTER` here was semantically meant to be an immutable constant that never varies per instance and is never reassigned in `__init__`, the mere presence of a type-annotated class-body attribute is sufficient to make GenVM treat it as storage. Reading it via `self.CHARTER` inside a leader/validator function crosses another storage-backed value into the nondet block — the exact same bug class as Bug 4, just far less obvious, since "a string constant" doesn't intuitively register as "storage" the way a `TreeMap` record does.

**The rule, unconditionally:** any value meant to be a genuine, never-mutated constant belongs at module level, entirely outside the class body — e.g.:
```python
_CHARTER = (
    "some fixed instruction text for the LLM..."
)

class MyContract(gl.Contract):
    # only genuine, mutable, per-instance storage fields go here,
    # each with a type annotation
    disputes: TreeMap[u256, Dispute]
```
A module-level constant is never storage-backed under any circumstances and can be freely referenced from anywhere, including inside nondet blocks, with zero risk. Never declare a class-body attribute with a type annotation unless it is genuinely meant to be a mutable, per-instance storage field.

**Confirmed via:** the same official storage documentation as Bug 4 (the "must be declared... and annotated with types" line), applied to a case the docs don't explicitly call out as a trap — this is an inference from the documented rule, confirmed empirically by the warning disappearing once `CHARTER` was moved to module level.

### Bug 6 — leader/validator logic must be nested functions, NEVER instance methods called via `self.method_name(...)`

**Symptom:** the pickling warning from Bugs 4/5 can persist even after fixing every specific storage-field access you can find, if `leader_fn`/`validator_fn` are still structured as separate instance methods.

**Root cause:** defining leader/validator logic like this —
```python
class MyContract(gl.Contract):
    def _resolve_leader(self, d):
        pass
    def _resolve_validator(self, leaders_res, d):
        pass

    @gl.public.write
    def resolve(self, dispute_id):
        result = gl.vm.run_nondet_unsafe(
            lambda: self._resolve_leader(d_mem),
            lambda leaders_res: self._resolve_validator(leaders_res, d_mem),
        )
```
— calls `self._resolve_leader(...)` and `self._resolve_validator(...)` as bound methods. A bound-method call inherently carries `self` — the entire contract instance, which owns every single storage field the contract has — into the nondet closure, regardless of which specific field the method body actually touches. This may be sufficient on its own to trigger the pickling warning, independent of any individual field access.

**Confirmed via two independent sources:**
1. Real, documented testimony from an actual GenLayer developer's build experience: "you cannot access `self` inside a non-deterministic block."
2. The structural pattern of GenLayer's own official WizardOfCoin example — which always defines `leader_fn`/`validator_fn` as nested functions directly inside the `@gl.public.write` method, never as separate instance methods, and calls `leader_fn()` directly from inside `validator_fn` (never `self.leader_fn()` or any `self.`-prefixed reference of any kind).

**THE FIX, and the single most important structural rule in this entire catalog:** always define `leader_fn`/`validator_fn` as nested functions, declared directly inside the `@gl.public.write` method that calls `run_nondet_unsafe`, closing only over: (a) plain local variables (memory-copied storage values via Bug 4's fix, plain scalar parameters), and (b) module-level constants/helper functions (Bug 5's fix, plus pure functions like `_sanitize`/`_fetch_text`/`_parse_leader_json`). Zero `self.` references of any kind, anywhere in the body of either nested function. `validator_fn` calls `leader_fn()` directly — the nested function reference — never a bound method. See section 5 for the complete, verified-correct template built on this exact structure.

**This rule has no exceptions and applies to every future contract, no matter how small the leader/validator logic seems.** Even a leader/validator pair with seemingly trivial bodies must be nested functions, never instance methods, from the very first draft — this is not an optimization to apply later, it's foundational structure.

### Bug 7 — `DynArray` can never be constructed by user code, under any calling convention, including as a nested `@allow_storage` dataclass field

**Symptom, in order of escalating attempts (all confirmed live, Recourse, Aug 2026):**
1. `DynArray[str]()` as a dataclass field's constructor argument: `TypeError: this class can't be instantiated by user`.
2. `gl.storage.inmem_allocate(DynArray[str])`, pattern-matched from the working `TreeMap[str, str]` `inmem_allocate` example: `TypeError: _GenericAlias.__init__() missing 1 required positional argument: 'args'`.

**Root cause:** per GenLayer's own SDK API reference, `DynArray.__init__()` is documented unconditionally: *"This class can't be created with DynArray() ... Raises: TypeError – always."* This is not a missing-argument problem to solve by passing different args — no calling convention constructs a `DynArray` directly, ever. `inmem_allocate` does not route around this; it still calls the type's own `__init__` underneath, so it fails identically. This is a materially different situation from `TreeMap`, which tolerates bare `TreeMap()` construction (confirmed via a real deployed contract's `self.data = TreeMap()` in `__init__`) — the two container types are not interchangeable under this rule despite both being generic storage containers.

**What DOES work, confirmed via the storage docs' own examples:** a `DynArray` field declared directly on a top-level `gl.Contract` (never a nested `@allow_storage` dataclass) needs no construction at all — it zero-initializes to `[]` automatically, and is only ever populated via `.append()` after the fact (e.g. `self.string_items.append(item)` in the confirmed `GenericContract`/`add_item` example). No working example of a populated `DynArray` living on a *nested* dataclass field was found anywhere across official docs, the SDK reference, or any deployed contract during this debugging.

**Confirmed-safe patterns, in order of preference:**
1. **Best:** if the array genuinely only needs to exist once per contract (not once per record), put it directly on the top-level `gl.Contract` class, not on a nested struct. Zero-initializes safely, `.append()` works immediately.
2. **If it must be per-record** (e.g. one array of items per dispute/engagement, keyed by a record ID): do not use `DynArray` on the nested dataclass at all. Store the data as a single delimiter-joined `str` field instead (confirmed working, Recourse), with paired module-level `_join_x`/`_split_x` helpers converting to/from a real list only where needed (prompt-building, view responses). Pick a delimiter unlikely to appear in sanitized user text (e.g. a non-printable Unicode symbol), and defensively strip it from each item at join time regardless, since `_sanitize`'s printable-character rule does not itself guarantee the delimiter's absence.
3. If a genuinely nested per-record array turns out to be unavoidable for a future contract, this remains an open question — verify against GenLayer's actual current SDK source (not doc prose) before attempting a fourth construction pattern, per section 13.1's escalation-order lesson, rather than repeating any of the two failed attempts above.

**Confirmed via:** live Studio failures (both tracebacks above, Recourse, Aug 2026), the SDK API reference's unconditional `DynArray.__init__` documentation, the storage docs' `PersistentContract`/`GenericContract` worked examples, and `generate.html`'s actual codegen source (confirms non-generic `@allow_storage` dataclasses use unmodified, plain-Python `__init__` semantics — relevant because it's what ruled out a fourth, never-attempted "just omit the field" approach before it could become a third live failure).

**Confirmed design principle — lock the checkable criteria structurally before either party has incentive to reshape them (Recourse, `spec_items` locked at `create_engagement`; MilestoneVault, criterion/target locked at `create_milestone`).** This is distinct from evidence-fetching (above) — it's about *when* the thing being checked against becomes immutable, not *where* the evidence comes from. The failure mode this prevents: a party proposing or agreeing to criteria that can still be renegotiated after they have information about the outcome (e.g. a client redefining "done" after seeing the delivered work, a submitter picking a deadline after knowing whether they beat it — see Chronomark's rejection in section 11, which failed on exactly the deadline-precommitment half of this). Concretely: any field a contract will later judge a claim against — a spec, a criterion, a deadline, a target value — should be written to storage at the earliest possible write call, structurally before the write call that could benefit from reshaping it exists or can be invoked. Check this explicitly on every new concept: identify the field(s) the resolution judgment depends on, and confirm each is locked at a write call that happens *before* the party with an incentive to game it has any information about how the judgment might go. Confirmed via Recourse's own accepted-submission README, which states this as its explicit design thesis ("the spec itself gets renegotiated after the fact by whoever's currently unhappy... Recourse removes that by making the spec a locked, on-chain record... before any work begins") — not confirmed via specific staff feedback praising the mechanism, since Recourse's acceptance came with a generic acknowledgment rather than technical commentary (see section 11's Recourse entry).

**Confirmed reusable storage pattern — a lightweight index TreeMap alongside the full-record TreeMap, for any contract with a list-type view (Copyleft, `dispute_index: TreeMap[u256, DisputeIndexEntry]` alongside `disputes: TreeMap[u256, Dispute]`).** Every skeleton and the canonical template in section 5 store one record type per contract and imply that a "list all records" view, if needed, would iterate the same full-record map directly. Copyleft's accepted, live-verified contract does this differently and better: `DisputeIndexEntry` carries only `dispute_id`, `claimant`, `respondent`, `status` — four fields — while the full `Dispute` record carries claim text, rebuttal text, reasoning summaries, and URLs, each capped up to 2000/800 chars. `list_disputes()` iterates only the narrow index; a caller who wants one dispute's full detail calls `get_dispute(id)` separately against the full map. This avoids deserializing every long text field on every record just to render a status list. Concretely, for any future contract with more than a handful of expected records and a "list all" or "list mine" view: write both the narrow index entry and the full record on creation (see Copyleft's `file_dispute` for the pattern — both `self.disputes[did] = ...` and `self.dispute_index[did] = ...` in the same write call), keep the index entry's fields updated wherever status changes (Copyleft updates `entry.status` at every state transition, immediately after updating the full record), and never let the index carry a field whose length could grow — it exists specifically to stay cheap to iterate. This is exactly the kind of community-reusable primitive staff's own stated goal for the Intelligent Contracts track calls for (section 10.1) — worth considering as a standalone submission on that track in its own right (a "list-view storage pattern" demonstration), separate from reusing it inside a Projects-track concept.

**Confirmed refinement to Bug 4 (section 4) — sequencing when a write method mutates a field, persists it, then also needs that same value inside a nondet block later in the same call (Copyleft, `request_cure`).** Bug 4's existing rule ("read the storage-backed record ONCE... copy_to_memory... before run_nondet_unsafe") doesn't by itself cover this case: `request_cure` mutates `d.cure_commit_url`, writes `self.disputes[dispute_id] = d`, and then needs `d`'s updated state inside `leader_fn`/`validator_fn`. The confirmed-correct sequence, live-tested: mutate the local `d`, write it to storage (`self.disputes[dispute_id] = d`), then call `copy_to_memory(d)` on that same already-mutated local object — never re-read from `self.disputes[dispute_id]` a second time (a redundant storage read) and never skip the storage write before the memory copy (the mutation wouldn't be durably persisted before the nondet call, even though the nondet block would still see it locally). The rule this generalizes to: when a write method both persists a mutation and needs that mutation's value inside a later nondet block in the same call, write to storage first, then memory-copy the same local variable you just wrote — don't re-read.

**Cross-model LLM variance is real and expected.** Different validators can run different underlying LLM providers/models (OpenAI, Ollama, etc. — confirmed via the `node_config`/`model`/`provider` fields visible in real transaction data on the explorer). This means exact JSON key names and value formatting are not guaranteed to match between leader and validator re-derivation, even on a fully correct contract. Consequences:
- Parse LLM JSON output defensively: check multiple possible key names a model might reasonably use (key aliasing) and coerce numeric-looking values robustly (never assuming a field arrives as exactly the requested type). This is GenLayer's own documented "Defensive Response Parsing" guidance, not an invented precaution.
- Size confidence-tolerance bands generously — 150bps out of a 0-1000 range was too tight in practice; 200bps confirmed reasonable given real cross-model variance observed live (confidence scores of 720, 420, and 320 were all produced by the same underlying LLM-judgment call across repeated tests of one intentionally-ambiguous dispute).
- For malformed/unparseable LLM output specifically (not just numeric variance, but genuinely broken output): the documented-correct response is to let `validator_fn` disagree (`return False`), forcing a leader rotation. Do not try to engineer agreement on garbage output — this is correct, expected GenLayer behavior, confirmed directly in official docs' "Error Patterns for Consensus" guidance.
- Leader rotation itself (a transaction going through 2+ consensus rounds before finalizing) is healthy, expected behavior for any genuinely ambiguous LLM judgment call — not a bug. Distinguish "healthy disagreement/rotation" from "an actual crash" by checking `execution_result` (`SUCCESS` vs `ERROR`) and `contract_state_hash` (whether it matches across nodes that reached the same conclusion) — a vote split where every participating node shows `SUCCESS` is healthy variance; a vote split where anyone shows `ERROR` needs real investigation.
- This has not yet been tested against a dispute with clear-cut, decisive evidence (only an intentionally ambiguous test dispute has been run repeatedly) — whether confidence variance and rotation frequency drop substantially on a decisive case, or whether the variance is inherent regardless of evidence clarity, is still an open question worth checking on a future build.

**UPDATE (Recourse, Aug 2026) — the above question is now answered, at least for genuinely decisive cases:** testing an unambiguous `unverifiable` case (a hard DNS/connection failure via a `.invalid`-TLD URL, not a subtle judgment call) produced `confidence_bps` of 994, 950, and 1000 across separate resolution calls, with zero or one leader rotation each time. Confidence variance and rotation both appear to drop substantially — close to disappearing — when the evidence genuinely leaves no room for interpretation. This is consistent with, not contradictory to, the earlier ambiguous-case findings above: the variance appears to scale with genuine interpretive ambiguity in the underlying judgment, not with the mechanism itself being inherently noisy.

**Graded-outcome ladder — a new verdict-shape option, adapted from an external accepted contract's confirmed design (Aug 2026).** This SUPPLEMENTS the confidence-bps tolerance-band pattern above, for concepts where it genuinely fits — it does not replace confidence-bps for binary/three-way verdicts, where the existing pattern remains correct. The pattern: instead of a verdict field plus a *separately LLM-invented* confidence-bps number the validator tolerance-bands, define four or more ordered outcome severities (e.g. `strongly_supported` through `fabricated_or_unverifiable`) and a fixed lookup table mapping each outcome directly to its deterministic consequence (a slash percentage, a reputation delta, whatever the concept's economics need). The validator agreement check then works on ORDINAL DISTANCE between the leader's and validator's independently-chosen outcome (via index position in a fixed, ordered tuple), not on a raw invented number: adjacent-rung disagreement (e.g. `weak_evidence` vs `materially_irrelevant`) is tolerated as plausible cross-model variance, while a wide swing (e.g. `strongly_supported` vs `fabricated`) is correctly rejected. This is meaningfully different from tolerance-banding confidence-bps: confidence-bps is a number the LLM is free to invent anywhere in a 0-1000 range each call, so a tolerance band is negotiating agreement on something inherently continuous and freely chosen. An outcome ladder forces the LLM to commit to one of a small, fixed, named set each call — there is structurally less room for two independent validators to drift apart when there are only five or six valid answers with fixed, pre-agreed meanings, versus an unbounded number. **Confirmed real advantage, not just a theoretical one:** the source contract's own edge-case tests (found in its test suite, not just claimed in a comment) show the ordinal-distance check correctly passing on a one-rung slash-percentage gap with a reward-eligibility flip, and correctly rejecting a case where reward-eligibility differs even with a small slash gap — i.e., binary/discrete fields derived from the outcome are held to exact agreement, and only the outcome's ordinal position itself gets any tolerance. **Rule for using this shape:** only reach for it when the real-world judgment has four or more genuinely, meaningfully different severities — do not pad a three-way verdict into a five-way ladder just to use the pattern; a ladder with redundant or near-synonymous rungs is worse than an honest three-way verdict, and this project's own verdict-enum-reachability check (Rule 0.8's sibling note in section 2) will treat any rung no `leader_fn` branch can actually produce as a confirmed rejection risk, same as any other unreachable verdict value.

**Bug 8 — `gl.message_raw["datetime"]` is an ISO-8601 UTC string, not a Unix integer (confirmed live, Aug 2026).** Calling `int()` on it directly raises `ValueError: invalid literal for int() with base 10: '2026-08-15T01:52:14.768822Z'` immediately — confirmed via live GenVM stderr. The exact format: `YYYY-MM-DDTHH:MM:SS.ffffffZ`, always UTC, microsecond precision, trailing `Z`. This was previously an open, unconfirmed question in this document (Recourse's own gap note said this format was "never confirmed against a worked example") — it is now settled by a live failure. **Confirmed-correct fix:** a hand-rolled parser using only integer arithmetic — never `float()` (TIER 1 rule), never a stdlib `datetime` import (GenVM's exact Python build is not independently confirmed, and a fully auditable hand-rolled parser is preferred over trusting unconfirmed stdlib behavior across versions). Independently verified against Python's own `datetime` as an oracle across six cases, including the year-2100 non-leap-century edge case (2100 is divisible by 4 but not 400 — the single case naive leap-year logic most commonly gets wrong). The confirmed-correct `_now_epoch_seconds()` implementation is in both skeletons (Project files) — copy verbatim, do not re-derive this parsing by hand on a future contract.

**Bug 9 — plain GitHub commit URLs return HTML, not diff content, when fetched server-side (confirmed live, Aug 2026).** Fetching `github.com/<owner>/<repo>/commit/<sha>` via `gl.nondet.web.request()` or `gl.nondet.web.get()` returns GitHub's rendered HTML page shell — GitHub renders the actual diff client-side via JavaScript, which a server-side fetch never executes. Confirmed independently by five validators converging identically on "no visible diff or code changes" in the fetched content. **Confirmed-correct fix:** GitHub serves raw plain-text diffs at the same URL with `.diff` (or `.patch`) appended — confirmed via multiple independent, long-standing developer references. The confirmed-correct `_to_raw_diff_url()` implementation is in both skeletons — only rewrites plain `.../commit/<sha>` URLs; PR-scoped commit URLs (`.../pull/<n>/commits/<sha>`) have confirmed-inconsistent `.diff` support and are deliberately left unmodified. Always keep a fallback that fetches the original URL if the `.diff` fetch itself fails.

**Bug 10 — a `TreeMap` keyed by an `Address`-derived value must be normalized identically at every write and read site (confirmed live, Aug 2026).** A real bug: an internal write used `sender.as_hex` unnormalized (which preserves real EIP-55 mixed-case checksum casing), while an external read force-lowercased its plain-string input — two different key strings, silent miss, every time, for every real address, regardless of how much data existed. This was invisible during testing because every *internal* write-to-write comparison used the same unnormalized convention on both sides; it only broke at the *external* boundary between a plain string input and an `Address`-object-derived key. **The rule:** any `TreeMap` keyed by something derived from an `Address` object, if also looked up via a plain external string anywhere, must be normalized (lowercase is the confirmed-working convention) at every single site that constructs that key — write and read, without exception. Do not trust that one test address happening to match hides this class of bug.

**Bug 11 — `DynArray` on a nested `@allow_storage` dataclass field, via plain-list-literal assignment (UNCONFIRMED, worth testing, NOT yet a confirmed fix to Bug 7).** An external accepted contract's source contains this pattern: `self.some_treemap[key] = []` (a plain Python list literal, assigned into a `TreeMap[..., DynArray[SomeType]]` value slot) followed by retrieving that value and calling `.append(SomeType(...))` on it — never calling `DynArray[SomeType]()` or `gl.storage.inmem_allocate(DynArray[...])` explicitly, both of which Bug 7 confirms raise live. This pattern is exercised by that contract's own test suite, which round-trips correctly: a record is created via the real `@gl.public.write` method, and reading it back afterward shows the appended values present and correct. **This is real evidence, stronger than an unverified comment — but it is not the same claim as a live GenLayer Studio deploy.** That contract's own test-suite documentation states explicitly that its test harness runs "only the leader function" and does not exercise validator disagreement or real GenVM storage-pickling behavior — which is precisely the layer Bugs 4, 5, and 6 in this catalog came from. A test harness passing does not rule out a live-only pickling warning the same way early write-function success didn't rule out Copyleft's own later-surfacing bugs in its six-bug debugging history. **What this means going forward:** both skeletons default to the delimiter-joined `str` pattern (Bug 7's confirmed-safe fix) rather than this one, until a live Studio deploy confirms otherwise. Claude can write the minimal isolated test contract for this on request and mention once that it's available — but doesn't insist the person run it before proceeding with anything else; the safe default stays in place either way, so there's no risk in leaving this untested for now.

**Update to Bug 7 and Bug 11 (Sep 2026, read from the SDK source that the pinned runner `1jb45…` depends on):** (1) `DynArray.__init__` raises `TypeError` unconditionally (`storage/vec.py`) — the source-level explanation for Bug 7's two live failures. (2) The array's storage descriptor, `_DynArrayDesc.set()`, accepts any `collections.abc.Sequence` and writes the length then each element, so assigning a plain list to a slot typed `DynArray[T]` is handled by the descriptor. That is real evidence Bug 11's pattern is an intended path. It is still not a live-Studio confirmation, and the official `write-contract` skill states that `self.items = [x]` "does not work" (for a top-level field) — the two claims conflict and neither has been run against a real deploy here. Default stays the delimiter-joined `str`.

**Bug 12 — `datetime.datetime.now()` as a claimed alternative to `gl.message_raw["datetime"]` string-parsing (UNCONFIRMED, worth testing, NOT a replacement for `_now_epoch_seconds()` yet).** An external accepted contract uses `datetime.datetime.now(datetime.timezone.utc).timestamp()` directly, with a code comment asserting "GenVM patches `datetime.now()` to the network's block time" — implying deterministic, identical values across independent validators, which would make Bug 8's entire hand-rolled parser unnecessary going forward. Official GenLayer storage documentation does confirm `datetime.datetime.now()` is legal to call inside a `@gl.public.write` method and store on a dataclass field — that part is real and confirmed. What is NOT confirmed anywhere in official docs, and not tested anywhere in that external contract's own repository: that the value returned is IDENTICAL across independently-executing validators, as opposed to each validator's own real wall-clock (which would differ by milliseconds and break exact-match consensus). This project's own most recent build (DomainClaim's post-CitationChain-rejection rewrite) was written with full knowledge of this claim and still chose to keep `_now_epoch_seconds()` rather than adopt the shortcut — a second, independent data point that the claim wasn't trusted without live proof, even by a build under real time pressure. **What this means going forward:** `_now_epoch_seconds()` stays the default. Claude can write the two-line isolated test contract for this on request and mention once that it's available — checking GenLayer Studio's own validator-agreement view would settle whether every participating validator produces an identical value — but doesn't insist on it before continuing other work. If ever confirmed live, this becomes a real Bug 12 fix simplifying future timestamp handling; until then, nothing about the safe default changes whether or not the test gets run.

**Update to Bug 12 (Sep 2026, GenVM spec `02-wasip1.rst` and ADR-000):** `clock_time_get` "returns transaction unix timestamp in **both** modes, regardless of the requested clock id." Python's `datetime.datetime.now()` reads that clock, so per spec it returns the transaction timestamp — identical for leader and validators — not each node's wall clock. This upgrades the claim from "asserted in a code comment" to "documented by GenVM's own spec"; it is still not a live cross-validator test. Also confirmed: a contract using `datetime.datetime.now(datetime.timezone.utc)` passes `genvm-lint check`. Do not confuse it with the separate `GetTimestamp` gl_call, which returns real wall-clock time in non-det mode. If adopted, use integer-only arithmetic (`.timestamp()` and `.total_seconds()` return floats): `d = datetime.datetime.now(datetime.timezone.utc) - datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)` then `epoch = d.days * 86400 + d.seconds`. `_now_epoch_seconds()` stays the default until one live Studio transaction shows identical values across validators.

**Confirmed distinction — two real fetch tools for two different needs.** `gl.nondet.web.get()` (Bug 1's confirmed pattern) and `gl.nondet.web.request(url, method='GET')` have the **identical** response shape (`.status`, `.body`) — confirmed against the SDK source (both return the same `Response` dataclass), not assumed. `.request()` is the more precise tool for a structured JSON API specifically; `.get()` remains right for general webpages. Both skeletons carry a `_fetch_json()` helper built on `.request()`, parsing the JSON response directly rather than handing back raw text — shipped commented out, because `genvm-lint` fails (E010) on a helper containing `gl.nondet.*` that no leader/validator can reach. Uncomment it only when `leader_fn` actually calls it.

**Confirmed, generalized rule — every field an on-chain verdict, score, or judgment depends on must be independently re-derived and compared inside `validator_fn`, never excluded from the agreement check because it's "just a number" (confirmed live, Aug 2026, across three structurally different real-world inputs with zero problematic rotation).** A validator that agrees on a coarse verdict bucket while a leader alone decides the specific numeric fields that determine the actual outcome is the same "format-only check proves nothing" rejection pattern already confirmed in section 3 — just operating at the individual-field level instead of the whole-response level. This is not a hypothetical risk to guard against; it is a gap a real, structurally sound-looking contract can have. Apply this to every numeric or categorical field a future contract's verdict depends on, not only the ones that feel like the "main" output.
