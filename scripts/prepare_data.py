"""Filter the arXiv metadata dump down to cs.LG / cs.CL papers.

Usage:
    python prepare_data.py --src arxiv-metadata-oai-snapshot.json --limit 150000

Input:  Kaggle "arXiv Dataset" JSONL (one JSON object per line).
Output: data/papers.jsonl with id, title, abstract, categories, date.
"""
import argparse
import json
import re
from pathlib import Path

KEEP = {"cs.LG", "cs.CL"}


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", default="data/papers.jsonl")
    ap.add_argument("--limit", type=int, default=150_000)
    args = ap.parse_args()

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    kept = 0
    with open(args.src, encoding="utf-8") as fin, open(args.out, "w", encoding="utf-8") as fout:
        for line in fin:
            rec = json.loads(line)
            cats = set(rec["categories"].split())
            if not cats & KEEP:
                continue
            abstract = clean(rec.get("abstract", ""))
            if len(abstract) < 100:  # skip empty / withdrawn entries
                continue
            fout.write(json.dumps({
                "id": rec["id"],
                "title": clean(rec["title"]),
                "abstract": abstract,
                "categories": rec["categories"],
                "date": rec.get("update_date"),
            }) + "\n")
            kept += 1
            if kept >= args.limit:
                break
    print(f"kept {kept} papers -> {args.out}")


if __name__ == "__main__":
    main()
