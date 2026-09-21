# Phase 0: Repository and Provenance Inventory

**Date:** September 7, 2026  
**Status:** Complete  
**Plan:** `ACTION_PLAN.md`, Phase 0

## Purpose and scope

This report records the repository, source ownership, provenance, licensing, dependencies, test baseline, and artifact conventions relevant to the planned migration of the Lode Runner literate source from LaTeX documentation to Markdown documentation.

Phase 0 made no changes to the upstream Lode Runner source, performed no source conversion, introduced no parser architecture, and implemented no HTML browser.

## Baseline

The repository was inspected at commit `3a8abfb4e3dbf733c97b33f8928420da831efa6b`. At the time of the baseline test, the only working-tree changes were the intentional addition of `reference/ultima1_reveng/README.md` and its inclusion in `manifest.lst`.

The local environment used Python 3.14.5.

The baseline command was:

`make test`

The suite was all green.

The project currently declares these development dependencies in `requirements.txt`:

- `black>=24.0`
- `pytest>=8.0`

The bundled Lode Runner weaver uses only the Python standard library. Its upstream documentation states Python 3.9 or later.

## Repository paths and ownership

| Path                                    | Current function |
|-----------------------------------------| --- |
| `reference/lode_runner_reveng/main.nw`  | Authoritative upstream Lode Runner LaTeX/Noweb source; must remain untouched |
| `reference/lode_runner_reveng/main.pdf` | Upstream woven reading view and navigation reference |
| `reference/lode_runner_reveng/weave.py` | Bundled upstream parser, relationship analyzer, LaTeX weaver, and tangler |
| `scripts/nwtool.py`                     | Project-owned command-line research interface |
| `tests/test_nwtool.py`                  | Behavioral specification for the current `nwtool` interface |
| `reference/ultima1_reveng/`             | Attributed reference snapshot of the later Ultima Markdown and HTML implementation |
| `docs/reports/literate-migration/`      | Maintained phase reports |
| `tests/fixtures/oracles/`               | Future machine-readable structural oracle fixtures |
| `tests/golden/nwtool/`                  | Future reviewed `nwtool` command-output goldens |
| `research/lode_runner/main.nw`          | Selected path for the future project-owned Markdown/Noweb adaptation |

The selected `research/lode_runner/main.nw` path creates a clear distinction between:

- upstream source preserved under `reference/`;
- project-owned maintained literate source under `research/`; and
- explanatory research notes under `docs/`.

The selected path does not exist yet. It will be created only during an approved later migration phase.

## Current parsing and tool path

A current `nwtool` action follows this path:

1. The user runs `scripts/nwtool.py` directly or through a `Makefile` target.
2. `scripts/nwtool.py` reads the selected `.nw` source.
3. It imports `reference/lode_runner_reveng/weave.py`.
4. `Weaver.extract_chunk_info()` computes the whole-source chunk and identifier relationships.
5. The `chapter`, `index`, or `chunk` renderer formats the relevant part of that shared analysis as Markdown.

All three public `nwtool` commands therefore use the same parsing and relationship analysis. They do not maintain separate parsers.

The implementation defining that analysis currently lives under `reference/`, where upstream material is preserved. Phase 3 must decide whether project-owned consumers should continue using that implementation through a documented boundary or whether the required parsing and graph behavior should move into a project-owned module or adapter. No parser move or rewrite is justified during Phases 0-2.

## Build and tooling commands

The root `Makefile` provides the current supported commands:

| Command | Purpose |
| --- | --- |
| `make setup` | Create `.venv` and install `requirements.txt` |
| `make test` | Run the complete test suite |
| `make test-verbose` | Run the suite with verbose output |
| `make nwchapter CHAPTER=N` | Export one chapter as compact woven Markdown |
| `make nwindex` | Regenerate the tracked whole-source index |
| `make nwchunk NAME="..."` | Export a named chunk and its immediate referenced chunks |
| `make filesdump` | Regenerate the project context dump |
| `make gentree` | Regenerate `tmp/project_tree.txt` |
| `make clean` | Remove the virtual environment, caches, and temporary output |

The existing tests establish these conventions:

- public command behavior is exercised through subprocesses;
- focused parser and rendering cases use `tests/fixtures/mini.nw`;
- integration smoke tests use `reference/lode_runner_reveng/main.nw`;
- generated test output uses pytest's temporary directories;
- CRLF input is tested explicitly;
- generated Markdown uses LF line endings;
- source ranges are one-based and inclusive in user-facing output.

## Generated and maintained artifacts

`tmp/` and `build/` are ignored and are appropriate for disposable generated output.

`docs/main-nw/main-index.md` is generated by `make nwindex` and tracked by Git. It is a maintained research-navigation artifact even though it is generated.

Future structural oracle files under `tests/fixtures/oracles/` will also be generated and tracked. Unlike temporary output, they will be committed because they form part of the migration test specification.

Future HTML output should remain under an ignored build directory unless a later explicit decision changes repository policy.

## Line endings and exact source preservation

