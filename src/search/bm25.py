"""BM25 from scratch. Your job: fill in the TODOs.

For a query q and document d:

    score(d, q) = sum over query terms t of
        idf(t) * tf(t, d) * (k1 + 1) / (tf(t, d) + k1 * (1 - b + b * len(d) / avgdl))

    idf(t) = log(1 + (N - df(t) + 0.5) / (df(t) + 0.5))

N = number of docs, df(t) = docs containing t, tf(t, d) = count of t in d,
avgdl = average doc length. Typical defaults: k1 = 1.5, b = 0.75.

Design hint: do NOT loop over every doc per query. Build an inverted index
(term -> list of (doc_id, tf)) so a query only touches docs that contain
its terms.
"""
import json
import math
import re
from collections import Counter, defaultdict

TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    # Baseline tokenizer. Later experiment: stopwords, stemming, keeping "k-v" style terms.
    return TOKEN_RE.findall(text.lower())


class BM25:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.index = defaultdict(list)  # term -> [(doc_id, tf), ...]
        self.doc_len: list[int] = []
        self.avgdl = 0.0
        self.n_docs = 0

    def fit(self, docs: list[str]) -> None:
        for doc_id, text in enumerate(docs):
            tokens=tokenize(text)
            self.doc_len.append(len(tokens))
            counts=Counter(tokens) #counts the occurence of each token
            for term,tf in counts.items():
                self.index[term].append((doc_id,tf))

        self.n_docs=len(docs)
        self.avgdl=sum(self.doc_len)/len(docs)

    def idf(self, term: str) -> float:
        # TODO: use len(self.index[term]) as df. Careful: indexing a defaultdict
        #       with an unseen term inserts it. Use .get().
        raise NotImplementedError

    def search(self, query: str, k: int = 10) -> list[tuple[int, float]]:
        # TODO: accumulate scores per doc via the inverted index,
        #       return the top-k (doc_id, score) sorted high to low.
        raise NotImplementedError


if __name__ == "__main__":
    papers = [json.loads(l) for l in open("data/papers.jsonl", encoding="utf-8")]
    texts = [p["title"] + ". " + p["abstract"] for p in papers]

    bm25 = BM25()
    bm25.fit(texts)

    for q in ["kv cache compression", "low rank adaptation fine tuning"]:
        print(f"\n{q}")
        for doc_id, score in bm25.search(q, k=5):
            print(f"  {score:6.2f}  {papers[doc_id]['title']}")
