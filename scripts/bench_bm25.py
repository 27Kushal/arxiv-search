"""Benchmark BM25 index build time and per-query search latency.
Run from repo root:  python scripts/bench_bm25.py
"""
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from search.bm25 import BM25

DATA = Path("data/papers.jsonl")

print("Loading papers...", flush=True)
papers = [json.loads(l) for l in DATA.open(encoding="utf-8")]
texts  = [p["title"] + ". " + p["abstract"] for p in papers]
print(f"  {len(papers):,} papers loaded", flush=True)

# --- Index build ---
print("\nBuilding index...", flush=True)
t0 = time.perf_counter()
bm25 = BM25()
bm25.fit(texts)
build_s = time.perf_counter() - t0
print(f"  Build time : {build_s:.2f} s")
print(f"  Index terms: {len(bm25.index):,}")
print(f"  Avg doc len: {bm25.avgdl:.1f} tokens")

# --- Per-query latency ---
queries = [
    "kv cache compression",
    "low rank adaptation fine tuning",
    "graph neural network molecular property",
    "reinforcement learning from human feedback",
    "contrastive learning visual representations",
    "large language model inference",
    "diffusion model image generation",
    "attention mechanism transformer",
]

print("\nSearching (100 runs per query)...", flush=True)
latencies_ms = []
for q in queries:
    times = []
    for _ in range(100):
        t0 = time.perf_counter()
        bm25.search(q, k=10)
        times.append((time.perf_counter() - t0) * 1000)
    p50 = statistics.median(times)
    p95 = statistics.quantiles(times, n=20)[18]   # 95th percentile
    latencies_ms.extend(times)
    print(f"  {p50:5.1f} ms p50  {p95:5.1f} ms p95   {q}")

overall_p50 = statistics.median(latencies_ms)
overall_p95 = statistics.quantiles(latencies_ms, n=20)[18]
print(f"\nOverall p50: {overall_p50:.1f} ms   p95: {overall_p95:.1f} ms")

# --- Top results for two queries (sanity check) ---
print("\n--- Sanity check: top-5 results ---")
for q in ["kv cache compression", "low rank adaptation fine tuning"]:
    print(f"\n{q}")
    for doc_id, score in bm25.search(q, k=5):
        print(f"  {score:6.2f}  {papers[doc_id]['title']}")
