# Phase 1: Lode Runner converter review

**Date:** September 7, 2026  
**Status:** Complete  
**Source:** `reference/lode_runner_reveng/main.nw`

## Purpose

Phase 1 measured the LaTeX and Noweb surface relevant to converting the upstream Lode Runner document to a project-owned Markdown/Noweb source.

The supplied Ultima `latex_to_md.py` was tested as a practical starting point rather than assuming that it was compatible with Lode Runner.

No upstream source was modified.

## Experiment setup

The converter normally imports `Weaver` from the Ultima `weave.py`. That parser restricts chunk names to letters, digits, spaces, hyphens, underscores, periods, and similar simple characters.

Lode Runner has richer chunk names containing constructs such as:

- `[[quoted code]]`;
- operators;
- parentheses;
- additional punctuation.

For the experiment, a disposable copy of `latex_to_md.py` was placed beside the Lode Runner `weave.py`. This allowed the existing import:

    from weave import Weaver

to resolve to the Lode Runner parser without modifying either upstream implementation.

This was sufficient because the converter only depends on the parser to distinguish documentation chunks from code chunks and to provide their source ranges.

The converted file was written under `tmp/experiment/`.

## Main result

The converter produced a useful Markdown adaptation while preserving the code structure well enough to produce an identical tangle.

The original and converted sources were tangled with the Lode Runner `weave.py`. The results were byte-identical:

    Tangles are identical
    be29dc257afe75605e0e3a5a0ddd6d311a2c7a7299bd3634c7a126c972f093a1  tmp/literate-migration/original.asm
    be29dc257afe75605e0e3a5a0ddd6d311a2c7a7299bd3634c7a126c972f093a1  tmp/literate-migration/converted.asm

This is strong evidence that the converter preserved the code used by tangling.

It is not a substitute for the Phase 2 structural manifest. Phase 2 must still compare individual code-chunk headers and bodies, continuations, references, and identifier declarations.

## Documentation and code separation

The existing Lode Runner parser successfully distinguishes documentation chunks from code chunks.

The converter applies Markdown transformations only to documentation and copies code-chunk headers and bodies as text. It is therefore not necessary to build a separate documentation-chunk scanner before proceeding.

The initial documentation before the first represented chunk is also converted.

## Constructs converted successfully

Inspection of the generated Markdown found that the converter successfully handled the main prose structure, including:

- ordinary chapters not located on a Noweb marker line;
- sections;
- paragraphs;
- ordinary inline formatting;
- ordinary inline `[[...]]` quoted code;
- lists;
- ordinary prose punctuation;
- removal of simple presentation environments such as `center`;
- preservation of code-chunk headers and bodies;
- preservation of `@ %def` markers.

The original source's physical prose wrapping remains in the generated Markdown. This is acceptable because Markdown renders consecutive nonblank lines as one paragraph.

## Constructs requiring project-specific or manual conversion

### Chapter title on a documentation marker

The source contains:

    @ \chapter{Lode Runner}

This is valid Noweb. A documentation marker may contain the first documentation text on the same line.

The converter copies documentation marker lines without applying its LaTeX transformations to their content. The generated result therefore contains both an invented heading and the unconverted source line:

    # Document

    @ \chapter{Lode Runner}

The initial Markdown adaptation should replace this with:

    @
    # Lode Runner

This is a converter limitation, not an error in the upstream source.

The scan of documentation markers found no other ordinary prose on an `@` marker line. The remaining marker lines containing text are `@ %def` declarations and must remain Noweb metadata.

### Standalone images

Seven standalone image commands remain:

- converted line 11: `title-screen`;
- converted line 27: `screen`;
- converted line 1370: `screen`;
- converted line 2764: `iris`;
- converted line 5134: `read_joystick_for_command`;
- converted line 5720: `digging`;
- converted line 8843: `lode_runner_game_loop`.

The converter handles figures in some recognized structures but does not convert these standalone `\includegraphics` commands after removing their surrounding `center` environments.

These should be converted to Markdown image syntax with paths appropriate to the final project-owned source location. Width or height information should be preserved with intentional Markdown-compatible HTML where it materially affects readability.

### Tables

