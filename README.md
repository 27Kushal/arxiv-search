# arxiv-search

A hybrid search engine over ~380,000 arXiv papers in cs.LG and cs.CL.

Built from scratch as a learning project. Every component is implemented by hand;
third-party libraries are used only for comparison and testing.

## Components (status)

| Component | Status |
|---|---|
| BM25 inverted index | done |
| Dense vector retrieval (embedding model) | not started |
| HNSW approximate nearest-neighbour index | not started |
| Hybrid fusion (RRF + weighted) | not started |
| Cross-encoder reranker | not started |
| FastAPI service | not started |
| Docker + GitHub Actions CI | not started |

## Setup

Requires Python 3.13. Uses a venv.

```
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Data file (`data/papers.jsonl`, ~512 MB, gitignored) must be obtained separately.
Run `prepare_data.py` against the Kaggle arXiv metadata dump, or download a pre-filtered
copy if one has been shared.

## Running the tests

From the repo root:

```
pytest -q
```

Expected: 7 passed.

## Running BM25 search

```
python src/search/bm25.py
```

Loads all 380k papers, builds the index (~16s), then prints top-5 results for two
example queries.

## Performance (BM25 baseline, CPU only, 380k papers)

Measured on a MacBook, Python 3.13.7, 2026-10-12.

| Metric | Value |
|---|---|
| Index build time | 16.17 s |
| Unique terms in index | 284,837 |
| Query latency p50 (8-query average) | 113.9 ms |
| Query latency p95 (8-query average) | 199.0 ms |

Latency varies by query. Specific term queries ("kv cache compression") run in ~3 ms.
Queries with common words ("reinforcement learning from human feedback") run at ~200 ms
because high-frequency terms have very large posting lists.

## Known failure cases / limitations (as of Phase 1)

- No semantic understanding. Searching "LoRA" will not find papers that only say
  "low-rank adaptation" and never use the abbreviation.
- No stopword filtering. Common words ("from", "learning") slow down queries
  significantly without improving ranking quality.
- Scores are not comparable across queries. A score of 31 for one query and 27 for
  another does not mean the first result is more relevant.
- Index is in-memory only. Rebuilding on every restart takes ~16s.

## Ablation table

To be filled in after Phase 5 (hybrid + reranking). Will show nDCG@10, MRR, and
p50/p95 latency for each configuration: BM25 alone, dense alone, RRF fusion,
weighted fusion, fusion + reranker.
