"""Step-2 migration: flip prose in main.nw from LaTeX to Markdown.

***********************************************************************************
NOTE: Adapted from `latex_to_md.py` in XekriRedmane's `ultima1_reveng`
(see `scripts/PROVENANCE.md`). Here we import from `weave_lode_runner`
instead of `weave`. The mixing of projects is intentional: the Lode Runner
`main.nw` is incompatible with the newer Ultima `weave.py`.
***********************************************************************************

Operates ONLY on documentation (prose) chunks. Code chunks, their
`<<name>>=` headers, and the `@` / `@ %def` markers are copied byte-for-byte,
so the tangled .asm is unchanged (verify.py stays byte-perfect).

Mechanical transforms (text layer):
  - \\chapter/\\section/... -> #, ##, ...
  - \\textbf -> **; \\emph/\\textit -> *; \\texttt -> `code`; \\textsc -> plain
  - itemize/enumerate/description -> Markdown lists; quote -> blockquote
  - verbatim -> fenced code; \\ldots -> ...; ``...'' -> "..."; --- -> em dash
  - \\label -> <a id>; \\ref -> link; escaped \\& \\% etc. -> literal
  - includegraphics figures -> Markdown images with captions

Hard environments are left for step 3, flagged and preserved verbatim:
  - tikzpicture / figure-with-tikz -> TODO-CONVERT + ```latex fence (-> Mermaid)
  - table / tabular -> TODO-CONVERT + ```latex fence (-> pipe/HTML table)
  - dgrecord -> TODO-CONVERT + ```latex fence (-> HTML byte-field table)

$...$ math and [[ ]] refs are protected from all text transforms.

Usage:  python3 latex_to_md.py [INPUT=main.nw] [OUTPUT=main.nw.new]
"""

import re
import sys

from weave_lode_runner import Weaver

LIST_ENVS = {"itemize", "enumerate", "description"}
FENCE_ENVS = {  # captured verbatim into a ```latex TODO block (step 3 work)
    "table", "table*", "tabular", "tabular*", "tabularx", "longtable",
    "tikzpicture", "dgrecord",
}

PLACEHOLDER = "\x00%d\x00"
PLACE_RE = re.compile("\x00(\\d+)\x00")


# --------------------------------------------------------------- inline pass
def protect(text, store):
    def repl(m):
        store.append(m.group(0))
        return PLACEHOLDER % (len(store) - 1)
    text = re.sub(r"\[\[.*?\]\]", repl, text)              # [[ refs ]]
    text = re.sub(r"(?<!\\)\$(?:\\.|[^$\\])*?\$", repl, text)  # $ math $
    return text


def restore(text, store):
    return PLACE_RE.sub(lambda m: store[int(m.group(1))], text)


def inline(text):
    """Convert inline LaTeX in one prose string to Markdown."""
    store = []
    text = protect(text, store)
    # quotes and dashes
    text = text.replace("``", '"').replace("''", '"')
    text = text.replace("---", "—").replace("--", "–")
    text = re.sub(r"\\(?:ldots|dots)\b", "…", text)
    text = re.sub(r"\\(?:quad|qquad)\b", " ", text)
    text = re.sub(r"(?<!\\)~", " ", text)   # nbsp -> space, but keep escaped \~
    # inline verbatim and cross-references
    text = re.sub(r"\\verb(.)(.*?)\1", r"`\2`", text)
    text = re.sub(r"\\(?:auto)?ref\{([^}]*)\}", r"[\1](#\1)", text)
    text = re.sub(r"\\label\{([^}]*)\}", r'<a id="\1"></a>', text)
    # literal-special texttt (pathological: \texttt{\{} \texttt{\}} \texttt{\~{}})
    text = (text.replace(r"\texttt{\{}", "`{`").replace(r"\texttt{\}}", "`}`")
                .replace(r"\texttt{\~{}}", "`~`"))
    # font commands (loop to catch simple nesting)
    for _ in range(3):
        text = re.sub(r"\\textbf\{([^{}]*)\}", r"**\1**", text)
        text = re.sub(r"\\(?:emph|textit)\{([^{}]*)\}", r"*\1*", text)
        text = re.sub(r"\\texttt\{([^{}]*)\}", r"`\1`", text)
        text = re.sub(r"\\textsc\{([^{}]*)\}", r"\1", text)
    # drop standalone formatting commands
    text = re.sub(r"\\(?:noindent|par|centering|small|footnotesize|scriptsize|"
                  r"normalsize|large|Large|bigskip|medskip|smallskip)\b", "", text)
    text = text.replace("\\\\", "<br>")
    # escaped specials -> literal
    text = re.sub(r"\\([&%#_${}])", r"\1", text)
    return restore(text, store)


