# Project Notes — arxiv-search

> Read this file at the start of every session before doing anything else.
> Every measured number must include the setup it was measured on.

---

## What this project is

A hybrid search engine over ~380k arXiv papers in cs.LG and cs.CL.
Built from scratch as a learning project: BM25 inverted index, dense vector
retrieval, a hand-built HNSW ANN index, hybrid fusion (RRF + weighted),
cross-encoder reranking, and a FastAPI service with Docker and CI.

---

## Current state

**Phase 0 complete.** Repo hygiene done. Tests not yet passing (BM25 not yet implemented).

---

## Architecture decisions

| Decision | Choice | Reason |
|---|---|---|
| Python version | 3.13.7 (Homebrew, `/opt/homebrew/bin/python3.13`) | User's machine; use same for Docker base image |
| Venv location | `.venv/` in repo root | Standard; already gitignored |
| Data file | `data/papers.jsonl` | Gitignored; 380,128 papers, ~512 MB |
| Year extraction | Parse arXiv ID (e.g. `1704.02362` → April 2017) | `date` field in papers.jsonl is `update_date`, not submission date |

---

## Measured numbers

*(None yet. Every number added here must state: what was measured, on what hardware, with what dataset size, at what date.)*

---

## Known issues / warnings

- `data/papers.jsonl` field `date` is arXiv's `update_date`. For submission year, parse the arXiv ID prefix instead.
- `scripts/harvest_arxiv.py` is untested against the live server. Do not run without a small `--limit` test first.
- Global gitignore (`~/.gitignore_global`) is not configured by the tool; user manages this manually.

---

## What's done

- [x] Phase 0: venv (Python 3.13.7), requirements.txt / requirements-dev.txt, data/.gitkeep, docs/ scaffold

## What's next

- [ ] Phase 1: Implement BM25 `fit()`, `idf()`, `search()` in `src/search/bm25.py`; pass all 7 tests; measure index build time and per-query latency on 380k papers