The repository's `.gitattributes` forces LF line endings for text files in the shared macOS and Windows working tree.

This establishes LF as the checked-out source convention, but Phase 2 must still define exact structural-oracle byte boundaries.

Parsing may operate on decoded logical lines. Exact header and body hashes must instead be calculated from the checked-out source bytes or from byte ranges whose newline treatment is explicitly defined. Reconstructing source with `splitlines()` and joining it again is not sufficient evidence of byte-for-byte preservation.

## Lode Runner provenance and license

The upstream Lode Runner repository identifies its work as licensed under the Creative Commons Attribution-ShareAlike 4.0 International license.

The future Markdown/Noweb source will be an adaptation of that upstream work. It must preserve appropriate attribution, identify the upstream source and revision, describe the adaptation, and observe the applicable ShareAlike requirements.

Detailed project-wide license and attribution documentation is deferred until the relevant project-owned adaptation is about to be created. The repository is private, but that does not remove the need to understand and document the terms governing adapted upstream material.

## Ultima reference provenance and license

`reference/ultima1_reveng/PROVENANCE.md` records the Ultima reference snapshot as originating from XekriRedmane's `ultima1_reveng` repository at commit `7467ca80a63f76a8d29a70cbe8596e5c422aef5d`, dated August 15, 2026.

The imported reference material includes:

- `README.md`;
- `html-migration-design.md`;
- `latex_to_md.py`;
- `weave.py`;
- `weave_html.py`;
- `web/app.js`;
- `web/style.css`;
- `sample.nw`.

No license was identified for the Ultima repository or snapshot during Phase 0. The files may remain as attributed reference material in this private research repository, but substantial source copying or derived implementation should not enter project-owned deliverables until the licensing question is resolved.

The intended later action is to ask XekriRedmane for an appropriate license before adapting substantial Ultima implementation code. Until then, later implementation should distinguish architectural ideas and observed behavior from copied source text.

This report records project handling rather than legal advice.

The existing `reference/ultima1_reveng/PROVENANCE.md` also contains a stale reproducibility note saying that the original commit still needs to be identified, even though the full commit is now recorded. That documentation cleanup is deferred to the end-of-session project-artifact pass.

## Ultima-only dependencies

The Ultima HTML reference uses Python packages and browser libraries that are not current `a2-lode-runner` dependencies:

- `absl-py`;
- `mistune`;
- Mermaid loaded from a CDN;
- KaTeX loaded from a CDN;
- MiniSearch loaded from a CDN.

No dependency should be added merely because it appears in the reference implementation. Phases 0-2 require no additional dependency. HTML dependencies should be selected only when a project-owned HTML implementation has an approved design and a real consumer.

## Action-plan assumptions

### Confirmed

- The existing upstream directory is named `reference/lode_runner_reveng/`.
- The authoritative upstream source is `reference/lode_runner_reveng/main.nw`.
- The upstream source must remain untouched.
- The Lode Runner parser supports chunk names richer than the Ultima parser's regular expressions allow.
- The current Lode Runner parser provides chunk order, continuations, references, backlinks, `%def` declarations, and detected identifier uses.
- The current `nwtool` commands share one whole-source analysis.
- The Ultima HTML weaver depends on its `weave.py` source model.
- The Ultima HTML command tangles assembly as a side effect, which is not wanted for the future Lode Runner documentation build.
- There is one public project-owned `scripts/nwtool.py`.
- The report, oracle, and golden-output directories are prepared but do not yet contain their Phase 1 or Phase 2 deliverables.
- Temporary and build output are ignored.
- The generated `docs/main-nw/main-index.md` is tracked.

### Partially confirmed

- The current Lode Runner parser appears suitable for Phase 1 source classification and for informing Phase 2, but its complete migration contract has not been frozen.
- LF is the repository checkout convention, but exact Phase 2 header and body byte ranges remain to be defined.
- `research/lode_runner/main.nw` is now the selected destination path, but no source will be created there until the applicable migration phase is approved.

### Contradicted or stale

- `reference/ultima1_reveng/PROVENANCE.md` says the upstream commit still needs to be identified, although it now records the full commit.
- `GOALS.md` contains a stale Noweb-tooling status paragraph and a duplicated Current Session Pointer heading.
- `ACTION_PLAN.md` permits Phases 0-2 within its broad execution boundary, while the narrower current session pointer authorizes only Phase 0 and Phase 1. The current session pointer controls this session, so Phase 2 will not begin.

## Open items carried forward

- Measure and classify the actual LaTeX surface of `reference/lode_runner_reveng/main.nw` in Phase 1.
- Compare that surface with the assumptions and transforms in `reference/ultima1_reveng/latex_to_md.py`.
- Define the structural-oracle schema and exact byte-range rules in Phase 2.
- Decide parser ownership and the shared source-model boundary in Phase 3.
- Resolve the Ultima reference license before substantial implementation adaptation.
- Add durable project license and attribution documentation when project-owned adapted material is about to be introduced.
- Clean up stale project-control and provenance documentation during the approved end-of-session artifact pass.
