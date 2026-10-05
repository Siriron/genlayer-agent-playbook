# Intelligent Contracts submission — {{CONTRACT_NAME}}

Only a title and a description are submitted (docs/knowledge/10.1). The description must stay
under 1000 characters; count with `python scripts/check_limits.py contract-description "<text>"`.

**Title:** "{{specific technique or primitive, not a product name}}"

**Description:** "{{Lead with the concrete technique (the actual mechanism). Name the method(s), the
verdict/outcome shape, the evidence binding, and why it is reusable by another builder. No
scene-setting. State what the tests prove and do not prove.}}"

Pre-flight (all must be true):
- Not extracted from a Projects-track submission (counted twice).
- Not a learning exercise (would it exist in this form only to practice consensus?).
- Passes `bash scripts/audit_all.sh <contract.py>`; every verdict value traced to a leader_fn branch.
