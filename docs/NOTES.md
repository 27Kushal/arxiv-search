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

**Phase 1 complete.** BM25 implemented and tested. Latency baseline measured.
Next: Phase 2 — evaluation harness (labeled queries, nDCG@10, MRR, recall@k).

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

All numbers below: MacBook (CPU only), Python 3.13.7, 380,128 papers (data/papers.jsonl),
`title + ". " + abstract` as the document text. Date: 2026-10-12.

### Phase 1 — BM25 baseline

| Metric | Value |
|---|---|
| Index build time | 16.17 s |
| Unique index terms | 284,837 |
| Avg document length | 190.8 tokens |
| Query p50 latency (overall, 8 queries × 100 runs) | 113.9 ms |
| Query p95 latency (overall) | 199.0 ms |

Per-query breakdown (p50 / p95):

| Query | p50 ms | p95 ms | Note |
|---|---|---|---|
| kv cache compression | 3.0 | 3.5 | Rare terms → tiny posting lists |
| attention mechanism transformer | 31.0 | 33.8 | |
| low rank adaptation fine tuning | 53.8 | 65.5 | |
| contrastive learning visual representations | 115.7 | 126.2 | |
| diffusion model image generation | 125.6 | 137.9 | |
| graph neural network molecular property | 82.5 | 88.2 | |
| large language model inference | 179.5 | 197.6 | |
| reinforcement learning from human feedback | 198.0 | 254.9 | Common terms ("learning", "from") → huge posting lists |

**Known bottleneck:** high-frequency stopwords ("from", "learning", "in") have near-zero IDF
but long posting lists. Walking them dominates latency. Fix candidates: IDF threshold skip
during search, or stopword filter at tokenize time. Neither applied yet — baseline only.

---

## Known issues / warnings

- `data/papers.jsonl` field `date` is arXiv's `update_date`. For submission year, parse the arXiv ID prefix instead.
- `scripts/harvest_arxiv.py` is untested against the live server. Do not run without a small `--limit` test first.
- Global gitignore (`~/.gitignore_global`) is not configured by the tool; user manages this manually.
- BM25 search latency is dominated by common-word posting lists. p95 is ~200ms. Acceptable for now; will improve in hybrid phase.

---

## What's done

- [x] Phase 0: venv (Python 3.13.7), requirements.txt / requirements-dev.txt, data/.gitkeep, docs/ scaffold
- [x] Phase 1: BM25 fit/idf/search implemented from scratch; 7/7 tests pass; latency measured on 380k papers

## What's next

- [ ] Phase 2: Evaluation harness — write ~60-100 labeled queries, implement nDCG@10 / MRR / recall@k