Five table areas remain near the beginning of the converted document:

1. an inline color table at converted line 172;
2. a byte, bit, and pixel-data table at converted lines 180-193;
3. a colored pixel grid at converted lines 204-216;
4. a second byte, bit, and pixel-data table at converted lines 225-238;
5. a second colored pixel grid at converted lines 245-257.

The first table was flattened into a single Markdown list item containing raw LaTeX commands and `<br>` elements. The remaining tables retain substantial raw LaTeX.

The ordinary data tables are candidates for Markdown pipe tables or semantic HTML tables.

The colored pixel grids depend on the custom commands `\bk0`, `\bl0`, `\bw0`, and `\bo0`. They require a project-specific representation, likely semantic HTML tables with CSS classes or an intentionally generated image.

The converter does not reliably isolate tables nested inside other documentation structures. This is a real gap, but the affected source is bounded and suitable for manual conversion.

### External table input

Converted line 275 retains:

    \input{sprite_tables.tex}

The referenced file and its role must be inspected before migration. Its content must either be incorporated into the maintained Markdown source, converted into a suitable Markdown or HTML representation, or preserved as an explicitly documented external dependency.

### TikZ diagrams

Two TikZ diagrams remain:

- converted lines 324-346;
- converted lines 396-416.

These require manual treatment. Options for the later migration phase are:

1. preserve rendered images;
2. convert them to Mermaid if Mermaid can express the relationships clearly;
3. use semantic HTML and CSS;
4. preserve fenced LaTeX temporarily with an explicit migration TODO.

The choice should prioritize research clarity rather than visual parity with the PDF.

### Layout commands

Two `\vspace{1em}` commands remain at converted lines 320 and 349.

These are presentation-only commands and can be removed during Markdown cleanup unless inspection shows that an explicit section break is needed.

### Generated Noweb indexes

The converted tail retains:

    \chapter{Defined Chunks}
    \nowebchunks
    \chapter{Index}
    \nowebindex

These commands request indexes generated by the LaTeX/Noweb toolchain. They should not be converted into maintained Markdown content.

The future HTML weaver will generate chunk and identifier indexes from the shared source model. These source commands can be omitted from the project-owned Markdown adaptation after structural checks confirm that they are documentation-only output directives.

## Multiline quoted code

The source contains one multiline `[[...]]` quoted-code span at original lines 9768-9785:

    [[
    QU $1C35
    ytable EQU $1C51
    bytable EQU $1C62
    bitable EQU $1C7E
    xbytable EQU $1C9A
    xbitable EQU $1D26
    boot EQU $1DB2
    scorebuf EQU $1F00
    chardata EQU $AD00

    rwtsparm EQU $B7E8
    rwtsvolm EQU $B7EB
    rwtstrck EQU $B7EC
    rwtssect EQU $B7ED
    rwtsbuff EQU $B7F0
    rwtscmn
    ]]

The PDF confirms that this is intentional Noweb quoted code rather than garbled source.

The converter only protects `[[...]]` when both delimiters occur in the same string being transformed. It does not carry quoted-code state across lines.

Dollar signs in the quoted assembly are consequently mistaken for inline-math delimiters. The converter joins pairs of physical lines while searching for closing dollar signs. The generated output becomes:

    [[
    QU $1C35 ytable EQU $1C51
    bytable EQU $1C62 bitable EQU $1C7E
    xbytable EQU $1C9A xbitable EQU $1D26
    boot EQU $1DB2 scorebuf EQU $1F00
    chardata EQU $AD00

    rwtsparm EQU $B7E8 rwtsvolm EQU $B7EB
    rwtstrck EQU $B7EC rwtssect EQU $B7ED
    rwtsbuff EQU $B7F0 rwtscmn ]]

This is a documentation conversion error.

The Markdown adaptation should preserve the original line structure and replace the outer Noweb quotation delimiters with a fenced code block or another representation supported by the HTML weaver.

If the converter is retained as a reproducible migration tool, it should eventually protect multiline quoted-code spans before processing inline mathematics.

## Mathematics

The source contains none of the following display-math forms:

- `$$...$$`;
- `\[...\]`;
- `equation` environments;
- `align` environments;
- `gather` environments;
- `multline` environments;
- `eqnarray` environments.

