# LaTeX validation

## Preferred portable workflow

Use the bundled Python utility through UV. It downloads no compiler unless
`--install-tectonic` is explicitly supplied.

```text
uv run <skill-dir>/scripts/compile_latex.py <tailored.tex> \
  --expected-keyword Python \
  --expected-keyword "REST APIs" \
  --forbidden-keyword "unsupported requirement"
```

If Tectonic is missing, obtain the user's approval for a network download and
rerun:

```text
uv run <skill-dir>/scripts/compile_latex.py <tailored.tex> \
  --install-tectonic \
  --expected-keyword Python
```

The script:

1. Uses Tectonic from `PATH` or its existing skill cache.
2. With explicit permission, downloads the pinned official Tectonic 0.16.9
   release for Windows, macOS, or Linux.
3. Verifies the release asset against its pinned SHA-256 digest.
4. Uses the pinned direct Tectonic bundle URL at
   `data1.fullyjustified.net`, avoiding reliance on the redirector host.
5. Compiles with Tectonic's `--untrusted` mode and a bounded timeout.
6. Opens the generated PDF with `pypdf` and verifies extractable text, required
   visible keywords, and forbidden unsupported keywords.
7. Only after validation, atomically publishes the final PDF beside the tailored
   `.tex`. If that path exists, it chooses a numbered suffix instead of
   overwriting it.
8. Prints a structured JSON report with the compiler, build PDF, published PDF,
   page count, and extracted character count.

Use `--final-pdf <path>` to select another publication path. Use
`--overwrite-final` only when replacing that exact PDF is intentional. A failed
compilation or validation never publishes or modifies the requested final PDF.

Tectonic is a self-contained native engine, not a pure-Python compiler. The
bundled Python utility handles its installation and validation without requiring
TeX Live, MiKTeX, administrator privileges, or a permanent project dependency.
The first compilation may download TeX support files into the skill-controlled
Tectonic cache.

On Windows, the pinned Tectonic build cannot reliably load `fontawesome5` and
may terminate inside its font engine. The utility rejects this package during
preflight instead of allowing a native crash. Replace decorative icon commands
with visible labels such as `Email`, `Phone`, `LinkedIn`, and `GitHub` in the
tailored copy. Keep the original CV unchanged.

## Cache and network behavior

The verified binary is cached under the platform's user cache directory:

- Windows: `%LOCALAPPDATA%/tailor-latex-cv/tectonic/<version>/`
- Linux: `${XDG_CACHE_HOME:-~/.cache}/tailor-latex-cv/tectonic/<version>/`
- macOS: `~/.cache/tailor-latex-cv/tectonic/<version>/`

Use `--cache-dir <path>` to select a different cache. Never download or execute
an unverified release asset. Request sandbox or network approval when the active
environment requires it.

## Existing compiler fallback

If Tectonic cannot compile a document because it depends on an incompatible
package or engine behavior, use an already-installed compiler in this order:

1. `latexmk`, selecting pdfLaTeX, XeLaTeX, or LuaLaTeX from the source.
2. XeLaTeX or LuaLaTeX for `fontspec`, `unicode-math`, or system fonts.
3. pdfLaTeX for conventional PDF-oriented documents.

Representative commands:

```text
latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error -outdir=<output-dir> <tailored.tex>
latexmk -xelatex -interaction=nonstopmode -halt-on-error -file-line-error -outdir=<output-dir> <tailored.tex>
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=<output-dir> <tailored.tex>
xelatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=<output-dir> <tailored.tex>
```

Do not install a full TeX distribution or system packages without explicit user
approval.

## Diagnose focused failures

Read the first actionable LaTeX error and its source line. Fix only issues
introduced by the tailored copy, such as:

- unescaped `%`, `&`, `_`, `#`, `$`, `{`, or `}`;
- unbalanced braces or environments;
- a renamed or malformed command;
- text that overflows a rigid CV macro;
- an engine mismatch.

Retry no more than three focused edit-and-compile cycles. If the original CV
also fails unchanged, distinguish the pre-existing failure from the tailored
changes.

## Validate the result

Before reporting success, require all of the following:

- the compiler exits successfully;
- the expected PDF exists and is non-empty;
- PDF text extraction returns meaningful CV content;
- important supported keywords are visible in source and extracted PDF text;
- unsupported requirements are not presented as candidate claims;
- no hidden keyword technique was introduced;
- the document has no obvious missing sections or accidental blank output.
- the final PDF was published only after all prior checks passed.

Render or visually inspect the PDF when a PDF inspection capability is
available and layout changes are material.