def plain(text):
    """Strip to plain text (for image alt)."""
    t = inline(text)
    t = re.sub(r"\[\[(.+?)\]\]", r"\1", t)
    t = re.sub(r"[`*]", "", t)
    t = re.sub(r"<[^>]+>", "", t)
    return t.strip().replace('"', "'")


# --------------------------------------------------------------- braces/envs
def find_braced(s, oi):
    depth = 0
    for k in range(oi, len(s)):
        if s[k] == "{":
            depth += 1
        elif s[k] == "}":
            depth -= 1
            if depth == 0:
                return s[oi + 1:k], k
    return s[oi + 1:], len(s)


def extract_caption(text):
    k = text.find("\\caption{")
    if k < 0:
        return None
    content, _ = find_braced(text, text.index("{", k))
    return " ".join(content.split())


def extract_image(text):
    m = re.search(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}", text)
    return m.group(1) if m else None


def capture_env(lines, i, env):
    beg = re.compile(r"\\begin\{" + re.escape(env) + r"\}")
    end = re.compile(r"\\end\{" + re.escape(env) + r"\}")
    depth, j = 0, i
    while j < len(lines):
        if beg.search(lines[j]):
            depth += 1
        if end.search(lines[j]):
            depth -= 1
            if depth == 0:
                return j + 1, lines[i:j + 1]
        j += 1
    return len(lines), lines[i:]


def labels_anchors(text):
    out = [f'<a id="{lab}"></a>' for lab in re.findall(r"\\label\{([^}]*)\}", text)]
    return out + ([""] if out else [])


def build_figure(block):
    text = "\n".join(block)
    cap = extract_caption(text)
    img = extract_image(text)
    out = labels_anchors(text)
    if img:
        out.append(f"![{plain(cap) if cap else ''}]({img})")
        out.append("")
        if cap:
            out.append(f"**Figure.** {inline(cap)}")
            out.append("")
    else:  # tikz figure -> TODO
        out.append(f"> **TODO-CONVERT — figure (TikZ → Mermaid):** "
                   f"{inline(cap) if cap else 'diagram'}")
        out += ["", "```latex", *block, "```", ""]
    return out


def build_fence(block, kind):
    text = "\n".join(block)
    cap = extract_caption(text)
    out = labels_anchors(text)
    note = {"table": "table (→ pipe/HTML table)",
            "tikz": "diagram (→ Mermaid)",
            "dgrecord": "byte-field layout (→ HTML table)"}[kind]
    head = f"> **TODO-CONVERT — {note}:**"
    if cap:
        head += " " + inline(cap)
    out += [head, "", "```latex", *block, "```", ""]
    return out


def build_verbatim(block):
    return ["```", *block[1:-1], "```", ""]


def convert_list(lines, i, depth=0):
    env = re.match(r"\\begin\{(\w+)\}", lines[i].strip()).group(1)
    ordered = env == "enumerate"
    desc = env == "description"
    indent = "  " * depth
    out, j = [], i + 1
    prefix, raw = None, ""   # current item's emitted prefix + accumulated raw body

    def flush():
        nonlocal prefix, raw
        if prefix is None:
            return
        body = inline(raw.strip())
        out.append(prefix + (f" — {body}" if desc and body else body))
        prefix, raw = None, ""

    while j < len(lines):
        s = lines[j].strip()
        if re.match(r"\\end\{" + env + r"\}", s):
            flush()
            j += 1
            break
        if re.match(r"\\begin\{(?:itemize|enumerate|description)\}", s):
            flush()
            j, sub = convert_list(lines, j, depth + 1)
            out += sub
            continue
        mi = re.match(r"\\item\b\s*(.*)$", s)   # strip first: items are often indented
        if mi:
            flush()
            rest = mi.group(1)
            if desc and rest.startswith("["):
                # Find the ] matching \item[ by bracket depth, so [[ ]] inside
                # the term or the body never confuses the term/body split.
                depth, end = 0, -1
                for idx, ch in enumerate(rest):
                    if ch == "[":
                        depth += 1
                    elif ch == "]":
                        depth -= 1
                        if depth == 0:
                            end = idx
                            break
                if end >= 0:
                    prefix = f"{indent}- **{inline(rest[1:end])}**"
                    raw = rest[end + 1:].lstrip()
                else:
                    prefix, raw = f"{indent}- ", rest
            elif desc:
                prefix, raw = f"{indent}- ", rest
            else:
                prefix, raw = f"{indent}{'1.' if ordered else '-'} ", rest
            j += 1
            continue
        if prefix is not None and s:        # continuation line of current item
            raw += " " + s
            j += 1
            continue
        if not s:
            j += 1
            continue
        flush()
        out.append(inline(s))
        j += 1
    if depth == 0:
        out.append("")
    return j, out


