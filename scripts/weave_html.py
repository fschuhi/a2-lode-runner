"""HTML weaver for the literate noweb source (prototype).

***********************************************************************************
NOTE: Adapted from `weave_html.py` in XekriRedmane's `ultima1_reveng`
(see `scripts/PROVENANCE.md`). Here we import from `weave_lode_runner`
instead of the Ultima `weave.py`.
The call to `self.weaver.tangle` is commented out because we cannot use the older
`weave_lode_runner` from this newer (Ultima1-related) caller. This is not a
problem because we don't need a tangle in this project; we are just interested
in the woven html output.
***********************************************************************************

This is the new weave backend described in `html-migration-design.md` in the
upstream `ultima1_reveng` repository. It REUSES
weave.py's tangler and chunk-graph analysis unchanged (the byte-perfect path)
and replaces only the output backend: instead of emitting LaTeX, it emits a
multi-page, three-pane, searchable HTML site.

Pipeline per source file:
  1. weave.Weaver.extract_chunk_info()  -> the chunk graph (UNCHANGED)
  2. weave.Weaver.tangle()              -> byte-perfect .asm (UNCHANGED)
  3. build_layout()  -> assign every chunk + heading to a page, build the
                        sublabel/name/ident -> (page, anchor) resolver maps
  4. render          -> Markdown (mistune) for doc chunks, a one-pass 6502
                        tokenizer + identifier links for code chunks
  5. emit            -> one HTML file per page + chunk/identifier index pages,
                        plus assets/ (style.css, app.js, site-data.js, .nojekyll)

Prose authoring rules the weaver assumes (see design doc):
  - Markdown (CommonMark + pipe tables + fenced ```mermaid).
  - Inline math stays as $...$ (rendered to \\( \\) for KaTeX).
  - [[X]] links: chunk name -> chunk; @ %def symbol -> its definition;
    anything else (raw $XXXX, undefined symbol) -> styled, no link.
  - A page starts at every H1 and at every explicit page marker:
        <!-- nwpage: slug | Page Title -->
    Page-breaking constructs must begin a doc-chunk line (not inside a fence).
"""

import html
import pathlib
import re
import shutil
from typing import Sequence

from absl import app

from weave_lode_runner import Weaver, ChunkInfo


# --- 6502 / dasm token tables (for syntax highlighting) ---------------------
MNEMONICS = set(
    "LDA LDX LDY STA STX STY TAX TAY TXA TYA TSX TXS ADC SBC AND ORA EOR CMP "
    "CPX CPY INC INX INY DEC DEX DEY ASL LSR ROL ROR BIT JMP JSR RTS RTI BRK "
    "NOP CLC SEC CLI SEI CLV CLD SED BCC BCS BEQ BNE BMI BPL BVC BVS PHA PLA "
    "PHP PLP".split()
)
DIRECTIVES = set(
    "PROCESSOR ORG SUBROUTINE EQU EQM DC DV HEX BYTE WORD MAC ENDM MACRO SEG "
    "RORG REND ALIGN DS INCLUDE INCBIN INCDIR IF ELSE ENDIF EIF REPEAT REPEND "
    "ECHO ERR SET SUBROUTINE LIST PROCESSOR".split()
)

# Page marker:  <!-- nwpage: slug | Title -->
PAGE_MARKER = re.compile(r"^\s*<!--\s*nwpage:\s*([-\w]+)\s*\|\s*(.+?)\s*-->\s*$")
ATX_HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
FENCE = re.compile(r"^\s*(```|~~~)")
# Cross-reference target:  <a id="ch:stuph"></a>
ANCHOR_TAG = re.compile(r'<a\s+id="([^"]+)"')
# Figure/table caption paragraph:  **Figure — ...**  /  **Table.** ...
CAPTION = re.compile(r"^\*\*(Figure|Table)\b")
# A rendered cross-reference, before its kind word has been folded in.
XREF_RAW = (r'<a class="xref" data-kind="(?P<kind>[^"]*)"'
            r' href="(?P<href>[^"]*)">(?P<num>[^<]*)</a>')
XREF_TAG = re.compile(XREF_RAW)
KIND_WORD = r"[Pp]arts?|[Cc]hapters?|[Ss]ubsections?|[Ss]ections?|[Ff]igures?|[Tt]ables?"
ABSORB_REF = re.compile(rf"(?P<word>\b(?:{KIND_WORD}))\s+{XREF_RAW}")
# "chapters 8-10": the second ref is the tail of a range, already introduced.
RANGE_TAIL = re.compile(r"</a>\s*[–—-]\s*$")
CHUNKREF = re.compile(r"<<([-._ 0-9A-Za-z]*)>>")
# Inline code token scanner for the code part of an assembly line.
TOKRE = re.compile(
    r"""(?P<str>"[^"]*"|'[^']*')
      | (?P<num>\#?\$[0-9A-Fa-f]+|\#?%[01]+|\#[0-9]+|\b[0-9]+\b)
      | (?P<id>\.?[A-Za-z_][A-Za-z0-9_]*)
      | (?P<ws>[ \t]+)
      | (?P<other>.)""",
    re.VERBOSE,
)

