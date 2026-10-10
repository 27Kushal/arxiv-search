# Learning Notes — arxiv-search

> Written by the student after each phase. Reviewed by the mentor.
> Each section: plain-language concept explanation, key trade-offs, quiz answers.

---

## Phase 0 — Repo hygiene

### Concepts

**Virtual environment:** An isolated copy of Python and its packages that lives inside your
project folder. When you `pip install` inside it, packages go there — not into the system
Python. This means different projects can have different versions of the same library without
clashing.

**`sys.path`:** Python's module search list. When you write `import foo`, Python walks this
list of directories and looks for a folder or file named `foo`. You can prepend directories
to it at runtime to make imports work without a build/install step.

**`.gitkeep`:** A git convention — an empty file placed inside a directory you want git to
track, because git doesn't track empty directories. The name is just human-readable
convention; it has no special meaning to git.

---

### Quiz answers

**Q1. Why two requirements files (`requirements.txt` vs `requirements-dev.txt`) instead
of one? What breaks if you mix them?**

Two audiences for the code:
- A **developer** (or CI server) needs pytest, rank_bm25, and other tools to *work on* the code.
- A **production server** only needs to *run* the application — it has no use for test tools.

If you mix them into one file and install everything in production:
1. **Image bloat** — numpy (~20 MB, pulled in by rank_bm25) ships in the Docker image for no reason.
2. **Security** — every extra package is a potential vulnerability surface.
3. **Clarity** — someone reading requirements.txt six months later can't tell if rank_bm25
   is a runtime dependency or a leftover test tool.

Pattern: `requirements.txt` = "run the app". `requirements-dev.txt` = "work on the app".
Dockerfile installs only `requirements.txt`. CI installs both.

---

**Q2. Why `data/*` + `!data/.gitkeep` instead of just `data/`? What would break?**

Git doesn't track directories — it tracks *files*. A directory only appears in a clone if it
contains at least one tracked file.

- `data/` in .gitignore → git ignores the entire directory including any file inside it. A
  fresh clone has no `data/` folder at all. Any script that writes to `data/papers.jsonl`
  fails immediately with `FileNotFoundError` because the parent directory doesn't exist.

- `data/*` → ignores all *contents* of data/, but not the directory concept itself.
  `!data/.gitkeep` un-ignores that one empty file. Git sees one tracked file → creates the
  directory on clone. Scripts can write into it without needing to call `mkdir` themselves.

`.gitkeep` is just an empty file. Any tracked file inside `data/` would work; the name is
a convention that signals intent.

---

**Q3. How does pytest find `src/search/bm25.py` without `src/__init__.py`? What is that
line 9 doing, and why is it the right approach here?**

Line 9 of `tests/test_bm25.py`:
```python
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
```

Step by step:
- `__file__` → absolute path of the test file, e.g. `.../arxiv-search/tests/test_bm25.py`
- `.parents[1]` → go up two levels to the repo root (parents[0] = tests/, parents[1] = repo root)
- `/ "src"` → append "src", giving `.../arxiv-search/src`
- `sys.path.insert(0, ...)` → prepend that path to Python's module search list

Now when Python sees `from search.bm25 import BM25`, it looks inside `src/` first, finds
`src/search/` (which has `__init__.py`, making it a proper package), and imports successfully.

`src/` itself doesn't need `__init__.py` because it's not being imported as a package —
it's just a root directory that Python searches for packages inside.

Why this approach and not `pip install -e .`? The repo has no `pyproject.toml` yet, so it
isn't an installable package. The sys.path trick is zero-config for now. Downside: you must
run pytest from the repo root. When we add a build file later, we'll switch to an editable
install and remove this line.

---

### Key trade-offs

| Choice | Trade-off |
|---|---|
| sys.path manipulation | Simple now, but fragile — only works from repo root. Replace with editable install when adding pyproject.toml. |
| Two requirements files | Slightly more to maintain; worth it for build reproducibility and clear intent. |
| `.gitkeep` pattern | Conventional, not standard — some projects use `mkdir -p` in Makefiles instead. Either works. |