SKIP_LINE = re.compile(
    r"\\(?:maketitle|tableofcontents|clearpage|newpage|bigskip|medskip|"
    r"smallskip|FloatBarrier|centering|appendix|listoffigures|listoftables)\b\*?$"
)
SKIP_ARG = re.compile(r"\\(?:pagestyle|thispagestyle|usepackage|setlength)\{[^}]*\}")
DOC_DELIM = re.compile(r"\\(?:begin|end)\{document\}")
HEADING = re.compile(r"\\(part|chapter|section|subsection|subsubsection)\*?\{(.*)\}\s*$")
LEVELS = {"part": 1, "chapter": 1, "section": 2, "subsection": 3, "subsubsection": 4}


def is_special(s):
    s = s.strip()
    return bool(not s or s.startswith(("\\begin", "\\end")) or HEADING.match(s)
                or SKIP_LINE.match(s) or SKIP_ARG.fullmatch(s) or DOC_DELIM.match(s))


def is_unbalanced(s):
    """True if open braces remain or $-math is left open on this line."""
    b = len(re.findall(r"(?<!\\)\{", s)) - len(re.findall(r"(?<!\\)\}", s))
    d = len(re.findall(r"(?<!\\)\$", s))
    return b > 0 or d % 2 == 1


def transform_block(lines):
    out, i, n = [], 0, len(lines)
    while i < n:
        line = lines[i]
        s = line.strip()
        if not s:
            out.append("")
            i += 1
            continue
        if DOC_DELIM.match(s) or SKIP_LINE.match(s) or SKIP_ARG.fullmatch(s):
            i += 1
            continue
        m = HEADING.match(line)
        if m:
            out.append("#" * LEVELS[m.group(1)] + " " + inline(m.group(2)))
            out.append("")
            i += 1
            continue
        mb = re.match(r"\\begin\{(\w+\*?)\}", s)
        if mb:
            env = mb.group(1)
            if env in LIST_ENVS:
                i, blk = convert_list(lines, i)
                out += blk
            else:
                j, block = capture_env(lines, i, env)
                if env in ("figure", "figure*"):
                    out += build_figure(block)
                elif env == "verbatim":
                    out += build_verbatim(block)
                elif env == "quote":
                    inner = transform_block(block[1:-1])
                    out += [("> " + x) if x.strip() else ">" for x in inner] + [""]
                elif env == "center":
                    out += transform_block(block[1:-1])
                elif env == "tikzpicture":
                    out += build_fence(block, "tikz")
                elif env == "dgrecord":
                    out += build_fence(block, "dgrecord")
                elif env in FENCE_ENVS:
                    out += build_fence(block, "table")
                else:  # unknown env -> preserve as TODO
                    out += [f"> **TODO-CONVERT — unknown env `{env}`:**",
                            "", "```latex", *block, "```", ""]
                i = j
            continue
        # Plain prose: join continuation lines so multi-line \emph{...},
        # \texttt{...}, $...$ etc. are converted as one logical unit.
        buf = line
        while is_unbalanced(buf) and i + 1 < n and not is_special(lines[i + 1]):
            i += 1
            buf = buf + " " + lines[i]
        out.append(inline(buf))
        i += 1
    return out


def extract_title(lines):
    text = "\n".join(lines)
    k = text.find("\\title{")
    if k < 0:
        return "Document", None
    content, _ = find_braced(text, text.index("{", k))
    content = content.replace("%", "")
    parts = [p.strip() for p in content.split("\\\\") if p.strip()]
    parts = [re.sub(r"\\(?:large|Large|huge|small)\b", "", p).strip() for p in parts]
    title = parts[0] if parts else "Document"
    subtitle = parts[1] if len(parts) > 1 else None
    return title, subtitle


def transform_leading(lines):
    title, subtitle = extract_title(lines)
    idx = next((k for k, l in enumerate(lines) if l.lstrip().startswith("\\chapter")),
               len(lines))
    out = [f"# {title}", ""]
    if subtitle:
        out += [f"*{inline(subtitle)}*", ""]
    out += transform_block(lines[idx:])
    return out


def main():
    inp = sys.argv[1] if len(sys.argv) > 1 else "main.nw"
    outp = sys.argv[2] if len(sys.argv) > 2 else "main.nw.new"
    with open(inp) as f:
        lines = [l.rstrip("\n") for l in f.readlines()]
    chunks = Weaver().extract_chunk_info(lines, inp, 0)
    first = chunks[0].start if chunks else len(lines)

    out = transform_leading(lines[:first])
    for c in chunks:
        if c.kind == "code":
            out += lines[c.start:c.end]                 # verbatim (header+body)
        else:
            out.append(lines[c.start])                  # @ / @ %def marker
            out += transform_block(lines[c.start + 1:c.end])

    with open(outp, "w") as f:
        f.write("\n".join(out) + "\n")
    print(f"Wrote {outp}: {len(out)} lines (from {len(lines)}).")


if __name__ == "__main__":
    main()
