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

---

## Phase 1 — BM25 from scratch

### Concepts

**Inverted index:** A data structure that maps each term to the list of documents that
contain it. Built once during `fit()`; queried at search time. The core idea: instead of
scanning every document per query, you only look at the documents that contain your query
terms. If "hnswlib" appears in 30 documents, a query for "hnswlib" touches exactly 30
document entries — not 380,128.

Structure: `index["hnswlib"] = [(doc_id_1, tf_1), (doc_id_2, tf_2), ...]`
Each tuple is: which document, and how many times the term appears there.

**Term frequency (TF):** How many times a query term appears in a document.
Raw TF has diminishing returns: a term appearing 10× is informative, but not 10× more
informative than appearing once. BM25 applies a saturation function to control this.

**Inverse document frequency (IDF):** A measure of how rare (and therefore informative)
a term is across the whole corpus. Formula:

    idf(t) = log(1 + (N - df(t) + 0.5) / (df(t) + 0.5))

Where N = total documents, df(t) = documents containing term t.
- High df (common word like "learning") → small IDF → contributes little to score
- Low df (rare word like "hnswlib") → large IDF → contributes a lot to score

**BM25 score:** For each query term, the score contribution to a document is:

    idf(t) * tf * (k1 + 1) / (tf + k1 * (1 - b + b * dl/avgdl))

Where dl = document length, avgdl = average document length across corpus.
k1 (default 1.5) controls TF saturation. b (default 0.75) controls length normalisation.

The total document score = sum of contributions across all query terms.

**Stopwords:** Very common words (the, from, in, of) that appear in nearly every document.
Their IDF is near zero so they barely affect scores — but their posting lists are enormous,
so walking them wastes time. Not filtered yet; flagged as a known bottleneck.

---

### Quiz answers

**Q1. Why does `idf("learning")` return a small number while `idf("hnswlib")` returns a
large number? What does that mean for scoring?**

IDF formula: `log(1 + (N - df + 0.5) / (df + 0.5))`

"learning" appears in ~200,000 of 380,128 papers (df = 200k):
  → (380128 - 200000 + 0.5) / (200000 + 0.5) ≈ 0.9 → log(1.9) ≈ 0.64

"hnswlib" appears in ~30 papers (df = 30):
  → (380128 - 30 + 0.5) / (30 + 0.5) ≈ 12463 → log(12464) ≈ 9.43

IDF is a multiplier in the BM25 formula. "hnswlib" appearing once in a document pushes
the score up by ~9.43 × (TF component). "learning" appearing 20 times pushes the score
up by only ~0.64 × (TF component). Rare words that are specific to a topic dominate
the score; common words that appear everywhere contribute almost nothing.

Interview version: "IDF measures how surprising it is to find a word. Surprising = specific
= informative. Unsurprising = universal = tells you nothing about this document."

---

**Q2. What changes if you set `b = 0`? Would a long survey unfairly outrank a short abstract?**

The BM25 TF denominator is:
  tf + k1 * (1 - b + b * dl/avgdl)

With b = 0:
  tf + k1 * (1 - 0 + 0 * dl/avgdl) = tf + k1

The dl/avgdl term disappears. Document length is no longer in the formula.

Two documents both containing "attention" twice:
- Doc A: 50-word abstract. Density: 4% of tokens.
- Doc B: 5,000-word survey. Density: 0.04% of tokens.

With b=0 they score identically — but Doc A is clearly more focused on "attention".

With b=0.75: Doc B's large dl makes its denominator larger, reducing its TF component.
Doc A (shorter, more focused) gets the higher score. This is the correct behaviour.

Why not b=1.0? Full normalisation assumes all documents should be the same length. That's
too aggressive — a long paper may cover the topic deeply, not just be padded. b=0.75 is
a partial penalty: empirically tuned to work well across many corpora.

---

**Q3. How many redundant `idf()` calls did hoisting save for "reinforcement learning from
human feedback"?**

The query has 5 terms. Approximate df values:
- reinforcement: ~80,000 docs
- learning: ~200,000 docs
- from: ~300,000 docs
- human: ~60,000 docs
- feedback: ~40,000 docs

Without hoisting: idf() is called inside the inner loop, once per posting entry.
Total calls = 80k + 200k + 300k + 60k + 40k = 680,000 idf() calls for one query.

With hoisting: idf() called once per term, before the inner loop.
Total calls = 5.

Redundant calls eliminated: ~679,995 — for one query. Each call does a dict lookup
and a math.log(). This is why the placement of one line matters: same logic,
dramatically different performance. The p95 latency of 200ms for this query is still
high; this optimisation was necessary, not sufficient.

---

### Key trade-offs

| Choice | Trade-off |
|---|---|
| Inverted index | O(df) per query term instead of O(N). Fast for rare terms, slow for common ones. |
| No stopword filter (baseline) | Simpler code, easier to measure. Common words dominate latency at p95. |
| b=0.75 (default) | Partial length normalisation. Standard across literature; we haven't tuned it for this corpus yet. |
| k1=1.5 (default) | TF saturation. Same — untested on this corpus. Tuning these is Phase 5 work. |
| idf hoisted out of inner loop | ~680k fewer function calls per query. Correctness unchanged. Always do this. |

