# ACTION PLAN: Markdown and HTML workspace for Lode Runner reverse engineering

**Status:** Closed -- Phases 0-1 complete; Phases 2-9 not pursued. The HTML research browser was built on a shorter path instead (`latex_to_md.py` -> `research/main.nw-edited.md` -> `weave_html.py`); see `README.md`.  
**Approved:** September 7, 2026  
**Last updated:** September 21, 2026  
**Scope:** Create a project-owned Markdown adaptation of XekriRedmane's Lode Runner `main.nw`, preserve its literate-program structure, adapt `nwtool.py`, and build a static HTML research browser based on the later Ultima I HTML weaver.

## 1. Purpose

The upstream Lode Runner reverse-engineering document is a LaTeX/Noweb source whose primary human-readable output is a PDF. The PDF preserves the author's literate presentation, but it is cumbersome for research involving repeated movement among:

- prose explanations;
- code chunks and continued chunks;
- callers and referenced chunks;
- identifier definitions and uses;
- related material in other chapters.

XekriRedmane's later `ultima1_reveng` project addresses the same problem with a Markdown-authored Noweb document and a static, multi-page HTML browser. This subproject will adapt that approach to Lode Runner while retaining the existing Lode Runner parser behavior where it is already correct.

The result is intended to be useful independently of whether the larger Godot port reaches a playable prototype.

**Working spirit:** This is a private, curiosity-driven project, so motivation matters alongside technical rigor. Prefer bounded work that creates visible research value, recognize completed milestones, and keep safeguards proportionate to real risks. Be precise without turning the project into bureaucracy. When several approaches are sound, favor the one that preserves momentum, makes progress enjoyable, and leaves the next session inviting to begin.

## 2. Current execution boundary

Phases 0 and 1 are complete.

The next implementation session should perform **Phase 2 only**:

1. create a deterministic structural manifest from the untouched upstream source;
2. capture selected baseline outputs from the current `nwtool.py`;
3. add comparison tests suitable for validating the future Markdown source;
4. record unresolved references, repeated definitions, parser warnings, and other structural ambiguities;
5. recommend the smallest safe shared-source-model strategy for Phase 3.

Do not begin the maintained Markdown migration, manual documentation cleanup, `nwtool.py` retrofit, or HTML implementation during Phase 2.

Disposable experiments may be created under `tmp/`, but they must not become maintained project sources.

Stop after the Phase 2 report and request review.

## 3. Completed investigation

### 3.1 Phase 0: repository and licensing inventory — complete September 7, 2026

The repository layout, existing tools and tests, upstream Lode Runner files, and supplied Ultima-derived materials were inspected before conversion work.

Before copying Ultima-derived code into permanent project-owned paths, preserve the applicable licenses, notices, and attribution. If a specific supplied file's licensing remains undocumented, resolve that question before copying the file; do not repeat the broader repository inventory.

### 3.2 Phase 1: converter review — complete September 7, 2026

The Phase 1 findings are recorded in:

`docs/reports/literate-migration/phase-1-converter-review.md`

The supplied `latex_to_md.py` was tested against the actual Lode Runner source using the Lode Runner parser to distinguish documentation from code.

The mechanical conversion produced a tangle byte-identical to the upstream tangle. Both had this SHA-256 digest:

```text
be29dc257afe75605e0e3a5a0ddd6d311a2c7a7299bd3634c7a126c972f093a1
```

The remaining documentation-conversion work is bounded:

- one chapter title located on a Noweb documentation marker;
- seven standalone image commands;
- five table areas;
- one external `sprite_tables.tex` input;
- two TikZ diagrams;
- two presentation-only spacing commands;
- one multiline `[[...]]` quoted-code block;
- generated Noweb chunk and identifier index directives.

No display-math environments were found.

The multiline `[[...]]` passage is valid Noweb and renders correctly in the upstream PDF. The converter joins some physical lines because assembly dollar signs are mistaken for inline-math delimiters. The maintained Markdown source must restore the original line structure and represent the passage as an appropriate fenced code block.

These findings establish that:

- the existing converter is suitable for creating the initial adaptation;
- a comprehensive new LaTeX inventory system is unnecessary;
- a general-purpose converter rewrite is not a migration prerequisite;
- the remaining exceptions can be handled explicitly during source review;
- whole-file LaTeX scans must not count LaTeX-like assembly text as prose;
- equal tangles are valuable evidence but are not the sole structural oracle.

