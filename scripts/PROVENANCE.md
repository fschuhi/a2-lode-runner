# Provenance: adapted files in `scripts/`

Several files in this directory are adapted from two projects by XekriRedmane. This file records where they come from, what was changed, and under which terms they are used. The other files in `scripts/` (such as `nwtool.py`) are this project's own code.

## From `ultima1_reveng`

- **Project:** Ultima I -- Reverse Engineering
- **Author/owner:** XekriRedmane
- **Upstream repository:** https://github.com/XekriRedmane/ultima1_reveng
- **Upstream branch:** `main`
- **Upstream commit:** 2026-08-15T18:05:23Z (`7467ca80a63f76a8d29a70cbe8596e5c422aef5d`)
- **Copied:** 2026-09-07

The upstream project reverse engineers the Apple II version of *Ultima I: The First Age of Darkness*. Its HTML weaving pipeline is the basis of this project's HTML research browser. The design behind it is described in `html-migration-design.md` in the upstream repository.

| Local file       | Upstream file    | Changes                                                                                          |
|------------------|------------------|--------------------------------------------------------------------------------------------------|
| `latex_to_md.py` | `latex_to_md.py` | Imports from `weave_lode_runner` instead of `weave`; NOTE header added                           |
| `weave_html.py`  | `weave_html.py`  | Imports from `weave_lode_runner` instead of `weave`; call to `self.weaver.tangle` commented out; NOTE header added; docstring points to the upstream design document; footer with attribution added to the page template |
| `web/app.js`     | `web/app.js`     | NOTE comment added                                                                               |
| `web/style.css`  | `web/style.css`  | NOTE comment added                                                                               |

**Terms.** The upstream repository contains no license file. On 2026-09-19, XekriRedmane confirmed by email that its files may be used under the same license as `lode_runner_reveng`: the Creative Commons Attribution-ShareAlike 4.0 International License (CC BY-SA 4.0). The adapted files listed above are therefore licensed under CC BY-SA 4.0; see `LICENSE-CC-BY-SA-4.0.md`.

## From `lode_runner_reveng`

- **Project:** lode_runner_reveng
- **Author/owner:** XekriRedmane
- **Upstream repository:** https://github.com/XekriRedmane/lode_runner_reveng
- **Upstream branch:** `main`
- **Upstream commit:** 2026-07-08T20:24:20-07:00 (`113db1c16951717259c9ae5e128958b29de0634d`)

| Local file             | Upstream file | Changes                          |
|------------------------|---------------|----------------------------------|
| `weave_lode_runner.py` | `weave.py`    | Renamed; NOTE header added       |

The unmodified upstream `weave.py` is kept in `reference/lode_runner_reveng/`, where `nwtool.py` uses it; see `reference/lode_runner_reveng/PROVENANCE.md`.

**Terms.** The upstream repository is licensed under CC BY-SA 4.0, and so is `weave_lode_runner.py`; see `LICENSE-CC-BY-SA-4.0.md`.
