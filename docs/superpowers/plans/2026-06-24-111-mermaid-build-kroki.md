# Mermaid Build via kroki.io Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the broken `mmdc`-CLI strategy in `plcc-mermaid-diagram-build` with an HTTP call to kroki.io that returns a PNG — no local tools required.

**Architecture:** `mermaid/build.py` reads the `.mmd` source, encodes it as `zlib + base64url`, GETs `https://kroki.io/mermaid/png/<encoded>`, and writes the response bytes to the output file. This mirrors the existing `plantuml/build.py` pattern exactly. No other files change.

**Tech Stack:** Python stdlib only — `urllib.request`, `zlib`, `base64`. No new dependencies.

## Global Constraints

- Run unit tests with: `bin/test/units.bash`
- Run the specific test file with: `bin/test/units.bash src/plcc/diagram/mermaid/build_test.py`
- TDD: write the failing test first, verify it fails, then implement.
- Commit after each task passes.
- Follow the existing style in `src/plcc/diagram/plantuml/build.py` for structure and error handling.

---

### Task 1: Replace mermaid build with kroki.io HTTP call

**Files:**
- Modify: `src/plcc/diagram/mermaid/build.py`
- Modify: `src/plcc/diagram/mermaid/build_test.py`

**Interfaces:**
- Consumes: nothing from other tasks
- Produces: `main(argv=None)` entry point (unchanged signature); `_encode(source: str) -> str` (new helper, importable for testing)

- [ ] **Step 1: Delete the three existing mmdc-specific tests, leaving only the arg-parsing test**

Replace the contents of `src/plcc/diagram/mermaid/build_test.py` with:

```python
import urllib.error
import pytest
from unittest.mock import patch, MagicMock

from .build import main as run_main


def test_missing_required_args_exits_nonzero():
    import docopt
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])
```

- [ ] **Step 2: Run the test file to confirm the one remaining test still passes**

```bash
bin/test/units.bash src/plcc/diagram/mermaid/build_test.py
```

Expected: `1 passed`

- [ ] **Step 3: Write a failing test for the happy path**

Add to `src/plcc/diagram/mermaid/build_test.py`:

```python
def test_renders_png_via_kroki(tmp_path):
    src = tmp_path / "diagram.mmd"
    src.write_text("classDiagram\n    class Foo {}\n")
    out = tmp_path / "diagram.png"

    fake_png = b'\x89PNG fake'
    mock_response = MagicMock()
    mock_response.read.return_value = fake_png
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch('urllib.request.urlopen', return_value=mock_response):
        run_main([f'--input={src}', f'--output={out}'])

    assert out.read_bytes() == fake_png
```

- [ ] **Step 4: Run to confirm it fails**

```bash
bin/test/units.bash src/plcc/diagram/mermaid/build_test.py
```

Expected: FAIL — `test_renders_png_via_kroki` fails (e.g., `shutil.which` / `subprocess.run` is called instead of `urlopen`)

- [ ] **Step 5: Replace `src/plcc/diagram/mermaid/build.py` with the kroki.io implementation**

```python
import base64
import enum
import sys
import urllib.error
import urllib.request
import zlib

from docopt import docopt

from ...verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-mermaid-diagram-build
    Render a Mermaid diagram source file to a PNG image via kroki.io.

Usage:
    plcc-mermaid-diagram-build --input=FILE --output=FILE [-v ...] [options]

Options:
    --input=FILE    Path to .mmd source file.
    --output=FILE   Path to write .png image.
    -h --help       Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def _encode(source):
    compressed = zlib.compress(source.encode('utf-8'), 9)
    return base64.urlsafe_b64encode(compressed).decode('utf-8').rstrip('=')


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-mermaid-diagram-build", Events, args)
    input_file = args['--input']
    output_file = args['--output']
    verbose.emit(Events.STARTED, message=f"rendering {input_file}")
    try:
        with open(input_file) as f:
            source = f.read()
        url = f'https://kroki.io/mermaid/png/{_encode(source)}'
        req = urllib.request.Request(url, headers={'User-Agent': 'plcc-ng/1.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            png_bytes = response.read()
    except Exception as e:
        print(f"plcc-mermaid-diagram-build: {e}", file=sys.stderr)
        sys.exit(1)
    with open(output_file, 'wb') as f:
        f.write(png_bytes)
    verbose.emit(Events.FINISHED, message=f"wrote {output_file}")
```

- [ ] **Step 6: Run tests to confirm happy path passes**

```bash
bin/test/units.bash src/plcc/diagram/mermaid/build_test.py
```

Expected: `2 passed`

- [ ] **Step 7: Write a failing test for HTTP errors**

Add to `src/plcc/diagram/mermaid/build_test.py`:

```python
def test_http_error_prints_message_and_exits(tmp_path, capsys):
    src = tmp_path / "diagram.mmd"
    src.write_text("classDiagram\n")
    out = tmp_path / "diagram.png"

    with patch('urllib.request.urlopen', side_effect=urllib.error.URLError('connection refused')):
        with pytest.raises(SystemExit) as exc:
            run_main([f'--input={src}', f'--output={out}'])

    assert exc.value.code != 0
    _, err = capsys.readouterr()
    assert 'plcc-mermaid-diagram-build' in err
```

- [ ] **Step 8: Run to confirm it passes (implementation already handles this)**

```bash
bin/test/units.bash src/plcc/diagram/mermaid/build_test.py
```

Expected: `3 passed`

- [ ] **Step 9: Write a failing test for URL encoding**

Add to `src/plcc/diagram/mermaid/build_test.py`:

```python
def test_encodes_source_in_url(tmp_path):
    src = tmp_path / "diagram.mmd"
    src.write_text("classDiagram\n    class Bar {}\n")
    out = tmp_path / "diagram.png"

    captured_urls = []

    def fake_urlopen(req, timeout=None):
        captured_urls.append(req.full_url)
        mock_response = MagicMock()
        mock_response.read.return_value = b'\x89PNG'
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        return mock_response

    with patch('urllib.request.urlopen', side_effect=fake_urlopen):
        run_main([f'--input={src}', f'--output={out}'])

    assert len(captured_urls) == 1
    url = captured_urls[0]
    assert url.startswith('https://kroki.io/mermaid/png/')
    payload = url[len('https://kroki.io/mermaid/png/'):]
    assert len(payload) > 0
```

- [ ] **Step 10: Run to confirm all four tests pass**

```bash
bin/test/units.bash src/plcc/diagram/mermaid/build_test.py
```

Expected: `4 passed`

- [ ] **Step 11: Run the full unit suite to check for regressions**

```bash
bin/test/units.bash
```

Expected: all tests pass (previously 1073 passed, 1 skipped)

- [ ] **Step 12: Commit**

```bash
git add src/plcc/diagram/mermaid/build.py src/plcc/diagram/mermaid/build_test.py
git commit -m "feat: render mermaid diagrams via kroki.io instead of mmdc"
```