Do not repeat Phase 1 unless later evidence reveals a meaningful source construct absent from its report.

## 4. Target state

At completion, the repository contains:

1. The untouched upstream Lode Runner source under `reference/`.
2. A maintained, project-owned Markdown/Noweb adaptation of `main.nw`.
3. A retained and attributed migration script or wrapper sufficient to
   reproduce the initial mechanical conversion.
4. One shared source-model interface used by:
   - `scripts/nwtool.py`; and
   - the HTML weaver.
5. An adapted `weave_html.py` and its required static assets.
6. A generated static, multi-page HTML research site that:
   - presents Markdown prose and assembly chunks in source order;
   - provides chunk-reference and continuation navigation;
   - links identifiers to definitions and uses;
   - shows definitions, uses, and used-in relationships;
   - provides chunk and identifier indexes;
   - provides full-site search;
   - supports non-disruptive source previews;
   - works without an application server.
7. Tests proving that the migration preserved:
   - significant literate-source structure;
   - code-chunk headers and bodies under the canonical line-ending policy;
   - chunk and identifier relationships;
   - byte-for-byte tangled assembly output.

## 5. Source ownership

### 5.1 Upstream source

Do not modify:

`reference/lode_runner_reveng/main.nw`

Confirm the repository's actual spelling and path before creating related project-owned paths. Do not silently rename existing reference directories.

The upstream file remains the original LaTeX/Noweb artifact and the provenance reference.

### 5.2 Project-owned source

Create the maintained Markdown/Noweb source outside `reference/`.

Preferred path, unless repository conventions strongly indicate otherwise:

`research/lode_runner/main.nw`

Record the final path in this file and in the relevant build and tool documentation.

After migration, the Markdown source is maintained directly. It is not disposable generated output.

### 5.3 Migration tool

Keep the migration tool as a project-owned historical and diagnostic tool.

Its roles are:

- provenance;
- reproducibility;
- migration diagnostics;
- comparison with a fresh mechanical conversion;
- documentation of how the Markdown fork was created.

The tool must not overwrite the maintained Markdown source without an explicit operator request. The normal browser build must not regenerate Markdown from the upstream LaTeX source.

## 6. Migration invariants

The following must remain invariant between the upstream LaTeX source and the initial Markdown adaptation:

1. Number and order of code-chunk instances.
2. Exact code-chunk names.
3. Exact code-chunk headers after canonical line-ending normalization.
4. Exact code-chunk bodies after canonical line-ending normalization.
5. Chunk-reference targets and relationships.
6. Continued-chunk ordering.
7. `@ %def` markers and identifier declarations.
8. Chapter ordering and semantic boundaries.
9. No unresolved chunk reference introduced by migration.
10. Byte-for-byte equality of the tangled assembly output.

For source-level comparison, canonical line-ending normalization means converting CRLF or CR line endings to LF. No other whitespace, encoding, or content normalization is permitted.

The repository policy is:

```text
* text=auto eol=lf
```

The project-owned Markdown source must use LF. Do not edit the untouched upstream reference merely to normalize its working-tree representation.

Documentation chunks may change from LaTeX to Markdown.

Do not use successful HTML rendering or successful tangling alone as proof that all invariants hold. Verify source structure independently and programmatically.

## 7. Architecture

The intended architecture is:

```text
upstream LaTeX main.nw
        |
        +-- one-time migration tool
                    |
project-owned Markdown main.nw
                    |
          shared source-model interface
        +-----------+-----------+
        |                       |
scripts/nwtool.py          weave_html.py
LLM context output         static research site
```

The shared source model owns or exposes:

- ordered documentation and code units;
- chunk names and ordering;
- continuation instances;
- outgoing chunk references and incoming backlinks;
- identifier definitions and uses;
- chapter association;
- source ranges;
- stable identities suitable for links;
- diagnostics for malformed or unresolved constructs.

`nwtool.py` owns compact research-context extraction.

`weave_html.py` owns HTML layout and rendering.

Do not independently reimplement graph analysis in both consumers.

“Shared” does not require an immediate rewrite of the bundled Lode Runner parser. A project-owned adapter around its proven parsing behavior is acceptable if both consumers receive the same relationships and project-owned tests protect the required behavior.

