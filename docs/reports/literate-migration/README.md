# Literate Migration Reports

This directory contains maintained reports produced while executing the literate-source migration described in `ACTION_PLAN.md`.

Reports:

- `phase-0-inventory.md` -- repository, provenance, licensing, and build inventory;
- `phase-1-converter-review.md` -- review of the supplied `latex_to_md.py` converter against the LaTeX constructs in the Lode Runner literate source.

The plan was closed after Phase 1 (see the status in `ACTION_PLAN.md`), so no further reports will be added.

These reports are project documentation, not transient build output. They should record conclusions, evidence, unresolved questions, and commands needed to reproduce relevant findings.

Do not add empty phase-report placeholders. Create each report when work on that phase begins.

Generated raw data should normally be placed under `tests/fixtures/oracles/` or another explicitly documented machine-artifact directory rather than embedded here without explanation.
