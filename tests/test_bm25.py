"""Run from the repo root:  pytest -q"""
import json
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from search.bm25 import BM25  # noqa: E402

DOCS = [
    "attention is all you need transformer attention",
    "convolutional networks for image recognition",
    "attention mechanisms in image captioning",
    "graph neural networks for molecules",
]


def make():
    m = BM25()
    m.fit(DOCS)
    return m


def test_counts():
    m = make()
    assert m.n_docs == 4
    assert m.doc_len[0] == 7
    assert m.avgdl == pytest.approx(sum(m.doc_len) / 4)


def test_rare_term_has_higher_idf():
    m = make()
    assert m.idf("molecules") > m.idf("attention") > 0


def test_unseen_term_is_harmless():
    m = make()
    assert m.idf("zzzz") >= 0
    assert m.search("zzzz", k=3) == []
    assert "zzzz" not in m.index  # idf must not insert into the index


def test_ranking_and_order():
    m = make()
    res = m.search("attention", k=10)
    ids = [d for d, _ in res]
    assert ids[0] == 0                      # highest tf, in a short doc
    assert set(ids) == {0, 2}               # only docs containing the term
    scores = [s for _, s in res]
    assert scores == sorted(scores, reverse=True)


def test_hand_computed_score():
    m = make()
    n, df = 4, 2
    idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
    tf, dl = 2, 7
    expected = idf * tf * (1.5 + 1) / (tf + 1.5 * (1 - 0.75 + 0.75 * dl / m.avgdl))
    assert dict(m.search("attention", k=4))[0] == pytest.approx(expected)


def test_top_k_respected():
    assert len(make().search("attention networks image", k=2)) == 2


def test_overlap_with_rank_bm25():
    """Scores differ (different idf formula) but top-10 should mostly agree."""
    rb = pytest.importorskip("rank_bm25")
    path = Path("data/papers.jsonl")
    if not path.exists():
        pytest.skip("data/papers.jsonl not found; run from repo root")
    papers = [json.loads(l) for _, l in zip(range(5000), open(path, encoding="utf-8"))]
    texts = [p["title"] + ". " + p["abstract"] for p in papers]
    from search.bm25 import tokenize
    ref = rb.BM25Okapi([tokenize(t) for t in texts])
    mine = BM25()
    mine.fit(texts)
    overlaps = []
    for q in ["kv cache compression", "low rank adaptation", "graph neural network",
              "reinforcement learning from human feedback", "contrastive learning"]:
        a = {d for d, _ in mine.search(q, 10)}
        scores = ref.get_scores(tokenize(q))
        b = set(sorted(range(len(scores)), key=lambda i: -scores[i])[:10])
        overlaps.append(len(a & b) / 10)
    assert sum(overlaps) / len(overlaps) >= 0.7, overlaps