The HTML build should not tangle assembly unless explicitly requested. Rendering documentation must not produce unrelated assembly files as a side effect.

Retain one public `nwtool.py`. Do not leave permanent old and new variants.

## 8. Non-goals

Do not:

- modify or annotate assembly during format migration;
- delete or edit the upstream source;
- make byte-perfect disk-image reproduction a prerequisite;
- build another comprehensive LaTeX inventory system;
- make broad converter improvements a prerequisite for migration;
- port Ultima-specific assembly postprocessors;
- narrow Lode Runner chunk names to Ultima-specific parser rules;
- rewrite `nwtool.py` from scratch;
- retain permanent `nwtool-old.py` and `nwtool-new.py` variants;
- duplicate graph analysis between tools;
- build an application server;
- add an annotation database or graph visualization;
- redesign the visual theme before validating navigation;
- preserve decorative PDF spacing in the Markdown source;
- preserve generated LaTeX chunk and identifier indexes;
- make every diagram conversion a blocker for the basic pipeline;
- conflate maintained source with generated site output;
- make the converter authoritative over the maintained Markdown source.

## 9. Phase 2: freeze the structural oracle

Before changing the maintained source format, capture the upstream source model in deterministic, reviewable form.

Create a structural manifest from the untouched LaTeX source. JSON is preferred unless repository conventions suggest another stable format.

For every code-chunk instance, record at least:

- ordinal number;
- exact chunk name;
- kind;
- source filename;
- start and end source range;
- SHA-256 hash of the canonical-LF header;
- SHA-256 hash of the canonical-LF body;
- SHA-256 hash of the canonical-LF header and body together;
- previous continuation identity;
- next continuation identity;
- referenced chunk names;
- incoming chunk references;
- declared identifiers;
- detected uses of declared identifiers.

Also record:

- chapter and part titles;
- chapter and part boundaries;
- total documentation- and code-chunk counts;
- ordered code-chunk names;
- continuation count per canonical chunk name;
- unresolved chunk references;
- duplicate or ambiguous labels;
- duplicate identifier definitions;
- parser warnings.

Use human-readable names and source order for relationships. Do not use opaque hashes as the only identities.

Source filenames and line ranges are provenance and diagnostic data. They are not expected to remain numerically identical after conversion. Migration parity must compare content, order, names, and relationships rather than equal filenames or line numbers.

The upstream manifest is an immutable baseline artifact. Do not overwrite it with a manifest generated from the migrated source. Later phases should produce a separate migrated manifest and compare it with the baseline through explicit assertions.

Raw-source hashes may also be recorded for provenance, but raw hashes must not reject an otherwise exact CRLF-to-LF migration.

### 9.1 Exact code comparison

Prepare tests that will compare:

```text
canonical_lf(original chunk header) == migrated chunk header
canonical_lf(original chunk body)   == migrated chunk body
```

Do not normalize trailing spaces, indentation, blank lines, encoding, or other content.

Also prepare a tangle comparison that:

1. tangles the upstream source;
2. tangles the migrated source;
3. compares the generated files byte-for-byte;
4. reports their SHA-256 hashes.

A matching tangle is necessary but not sufficient because structurally different literate sources can potentially produce the same assembled output.

### 9.2 Selected `nwtool.py` goldens

Capture representative output from the current `nwtool.py` before retrofitting
it.

Include:

- Chapter 8;
- one representative continued chunk;
- one chunk with several incoming references;
- one chunk with outgoing references;
- one identifier definition-and-use query;
- one repeated or ambiguous identifier definition, if present;
- the whole-source or chapter index.

Normalize only genuinely unstable information, such as absolute filesystem paths. Do not broadly normalize whitespace.

These goldens protect the usefulness and information density of `nwtool.py`, not every incidental formatting choice.

### 9.3 Phase 2 deliverables

Deliver:

- the immutable upstream structural manifest;
- tests or helpers for comparing a future migrated manifest;
- selected `nwtool.py` goldens;
- the exact test commands;
- source and chunk counts;
- unresolved and ambiguous relationships;
- current parser warnings;
- an assessment of whether the existing parser is reusable;
- the recommended smallest safe parser strategy for Phase 3;
- any required amendments to this plan.

Phase 2 does not implement a generalized parser API, migrate the maintained source, or begin the HTML weaver.

Stop after the Phase 2 report and request review.

## 10. Phase 3: establish the shared source model