# Pinned CDN dependencies (viewing requires internet, per design 4.5).
CDN_MERMAID = "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"
CDN_KATEX_CSS = "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css"
CDN_KATEX_JS = "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"
CDN_KATEX_AUTO = (
    "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"
)
CDN_MINISEARCH = "https://cdn.jsdelivr.net/npm/minisearch@7.1.0/dist/umd/index.min.js"


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def slugify(text: str, used: set[str]) -> str:
    """Lowercase, dash-separated, unique-within-`used` slug."""
    # Strip a little markdown so slugs are clean.
    text = re.sub(r"\[\[(.+?)\]\]", r"\1", text)
    text = re.sub(r"[`*_]", "", text)
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    s = s or "section"
    base, n = s, 2
    while s in used:
        s = f"{base}-{n}"
        n += 1
    used.add(s)
    return s


def roman(n: int) -> str:
    """Uppercase Roman numeral (parts are numbered I, II, ... as in LaTeX)."""
    out = ""
    for value, sym in ((10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")):
        while n >= value:
            out += sym
            n -= value
    return out


def strip_md(text: str) -> str:
    """Cheap markdown -> plain text for TOC labels and search."""
    text = re.sub(r"\[\[(.+?)\]\]", r"\1", text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"[*_]{1,2}", "", text)
    return text.strip()


class Page:
    def __init__(self, slug: str, filename: str, title: str):
        self.slug = slug
        self.filename = filename
        self.title = title
        self.parts: list[str] = []        # rendered HTML fragments, in order
        self.headings: list[tuple[int, str, str]] = []  # (level, text, anchor)


class HtmlWeaver:
    def __init__(self):
        self.weaver = Weaver()
        self.md = None  # mistune instance, built once maps exist
        self.warned: set[str] = set()

    def warn(self, msg: str):
        """Report a source problem once (the renderer sees each page twice)."""
        if msg not in self.warned:
            self.warned.add(msg)
            print(f"warning: {msg}")

    # ---------------------------------------------------------------- layout
    def split_docchunk(self, lines: Sequence[str]):
        """Fence-aware split of a doc chunk into segments at page triggers.

        Yields (trigger, seg_lines) where trigger is None, ('h1', title) or
        ('marker', slug, title). The trigger line itself is NOT included in
        seg_lines for markers; for H1 it IS (the heading renders in content).
        """
        seg: list[str] = []
        trigger = None
        in_fence = False
        first = True
        for line in lines:
            if FENCE.match(line):
                in_fence = not in_fence
                seg.append(line)
                continue
            if not in_fence:
                m = PAGE_MARKER.match(line)
                if m:
                    if seg or not first:
                        yield (trigger, seg)
                    seg, trigger, first = [], ("marker", m.group(1), m.group(2)), False
                    continue
                h = ATX_HEADING.match(line)
                if h and len(h.group(1)) == 1:
                    if seg or not first:
                        yield (trigger, seg)
                    seg, trigger, first = [line], ("h1", h.group(2)), False
                    continue
            seg.append(line)
        yield (trigger, seg)

    def scan_headings(self, seg_lines: Sequence[str]):
        """Fence-aware list of (level, raw_text) headings in a segment."""
        out, in_fence = [], False
        for line in seg_lines:
            if FENCE.match(line):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            h = ATX_HEADING.match(line)
            if h:
                out.append((len(h.group(1)), h.group(2)))
        return out

    # -------------------------------------------------------------- numbering
    # The prose carries LaTeX-style bare cross-references, `[ch:stuph](#ch:stuph)`,
    # whose link text is meant to be the target's NUMBER (that is what \ref
    # expanded to). Numbering therefore happens here, in document order, and
    # every numbered target advertises its number: headings get "9." / "9.3",
    # figure and table captions get "Figure 2 — ...".
    @staticmethod
    def label_of_heading(seg, i):
        """The <a id="..."> that labels the heading at seg[i], if any.

        Blank lines may sit between the heading and its anchor; anything else
        ends the search (the heading is then unlabelled).
        """
        for line in seg[i + 1:]:
            if not line.strip():
                continue
            m = ANCHOR_TAG.search(line)
            return m.group(1) if m else None
        return None

    def number_heading(self, level, label):
        """Advance the sectioning counters for one heading; return its prefix.

        The prefix is what the heading displays ("Part I.", "9.", "9.3"); the
        bare number is what a `\\ref` to `label` resolves to.
        """
        if level == 1:
            if not self.doc_title_seen:  # the document title, not a chapter
                self.doc_title_seen = True
                return ""
            if label and label.startswith("part:"):
                num = roman(self.part_n + 1)
                self.part_n += 1
                kind, prefix = "Part", f"Part {num}."
            else:
                self.chapter_n += 1
                num = str(self.chapter_n)
                kind, prefix = "chapter", f"{num}."
            self.sec_n = self.sub_n = 0
        elif level == 2:
            self.sec_n += 1
            self.sub_n = 0
            kind = "section"
            num = prefix = f"{self.chapter_n}.{self.sec_n}"
        elif level == 3:
            self.sub_n += 1
            kind = "subsection"
            num = prefix = f"{self.chapter_n}.{self.sec_n}.{self.sub_n}"
        else:
            return ""
        if label:
            self.ref_number[label] = (kind, num)
        return prefix

    def number_caption(self, kind, line):
        """Number one figure/table caption and bind the anchor that precedes it."""
        if kind == "Figure":
            self.fig_n += 1
            n = self.fig_n
        else:
            self.tab_n += 1
            n = self.tab_n
        prefix = kind.lower()[:3] + ":"          # "fig:" / "tab:"
        for i, label in enumerate(self.pending_media):
            if label.startswith(prefix):
                self.ref_number[self.pending_media.pop(i)] = (kind, str(n))
                break
        return CAPTION.sub(f"**{kind} {n}", line, count=1)

    def number_segment(self, seg):
        """Number one doc segment: headings, `\\label` anchors, captions.

        Returns (lines, head_nums): the segment with numbers spliced into its
        captions, and the display prefix of each heading in order (parallel to
        scan_headings, so the renderer can pair them up).
        """
        out, head_nums = [], []
        in_fence = False
        for i, line in enumerate(seg):
            if FENCE.match(line):
                in_fence = not in_fence
            elif not in_fence:
                h = ATX_HEADING.match(line)
                if h:
                    head_nums.append(
                        self.number_heading(len(h.group(1)),
                                            self.label_of_heading(seg, i)))
                    out.append(line)
                    continue
                a = ANCHOR_TAG.search(line)
                if a and a.group(1).startswith(("fig:", "tab:")):
                    # Bound to the next caption of its kind, which is where the
                    # counter actually advances.
                    self.pending_media.append(a.group(1))
                    out.append(line)
                    continue
                c = CAPTION.match(line)
                if c:
                    line = self.number_caption(c.group(1), line)
            out.append(line)
        return out, head_nums

    def build_layout(self, lines, chunks):
        """Pass 1: assign chunks/headings to pages; build resolver maps."""
        self.ref_number: dict[str, str] = {}   # \label id -> displayed number
        self.pending_media: list[str] = []     # fig:/tab: labels awaiting a caption
        self.doc_title_seen = False
        self.part_n = self.chapter_n = self.sec_n = self.sub_n = 0
        self.fig_n = self.tab_n = 0
        self.pages: list[Page] = []
        self.units: list[tuple] = []          # ('doc', page_idx, seg, anchors) | ('code', page_idx, chunk)
        self.label_loc: dict[str, tuple[str, str]] = {}  # \label id -> (page, anchor)
        page_slugs: set[str] = set()
        anchor_slugs: set[str] = set()
        cur = None  # current Page index

        def new_page(slug, title):
            filename = "index.html" if not self.pages else f"{slug}.html"
            self.pages.append(Page(slug, filename, title))
            return len(self.pages) - 1

        sublabel_loc: dict[str, tuple[str, str]] = {}
        label_loc: dict[str, tuple[str, str]] = {}

        def process_doc(seg_lines):
            nonlocal cur
            for trig, seg in self.split_docchunk(seg_lines):
                titled = False
                if trig and trig[0] == "h1":
                    cur = new_page(slugify(trig[1], page_slugs), strip_md(trig[1]))
                    titled = True
                elif trig and trig[0] == "marker":
                    cur = new_page(slugify(trig[1], page_slugs), trig[2])
                if cur is None:  # content before the first trigger
                    cur = new_page(slugify("home", page_slugs), "Home")
                seg, head_nums = self.number_segment(seg)
                anchors = []
                for (level, text), num in zip(self.scan_headings(seg), head_nums):
                    a = slugify(text, anchor_slugs)  # slugs stay number-free
                    anchors.append(a)
                    title = strip_md(text)
                    self.pages[cur].headings.append(
                        (level, f"{num} {title}" if num else title, a))
                # A page opened by a numbered chapter/part heading carries the
                # number in its nav entry and <title> too.
                if titled and head_nums and head_nums[0]:
                    self.pages[cur].title = f"{head_nums[0]} {self.pages[cur].title}"
                # Record \label-derived anchors for site-wide cross-page refs.
                for mm in ANCHOR_TAG.finditer("\n".join(seg)):
                    self.label_loc.setdefault(
                        mm.group(1), (self.pages[cur].filename, mm.group(1)))
                self.units.append(("doc", cur, seg, anchors, head_nums))

        # The prose before the first chunk is NOT in `chunks` (weave.py treats
        # it as an unrepresented leading doc chunk) -- process it explicitly.
        lead_end = chunks[0].start if chunks else len(lines)
        if lead_end > 0:
            process_doc(lines[:lead_end])

        for chunk in chunks:
            if chunk.kind == "doc":
                process_doc(lines[chunk.start + 1 : chunk.end])
            else:  # code chunk
                if cur is None:
                    cur = new_page(slugify("home", page_slugs), "Home")
                fn = self.pages[cur].filename
                sublabel_loc[chunk.sublabel] = (fn, chunk.sublabel)
                if chunk.sublabel == chunk.label:
                    label_loc[chunk.label] = (fn, chunk.label)
                self.units.append(("code", cur, chunk))

        # Resolver maps.
        self.sublabel_loc = sublabel_loc
        self.sublabel_to_chunk = {c.sublabel: c for c in chunks if c.name}
        name_to_label = {c.name: c.label for c in chunks if c.name}
        self.name_loc = {n: label_loc[l] for n, l in name_to_label.items() if l in label_loc}
        # An identifier can be defined by several chunks, because each assembly target
        # redeclares the soft switches and ROM entries it uses. Keep every location so
        # a reference can resolve to the definition on its own page.
        ident_chunks: dict[str, list[ChunkInfo]] = {}
        for c in chunks:
            for ident in c.defines:
                ident_chunks.setdefault(ident, []).append(c)
        self.ident_to_chunk = {i: cs[0] for i, cs in ident_chunks.items()}
        self.ident_locs = {}
        for i, cs in ident_chunks.items():
            locs = [sublabel_loc[c.sublabel] for c in cs if c.sublabel in sublabel_loc]
            if locs:
                self.ident_locs[i] = locs
        self.ident_loc = {i: locs[0] for i, locs in self.ident_locs.items()}
        for label in self.pending_media:
            self.warn(f"anchor #{label} has no following Figure/Table caption")

    # ---------------------------------------------------------- mistune setup
    def build_md(self):
        import mistune

        weaver = self

        def plugin_refs(md):
            LINKREF = r"\[\[(?P<lr>.+?)\]\]"
            MATH = r"(?<!\$)\$(?!\$)(?P<mx>[^\$\n]+?)\$(?!\$)"

            def parse_lr(inline, m, state):
                state.append_token({"type": "linkref", "raw": m.group("lr")})
                return m.end()

            def parse_mx(inline, m, state):
                state.append_token({"type": "mathx", "raw": m.group("mx")})
                return m.end()

            md.inline.register("linkref", LINKREF, parse_lr, before="link")
            md.inline.register("mathx", MATH, parse_mx, before="emphasis")

        class R(mistune.HTMLRenderer):
            cur_page = "index.html"
            head_q: list[str] = []
            num_q: list[str] = []
            head_i = 0

            def _href(self, loc):
                fn, anchor = loc
                return f"#{anchor}" if fn == self.cur_page else f"{fn}#{anchor}"

            def linkref(self, body):
                name = body.strip()
                if name in weaver.name_loc:
                    loc = weaver.name_loc[name]
                    return (f'<a class="ref chunkref" href="{self._href(loc)}" '
                            f'data-pop="{loc[1]}">&#x27E8;{esc(name)}&#x27E9;</a>')
                if name in weaver.ident_locs:
                    loc = weaver.pick_ident_loc(name, self.cur_page)
                    return (f'<a class="ref symref" href="{self._href(loc)}" '
                            f'data-pop="{loc[1]}"><code>{esc(name)}</code></a>')
                return f'<code class="addr">{esc(name)}</code>'

            def mathx(self, body):
                return f'<span class="math">\\({esc(body)}\\)</span>'

            def link(self, text, url, title=None):
                cls = ""
                if url.startswith("#"):
                    label = url[1:]
                    # `[ch:stuph](#ch:stuph)` is a bare \ref: the link text is
                    # the label itself, so it stands for the target's number.
                    # A ref the author gave real link text keeps that text.
                    if text.strip() == label:
                        ref = weaver.ref_number.get(label)
                        if ref:
                            # The kind word is folded in after rendering, once
                            # the surrounding prose is visible (absorb_kind_words).
                            kind, text = ref[0], esc(ref[1])
                            cls = f' class="xref" data-kind="{esc(kind)}"'
                        else:
                            weaver.warn(f"no number for reference #{label}")
                    # Resolve a same-page #label that actually lives on another
                    # page (cross-page \ref targets).
                    loc = weaver.label_loc.get(label)
                    if loc and loc[0] != self.cur_page:
                        url = f"{loc[0]}#{loc[1]}"
                t = f' title="{esc(title)}"' if title else ""
                return f'<a{cls} href="{esc(url)}"{t}>{text}</a>'

            def block_code(self, code, info=None):
                if (info or "").strip() == "mermaid":
                    return f'<div class="mermaid">{esc(code)}</div>\n'
                return f'<pre class="verbatim"><code>{esc(code)}</code></pre>\n'

            def block_html(self, html):
                # Author raw-HTML blocks (e.g. layout-figure tables) are passed
                # through verbatim, so mistune's inline rules never see them.
                # Resolve [[ ]] refs here so layout cells can link to symbols.
                return re.sub(r"\[\[(.+?)\]\]",
                              lambda m: self.linkref(m.group(1)), html) + "\n"

            def heading(self, text, level, **attrs):
                i = self.head_i
                self.head_i += 1
                anchor = self.head_q[i] if i < len(self.head_q) else ""
                num = self.num_q[i] if i < len(self.num_q) else ""
                idattr = f' id="{anchor}"' if anchor else ""
                secnum = f'<span class="secnum">{esc(num)}</span> ' if num else ""
                link = (f'<a class="hlink" href="#{anchor}">#</a>' if anchor else "")
                return f"<h{level}{idattr}>{secnum}{text}{link}</h{level}>\n"

        # escape=False is required on the renderer instance: when a custom
        # renderer is passed, create_markdown's own escape flag is ignored, so
        # raw HTML blocks/inlines would otherwise be escaped.
        self._renderer = R(escape=False)
        self.md = mistune.create_markdown(
            renderer=self._renderer, plugins=["table", plugin_refs]
        )

    # ----------------------------------------------------------- code chunks
    def render_code_line(self, line: str) -> str:
        """One assembly line -> highlighted HTML with identifier/chunk links."""
        # Split trailing comment at the first ';' (outside strings — approx).
        code, comment = line, ""
        in_str = False
        for i, ch in enumerate(line):
            if ch in "\"'":
                in_str = not in_str
            elif ch == ";" and not in_str:
                code, comment = line[:i], line[i:]
                break

        out = []
        # Leading label:  LABEL:  or  .local:
        mlbl = re.match(r"^(\.?[A-Za-z_][\w]*)(:)", code)
        rest = code
        if mlbl:
            out.append(f'<span class="lbl">{esc(mlbl.group(1))}</span>'
                       f'<span class="pun">:</span>')
            rest = code[mlbl.end():]

        # Process chunk refs interspersed with tokenizable text.
        pos = 0
        for m in CHUNKREF.finditer(rest):
            out.append(self.tokenize(rest[pos:m.start()]))
            name = m.group(1).strip()
            if name in self.name_loc:
                loc = self.name_loc[name]
                href = (f"#{loc[1]}" if loc[0] == self._renderer.cur_page
                        else f"{loc[0]}#{loc[1]}")
                out.append(f'<a class="chunkref" href="{href}" data-pop="{loc[1]}">'
                           f'&#x27E8;{esc(name)}&#x27E9;</a>')
            else:
                out.append(f'<span class="chunkref">&#x27E8;{esc(name)}&#x27E9;</span>')
            pos = m.end()
        out.append(self.tokenize(rest[pos:]))

        if comment:
            out.append(f'<span class="cm">{esc(comment)}</span>')
        return "".join(out)

    def tokenize(self, text: str) -> str:
        out = []
        for m in TOKRE.finditer(text):
            kind = m.lastgroup
            tok = m.group()
            if kind == "ws":
                out.append(tok)
            elif kind == "str":
                out.append(f'<span class="str">{esc(tok)}</span>')
            elif kind == "num":
                out.append(f'<span class="num">{esc(tok)}</span>')
            elif kind == "id":
                out.append(self.id_token(tok))
            else:
                out.append(f'<span class="pun">{esc(tok)}</span>')
        return "".join(out)

    def pick_ident_loc(self, ident, page):
        """The definition of `ident` on `page` if there is one, else the first."""
        locs = self.ident_locs[ident]
        return next((l for l in locs if l[0] == page), locs[0])

    def id_token(self, tok: str) -> str:
        if tok in self.ident_locs:
            loc = self.pick_ident_loc(tok, self._renderer.cur_page)
            href = (f"#{loc[1]}" if loc[0] == self._renderer.cur_page
                    else f"{loc[0]}#{loc[1]}")
            return (f'<a class="idlink" href="{href}" data-pop="{loc[1]}">'
                    f'{esc(tok)}</a>')
        up = tok.upper()
        if up in MNEMONICS:
            return f'<span class="mn">{esc(tok)}</span>'
        if up in DIRECTIVES:
            return f'<span class="dir">{esc(tok)}</span>'
        return f'<span class="sym">{esc(tok)}</span>'

    def render_code_chunk(self, chunk: ChunkInfo, lines) -> str:
        body_lines = lines[chunk.start + 1 : chunk.end]
        cont = "+=" if chunk.prev_sublabel else "="
        nameref = ""
        if chunk.name in self.name_loc:
            loc = self.name_loc[chunk.name]
            href = (f"#{loc[1]}" if loc[0] == self._renderer.cur_page
                    else f"{loc[0]}#{loc[1]}")
            nameref = f' <a class="pageref" href="{href}">[{chunk.number}]</a>'

        code_html = "\n".join(self.render_code_line(l) for l in body_lines)

        # Footer: prev/next, used-in, Defines, Uses.
        foot = []
        nav = []
        if chunk.prev_sublabel and chunk.prev_sublabel in self.sublabel_loc:
            loc = self.sublabel_loc[chunk.prev_sublabel]
            nav.append(f'<a href="{self._loc_href(loc)}">&#x25C1; prev</a>')
        if chunk.next_sublabel and chunk.next_sublabel in self.sublabel_loc:
            loc = self.sublabel_loc[chunk.next_sublabel]
            nav.append(f'<a href="{self._loc_href(loc)}">next &#x25B7;</a>')
        if nav:
            foot.append('<div class="chunk-nav">' + " ".join(nav) + "</div>")

        if chunk.sublabels_used_in:
            used = []
            for sl in chunk.sublabels_used_in:
                if sl in self.sublabel_loc:
                    c2 = self.sublabel_to_chunk.get(sl)
                    label = esc(c2.name) if c2 else "chunk"
                    used.append(f'<a href="{self._loc_href(self.sublabel_loc[sl])}" '
                                f'data-pop="{sl}">&#x27E8;{label}&#x27E9;</a>')
            if used:
                foot.append('<div class="used-in">Used in ' + ", ".join(used) + "</div>")
        else:
            foot.append('<div class="used-in not-used">(root chunk &mdash; tangled to file)</div>')

        if chunk.defines:
            defs = ", ".join(f'<code>{esc(d)}</code>' for d in sorted(chunk.defines))
            foot.append(f'<div class="defines">Defines {defs}</div>')
        if chunk.defines_used:
            uses = []
            for d in sorted(chunk.defines_used):
                if d in self.ident_locs:
                    loc = self.pick_ident_loc(d, self._renderer.cur_page)
                    uses.append(f'<a href="{self._loc_href(loc)}" '
                                f'data-pop="{loc[1]}"><code>{esc(d)}</code></a>')
            if uses:
                foot.append('<div class="uses">Uses ' + ", ".join(uses) + "</div>")

        return (
            f'<section class="chunk" id="{chunk.sublabel}">'
            f'<div class="chunk-head">'
            f'<button class="collapse" title="collapse/expand"></button>'
            f'<span class="chunk-title">&#x27E8;{esc(chunk.name)}{nameref}&#x27E9;{cont}</span>'
            f'</div>'
            f'<div class="chunk-body"><pre class="asm">{code_html}</pre></div>'
            f'<div class="chunk-foot">' + "".join(foot) + "</div>"
            f"</section>\n"
        )

    # ------------------------------------------------------- reference wording
    @staticmethod
    def _xref(href, text):
        return f'<a class="xref" href="{href}">{text}</a>'

    def absorb_kind_words(self, html_text: str) -> str:
        """Fold the prose kind word into the reference link.

        A cross-reference renders as a number, and "chapter" or "Figure" is
        already sitting in front of it in the prose; the whole phrase should be
        the link, not the bare number. So the preceding word is pulled inside
        the link (keeping the author's spelling, singular or plural), and a
        reference with no word in front of it supplies its own. The exception
        is the tail of a range -- "chapters 8-10" -- which stays bare.
        """
        def fold(m):
            word, kind = m.group("word"), m.group("kind")
            if word.lower().rstrip("s") != kind.lower():
                self.warn(f'"{word}" introduces a reference to {kind} '
                          f'{m.group("num")}')
            return self._xref(m.group("href"), f'{word} {m.group("num")}')

        def introduce(m):
            if RANGE_TAIL.search(m.string[:m.start()]):
                return self._xref(m.group("href"), m.group("num"))
            return self._xref(m.group("href"),
                              f'{m.group("kind")} {m.group("num")}')

        return XREF_TAG.sub(introduce, ABSORB_REF.sub(fold, html_text))

    def _loc_href(self, loc):
        fn, anchor = loc
        return f"#{anchor}" if fn == self._renderer.cur_page else f"{fn}#{anchor}"

    # --------------------------------------------------------------- render
    def render(self, lines):
        search_docs = []
        chunk_meta = {}
        for unit in self.units:
            page = self.pages[unit[1]]
            self._renderer.cur_page = page.filename
            if unit[0] == "doc":
                _, _, seg, anchors, nums = unit
                self._renderer.head_q = anchors
                self._renderer.num_q = nums
                self._renderer.head_i = 0
                text = "\n".join(seg)
                if text.strip():
                    page.parts.append(self.absorb_kind_words(self.md(text)))
                # search docs per heading segment
                heads = self.scan_headings(seg)
                if heads and anchors:
                    page.parts  # no-op
                    title = strip_md(heads[0][1])
                    if nums and nums[0]:
                        title = f"{nums[0]} {title}"
                    search_docs.append({
                        "id": f"{page.filename}#{anchors[0]}",
                        "t": title, "u": f"{page.filename}#{anchors[0]}",
                        "k": "section", "b": strip_md(text)[:400],
                    })
            else:
                chunk = unit[2]
                page.parts.append(self.render_code_chunk(chunk, lines))
                body = lines[chunk.start + 1 : chunk.end]
                snippet = "\n".join(body[:6])
                chunk_meta[chunk.sublabel] = {
                    "n": chunk.name, "u": f"{page.filename}#{chunk.sublabel}",
                    "p": page.title, "s": snippet[:400],
                }
                search_docs.append({
                    "id": f"{page.filename}#{chunk.sublabel}",
                    "t": chunk.name, "u": f"{page.filename}#{chunk.sublabel}",
                    "k": "chunk", "b": "\n".join(body)[:400],
                })
                for d in chunk.defines:
                    search_docs.append({
                        "id": f"sym:{d}", "t": d,
                        "u": f"{page.filename}#{chunk.sublabel}",
                        "k": "symbol", "b": f"symbol {d}",
                    })
        self.search_docs = search_docs
        self.chunk_meta = chunk_meta

    # ------------------------------------------------------------- emit site
    def build_toc(self) -> str:
        out = ['<ul class="toc">']
        for p in self.pages:
            out.append(f'<li><a href="{p.filename}">{esc(p.title)}</a>')
            subs = [h for h in p.headings if h[0] == 2]
            if subs:
                out.append("<ul>")
                for _, text, anchor in subs:
                    out.append(f'<li><a href="{p.filename}#{anchor}">{esc(text)}</a></li>')
                out.append("</ul>")
            out.append("</li>")
        out.append("</ul>")
        # Extra index pages.
        out.append('<ul class="toc toc-aux">'
                   '<li><a href="chunk-index.html">Chunk index</a></li>'
                   '<li><a href="identifier-index.html">Identifier index</a></li>'
                   "</ul>")
        return "\n".join(out)

    def page_outline(self, page: Page) -> str:
        items = [h for h in page.headings if h[0] in (2, 3)]
        if not items:
            return ""
        out = ['<nav class="outline"><div class="outline-title">On this page</div><ul>']
        for level, text, anchor in items:
            out.append(f'<li class="lvl{level}"><a href="#{anchor}">{esc(text)}</a></li>')
        out.append("</ul></nav>")
        return "\n".join(out)

    def page_html(self, page: Page, doc_title: str) -> str:
        toc = self.build_toc()
        outline = self.page_outline(page)
        content = "\n".join(page.parts)
        return PAGE_TEMPLATE.format(
            title=esc(page.title), doc_title=esc(doc_title), toc=toc,
            outline=outline, content=content,
            mermaid=CDN_MERMAID, katex_css=CDN_KATEX_CSS, katex_js=CDN_KATEX_JS,
            katex_auto=CDN_KATEX_AUTO, minisearch=CDN_MINISEARCH,
        )

    def index_page(self, slug, title, doc_title, body_html) -> str:
        p = Page(slug, f"{slug}.html", title)
        p.parts.append(body_html)
        return self.page_html(p, doc_title)

    def chunk_index_html(self) -> str:
        names = sorted({c.name for c in self.chunks if c.name})
        rows = []
        for n in names:
            if n not in self.name_loc:
                continue
            loc = self.name_loc[n]
            rows.append(f'<li><a href="{loc[0]}#{loc[1]}">&#x27E8;{esc(n)}&#x27E9;</a></li>')
        return '<h1>Chunk index</h1><ul class="index-list">' + "".join(rows) + "</ul>"

    def ident_index_html(self) -> str:
        idents = sorted(self.ident_to_chunk)
        rows = []
        for i in idents:
            loc = self.ident_loc.get(i)
            if not loc:
                continue
            rows.append(f'<li><a href="{loc[0]}#{loc[1]}"><code>{esc(i)}</code></a></li>')
        return '<h1>Identifier index</h1><ul class="index-list">' + "".join(rows) + "</ul>"

    def site_data_js(self) -> str:
        import json
        return ("window.SEARCH_INDEX = " + json.dumps(self.search_docs) + ";\n"
                "window.CHUNK_META = " + json.dumps(self.chunk_meta) + ";\n")

    def weave(self, lines, chunks, output_dir, filename):
        self.chunks = chunks
        doc_title = self.pages[0].title if self.pages else "Document"
        outdir = pathlib.Path(output_dir)
        outdir.mkdir(parents=True, exist_ok=True)
        assets = outdir / "assets"
        assets.mkdir(exist_ok=True)

        for page in self.pages:
            (outdir / page.filename).write_text(self.page_html(page, doc_title))
        (outdir / "chunk-index.html").write_text(
            self.index_page("chunk-index", "Chunk index", doc_title, self.chunk_index_html()))
        (outdir / "identifier-index.html").write_text(
            self.index_page("identifier-index", "Identifier index", doc_title,
                            self.ident_index_html()))

        # Assets: copy static web/ files, generate data + .nojekyll.
        web = pathlib.Path(__file__).parent / "web"
        for fn in ("style.css", "app.js"):
            src = web / fn
            if src.exists():
                shutil.copy(src, assets / fn)
        (assets / "site-data.js").write_text(self.site_data_js())
        (outdir / ".nojekyll").write_text("")
        # Rendered image figures referenced by the prose live in images/.
        src_images = pathlib.Path("images")
        if src_images.exists():
            shutil.copytree(src_images, outdir / "images", dirs_exist_ok=True)
        # The porting sections point readers at the extracted asset tree, so
        # the published site carries it too. It lands under game-assets/
        # because assets/ above is already the site's own css and js.
        src_assets = pathlib.Path("assets")
        if src_assets.exists():
            shutil.copytree(src_assets, outdir / "game-assets",
                            dirs_exist_ok=True)

    # ------------------------------------------------------------------ run
    def run(self, files, output_dir):
        pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)
        for fileno, filename in enumerate(files):
            with open(filename) as f:
                lines = [l.rstrip("\n") for l in f.readlines()]
            chunks = self.weaver.extract_chunk_info(lines, filename, fileno)
            # 1) byte-perfect tangle (identical code path to weave.py)
            #self.weaver.tangle(lines, chunks, output_dir, filename)
            # 2) HTML weave
            self.build_layout(lines, chunks)
            self.build_md()
            self.render(lines)
            self.weave(lines, chunks, output_dir, filename)
            print(f"Wove {len(self.pages)} pages + 2 index pages from {filename}.")


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} &middot; {doc_title}</title>
<link rel="stylesheet" href="{katex_css}">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="topbar">
  <button id="menu-toggle" class="iconbtn" title="Menu">&#9776;</button>
  <span class="brand">{doc_title}</span>
  <div class="search"><input id="q" type="search" placeholder="Search (/)"
       autocomplete="off"><div id="results"></div></div>
  <button id="theme-toggle" class="iconbtn" title="Toggle theme">&#9680;</button>
</header>
<div class="page-grid">
  <nav class="left" id="left">{toc}</nav>
  <main id="main">{content}
<footer style="margin-top: 3rem; color: var(--muted); font-size: .85em;">
Based on <a href="https://github.com/XekriRedmane/lode_runner_reveng">lode_runner_reveng</a> by XekriRedmane.
HTML edition by <a href="https://github.com/fschuhi/a2-lode-runner">a2-lode-runner</a>.
License: <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a>.
<a href="index.html">About this edition</a>
</footer>
</main>
  <aside class="right">{outline}</aside>
</div>
<div id="popover" class="popover" hidden></div>
<script src="{mermaid}"></script>
<script src="{katex_js}"></script>
<script src="{katex_auto}"></script>
<script src="{minisearch}"></script>
<script src="assets/site-data.js"></script>
<script src="assets/app.js"></script>
</body>
</html>
"""


def main(argv):
    args = argv[1:]
    src = args[0] if args else "sample.nw"
    out = args[1] if len(args) > 1 else "output"
    HtmlWeaver().run([src], out)


if __name__ == "__main__":
    app.run(main)