Display-math conversion is therefore not required for the initial Lode Runner migration.

Ordinary dollar signs inside multiline quoted code must still be protected from the converter's inline-math handling.

## Remaining-command scan

A scan of converted documentation found the bounded constructs listed in this report.

A less restricted scan also reported assembly comments containing sequences such as `\r`. Those are false positives caused by the scan's documentation/code state handling and are not remaining LaTeX commands in prose.

The useful scan must distinguish documentation from code using the Lode Runner parser or equivalent Noweb-aware logic. A plain whole-file search for backslash commands is not sufficient because assembly strings and comments may legitimately contain backslashes.

Unknown meaningful LaTeX commands should be reported rather than silently discarded by the final migration process.

## Line-ending policy

The upstream working copy was observed as CRLF in Notepad++, but the repository's `.gitattributes` declares LF for all detected text:

    * text=auto eol=lf

Git reports the relevant attributes for the upstream source as:

    reference/lode_runner_reveng/main.nw: text: auto
    reference/lode_runner_reveng/main.nw: eol: lf

The converter reads decoded text, removes line terminators, and writes output joined with LF. It therefore preserves code line content but does not preserve the upstream working copy's CRLF bytes.

The project-owned Markdown source should follow the repository's authoritative LF policy.

Phase 2 should define exact code comparison using canonical LF line endings. It should compare every code header and body after normalizing only line endings. No other whitespace or content normalization should be allowed.

The untouched upstream reference file should not be edited merely to normalize its current working-tree line endings.

## Classification summary

| Construct | Observed result | Treatment |
|---|---|---|
| Ordinary chapters and sections | Converted | Mechanical |
| Chapter on `@` marker | Left as LaTeX | Project-specific rule or manual correction |
| Ordinary paragraphs | Converted | Mechanical |
| Ordinary inline formatting | Converted | Mechanical |
| Single-line `[[...]]` quotations | Preserved | Mechanical |
| Multiline `[[...]]` quotation | Line structure corrupted | Manual correction and later converter rule |
| Lists | Generally converted | Mechanical, with table-containing item review |
| Standalone images | Left as LaTeX | Manual or project-specific rule |
| Ordinary tables | Left raw or flattened | Manual conversion |
| Colored pixel tables | Left raw | Project-specific representation |
| `sprite_tables.tex` input | Left raw | Investigate and convert explicitly |
| TikZ diagrams | Left raw | Manual conversion or rendered image |
| Layout spacing | Left raw | Remove unless semantically useful |
| Inline math | No general problem observed | Protect quoted assembly dollar signs |
| Display math | Not present | No initial support required |
| Noweb-generated indexes | Left raw | Remove from maintained prose; generate in HTML |
| Code chunks | Preserved well enough for identical tangle | Verify structurally in Phase 2 |
| `@ %def` declarations | Preserved | Verify structurally in Phase 2 |

## Recommendation

Use the supplied `latex_to_md.py` as the basis for the one-time Lode Runner migration, with the Lode Runner parser supplying chunk boundaries.

Do not build a separate broad LaTeX inventory system before migration. The experiment has reduced the remaining conversion surface to a small, reviewable set of constructs.

The migration approach should be:

1. run the converter into a new project-owned destination;
2. correct the bounded documentation issues identified in this report;
3. preserve code chunks unchanged;
4. validate the result against the Phase 2 structural oracle;
5. retain the converter as a historical and diagnostic tool rather than running it during normal HTML builds.

Do not modify the upstream `reference/lode_runner_reveng/main.nw`.

## Phase 2 handoff

Phase 2 should now freeze the structural oracle before the project-owned Markdown source is created or manually cleaned.

The structural manifest must independently verify:

- exact code-chunk order;
- exact chunk names;
- exact headers;
- exact bodies after canonical LF normalization;
- continuation chains;
- outgoing and incoming chunk references;
- `@ %def` declarations;
- identifier definitions and detected uses;
- unresolved references;
- duplicate and ambiguous definitions;
- chapter boundaries.

The identical tangle is useful supporting evidence, but it must not be the only migration oracle.