This phase begins only after Phase 2 has been reviewed.

Compare:

1. the current Lode Runner `weave.py`;
2. Ultima's parser, if available and relevant;
3. the data contract expected by `weave_html.py`;
4. the data consumed by `nwtool.py`;
5. the structural baseline from Phase 2.

Prefer the smallest safe adaptation.

The likely approach is to preserve the Lode Runner parser's broader, already-tested chunk parsing and place a project-owned interface or adapter around it.

If parsing code is copied or refactored into a new project-owned module, prove parity against the Phase 2 manifest.

The source-model interface must provide:

- ordered source units;
- documentation/code distinction;
- canonical chunk names;
- continuation instances;
- source ranges;
- outgoing and incoming chunk references;
- `%def` declarations;
- identifier definitions and uses;
- chapter association;
- stable anchor identities;
- actionable diagnostics.

Do not place HTML-specific strings or rendering decisions in the core model.

Deliver:

- one documented source-model interface;
- parity tests against the upstream baseline;
- tests for actual Lode Runner chunk-name syntax;
- tests for continuations and repeated definitions;
- no broad HTML implementation beyond a small fixture if needed to validate the interface.

## 11. Phase 4: create the initial Markdown adaptation

Use the Phase 1 procedure to create a mechanical Markdown conversion from the untouched upstream source. The converter must operate through the Lode Runner parser rather than an incompatible narrower Ultima parser.

The migration procedure must:

- transform documentation chunks only;
- preserve Noweb code headers and bodies under canonical LF normalization;
- preserve `@` and `@ %def` markers;
- write to an explicit new destination;
- refuse accidental overwrite by default;
- produce deterministic output;
- run structural comparison after conversion;
- run byte-for-byte tangle comparison after conversion.

A broad converter rewrite is not required.

Minimal converter changes are allowed when necessary for reproducibility, diagnostics, or structural safety. Do not delay migration to implement capabilities unused by the actual source.

Retain an attributed project-owned script or wrapper sufficient to reproduce the mechanical conversion.

Where practical, commit the raw mechanical adaptation separately from manual documentation cleanup.

## 12. Phase 5: review the Markdown source

Review and clean the project-owned source in bounded passes without altering assembly.

Resolve the known Phase 1 exceptions:

1. Replace the chapter title on the documentation marker with:

   ```text
   @
   # Lode Runner
   ```

2. Convert the seven standalone images and verify their paths and alternative text.
3. Convert the five table areas near the beginning of the document.
4. Inspect and explicitly incorporate or replace `sprite_tables.tex`.
5. Choose appropriate representations for the two TikZ diagrams.
6. Remove the two presentation-only spacing commands.
7. Restore the original physical line structure of the multiline quoted assembly passage and represent it as fenced code.
8. Remove the LaTeX directives for generated “Defined Chunks” and “Index” sections; the HTML browser will generate those views.
9. Run a Noweb-aware, documentation-only scan for meaningful residual LaTeX.
10. Confirm that any remaining raw HTML or fenced LaTeX is intentional and documented.

Prefer semantic Markdown or HTML over visual imitation of the PDF.

Ordinary tables should generally become Markdown tables. Address maps, byte fields, or colored pixel grids may use semantic HTML/CSS or retained rendered images when that is clearer and more maintainable.

Manual corrections belong in the maintained Markdown source. Do not turn every one-off correction into recurring converter postprocessing.

Completion requirements:

- no unexplained converter TODO remains;
- every deferred diagram is explicitly tracked;
- source-structure parity remains green;
- code chunks remain exact under canonical LF comparison;
- upstream and migrated tangles remain byte-identical;
- the source is useful and reviewable as plain Markdown/Noweb.

## 13. Phase 6: retrofit `nwtool.py`

Retain one public `scripts/nwtool.py`.

Make it consume the project-owned Markdown source through the shared source model.

Preserve where practical:

- command names;
- argument behavior;
- compact output;
- source provenance;
- chunk and identifier query semantics;
- bounded output suitable for model context.

Update assumptions tied specifically to LaTeX, including:

- default source path;
- chapter and heading recognition;
- prose rendering;
- extraction around Markdown headings;
- Markdown tables;
- fenced code and Mermaid blocks;
- intentional raw Markdown HTML.

Run the Phase 2 golden comparisons. Formatting may intentionally change from LaTeX-oriented output to native Markdown, but loss of source content or relationships is unacceptable.

If the old implementation is needed for differential tests, keep it in test fixtures or retrieve it from version control. Do not expose it as a second supported command.

## 14. Phase 7: adapt the HTML weaver

Adapt Ultima's `weave_html.py` and useful static assets into project-owned paths, preserving required licenses and attribution.

The weaver must:

1. consume the shared Lode Runner source model;
2. avoid tangling unless explicitly requested;
3. support all actual Lode Runner chunk names;
4. support actual continuation and identifier relationships;
5. read the maintained Markdown source;
6. preserve source-order presentation;
7. use correct repository-relative image and asset paths;
8. avoid Ultima-specific roots, filenames, assembly targets, and postprocessors;
9. emit deterministic output;
10. fail visibly on missing dependencies or malformed source.

Implement features in this order:

1. Markdown prose and code chunks in source order.
2. Chapter/page splitting.
3. Table of contents and on-page outline.
4. Chunk-reference links.
5. Previous/next continuation navigation.
6. Used-in backlinks.
7. Identifier definition-and-use links.
8. Chunk and identifier indexes.
9. Hover or focus previews.
10. Search.
11. Collapse controls and theme polish.
12. Mermaid or KaTeX only where the maintained source requires them.

Do not require every visual feature before testing Chapter 8.

### 14.1 Static assets and dependencies

Retain features from the supplied JavaScript and CSS only where they remain useful and reliable. Information architecture and navigation take priority over cosmetic parity with the Ultima site.

Document any CDN-hosted dependencies such as Mermaid, KaTeX, or MiniSearch.

If fully offline behavior is required, vendor pinned versions in a separate bounded task. Do not claim complete offline support while essential behavior depends on a CDN.

Core prose, code, navigation, and hyperlinks must remain readable when optional scripts fail.

## 15. Phase 8: Chapter 8 proof of experience

Use Chapter 8, “Game play,” as the first real acceptance scenario.

Confirm that a reader can:

- read its prose and code in source order;
- inspect `MOVE_PLAYER` relationships;
- inspect `HANDLE_TIMERS` relationships;
- follow `ENABLE_NEXT_LEVEL_LADDERS` to relevant initialization;
- reach the Chapter 10 game loop;
- reach Chapter 9 guard behavior;
- traverse continued chunks;
- inspect identifier definitions and uses;
- return to the original reading position without manual recovery.

Compare the experience with:

- `main.pdf`;
- editor search in the upstream `main.nw`;
- current or baseline `nwtool.py` output.

Exercise actual navigation paths and record whether each target resolves correctly. Record shortcomings before adding more infrastructure.

## 16. Phase 9: site acceptance and documentation

The generated site must:

- be static;
- use relative internal links;
- use explicit `.html` filenames when multi-page;
- open through `file://` where practical;
- work when served locally;
- preserve navigation across pages;
- provide deterministic index and search data;
- avoid committing generated output unless repository policy requires it.

Document:

- the site build command;
- Python dependencies;
- optional CDN dependencies;
- structural and tangle test commands;
- how `nwtool.py` selects the maintained source;
- how to compare the Markdown fork with the upstream source;
- generated-output paths and commit policy;
- provenance, attribution, and licensing.

Provide one documented build command following repository conventions, for example:

```text
python3 scripts/weave_html.py research/lode_runner/main.nw build/lode-runner-docs
```

## 17. Testing strategy

### 17.1 Migration tests

Verify:

- code-chunk headers and bodies under canonical LF comparison;
- code-chunk count, order, and names;
- continuation chains;
- references and backlinks;
- `%def` declarations and identifier relationships;
- no newly unresolved chunk reference;
- no documentation chunk lost through parser mistakes;
- byte-for-byte equality of upstream and migrated tangles.

### 17.2 Parser parity tests

Verify:

- the Markdown source produces the expected structural model;
- rich Lode Runner chunk names parse correctly;
- multiline and unusual `[[...]]` forms survive;
- documentation headings do not create false code chunks;
- code resembling Markdown or LaTeX remains code;
- repeated identifier definitions remain represented;
- continuation relationships remain stable;
- malformed source produces actionable diagnostics.

### 17.3 `nwtool.py` tests

Verify:

- Chapter 8 extraction;
- chunk lookup;
- continuation output;
- identifier lookup;
- repeated identifier definitions;
- index output;
- default and explicit source selection;
- bounded, context-efficient output;
- useful diagnostics for unknown queries.

### 17.4 HTML tests

Verify with focused assertions or an HTML parser:

- intended chapter/page files exist;
- chunk anchors are valid;
- chunk-reference links resolve;
- continuation links resolve;
- identifier links resolve;
- index links resolve;
- cross-page prose references resolve;
- required local assets are emitted;
- search metadata contains chapters, chunks, and identifiers;
- filenames and output are deterministic;
- source text is escaped correctly;
- raw HTML from Markdown is intentional.

Browser-driven visual tests are optional initially.

Tests should protect source structure and research behavior, not only rendered appearance. Large snapshots may supplement focused assertions but must not become the sole oracle.

## 18. Commit discipline

Prefer small, conceptually isolated commits:

1. structural oracle and goldens;
2. shared source-model interface;
3. migration script or wrapper;
4. raw mechanical Markdown adaptation;
5. manual Markdown cleanup batches;
6. `nwtool.py` retrofit;
7. basic HTML renderer;
8. navigation and references;
9. search, previews, and polish;
10. documentation and backlog cleanup.

Run structural parity and tangle equality tests after every commit that touches:

- the maintained `main.nw`;
- chunk parsing;
- conversion;
- graph analysis.

The Phase 1 upstream tangle SHA-256 was:

```text
be29dc257afe75605e0e3a5a0ddd6d311a2c7a7299bd3634c7a126c972f093a1
```

Prefer comparing freshly generated upstream and migrated tangles rather than relying only on the recorded digest.

Do not combine assembly edits with format migration.

Where repository workflow permits, do not combine raw converter output and extensive manual cleanup into one unreviewable commit.

## 19. Model handoff guidance

Phase 1 is complete. Do not repeat its broad LaTeX-surface investigation unless new evidence contradicts the report.

Use the strongest available reasoning model for:

- Phase 2 structural-oracle design and interpretation;
- the Phase 3 parser decision if it remains ambiguous;
- structural-parity failures whose causes are not mechanical.

Later implementation phases may be performed one bounded step at a time after the manifest, invariants, and shared source-model contract are established.

Each implementation session should:

1. read this file and the latest phase report;
2. work on one bounded phase or subphase;
3. run the prescribed tests;
4. record decisions and update relevant artifacts;
5. stop when a consultation condition occurs;
6. avoid unrelated opportunistic refactoring.

Communicate progress constructively. Clearly name what was accomplished, keep the next step approachable, and do not present every possible improvement as a prerequisite. This is a long-running private research project: rigor should support momentum rather than extinguish it.

## 20. Stop and consult conditions

Stop and report findings rather than guessing if:

- upstream licensing for code about to be copied remains unclear;
- an actual Lode Runner chunk name cannot be represented;
- converter output changes code after canonical LF normalization;
- upstream and migrated tangles differ;
- old and new graph results disagree without a clear explanation;
- structural parity passes only by ignoring a meaningful relationship;
- an unknown repeated construct carries semantic content;
- adapting the HTML weaver would discard existing relationship data;
- the project-owned source path conflicts with repository conventions;
- `nwtool.py` relies on undocumented parser behavior;
- identifier relationships are more ambiguous than the proposed model can represent;
- a shortcut would make generated Markdown authoritative again;
- actual source behavior requires a materially different architecture.

Do not stop merely because conversion encounters one of the bounded Phase 1 exceptions. Those are expected cleanup work.

A stop report should include:

- the exact source location or failing test;
- expected and actual behavior;
- the smallest known reproduction;
- alternatives considered;
- a recommended decision.

## 21. Definition of done

This action plan is complete when:

1. The original upstream LaTeX source remains untouched.
2. A reviewed project-owned Markdown `main.nw` exists.
3. Code chunks and literate relationships pass structural parity tests under the canonical LF policy.
4. Upstream and migrated tangles are byte-identical.
5. All known Phase 1 conversion exceptions are resolved or explicitly deferred without impairing research use.
6. One `nwtool.py` operates on the Markdown source.
7. A static HTML site is generated from the same source and graph model.
8. Chapter 8 provides clearly better cross-reference navigation than the PDF.
9. Build, testing, provenance, attribution, and licensing are documented.
10. Remaining enhancements are ordinary backlog items rather than migration blockers.
