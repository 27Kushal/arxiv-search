"""Harvest cs.LG / cs.CL paper metadata straight from arXiv's OAI-PMH endpoint.

Usage:
    python harvest_arxiv.py --limit 200          # quick test first
    python harvest_arxiv.py --limit 150000       # real run, can take an hour+

Writes data/papers.jsonl (same fields as prepare_data.py). Resumable: progress
is saved to data/.harvest_state.json, so Ctrl+C and rerun to continue.

Be polite: arXiv asks harvesters to wait between requests and to honor
503 Retry-After. This script does both. Check arXiv's OAI docs and Terms of
Use for API access (info.arxiv.org/help/oa) before running it for long.

Untested against the live server: verify with a small --limit first. If the
set name is rejected, run  ?verb=ListSets  on the endpoint and pass --set.
"""
import argparse
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = "https://oaipmh.arxiv.org/oai"
OAI = "{http://www.openarchives.org/OAI/2.0/}"
AX = "{http://arxiv.org/OAI/arXiv/}"
KEEP = {"cs.LG", "cs.CL"}
DELAY = 3.0  # seconds between requests
UA = {"User-Agent": "arxiv-search-student-project (contact: your-email-here)"}


def fetch(params: dict) -> ET.Element:
    url = BASE + "?" + urllib.parse.urlencode(params)
    while True:
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                return ET.fromstring(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 503:
                wait = int(e.headers.get("Retry-After", 30))
                print(f"503, waiting {wait}s")
                time.sleep(wait + 1)
                continue
            raise


def clean(t: str | None) -> str:
    return re.sub(r"\s+", " ", t or "").strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="cs")
    ap.add_argument("--limit", type=int, default=150_000)
    ap.add_argument("--out", default="data/papers.jsonl")
    args = ap.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    state_file = out.parent / ".harvest_state.json"
    state = json.loads(state_file.read_text()) if state_file.exists() else {"token": None, "kept": 0}

    kept = state["kept"]
    token = state["token"]
    with open(out, "a", encoding="utf-8") as fout:
        while kept < args.limit:
            params = ({"verb": "ListRecords", "resumptionToken": token} if token
                      else {"verb": "ListRecords", "set": args.set, "metadataPrefix": "arXiv"})
            root = fetch(params)
            err = root.find(f"{OAI}error")
            if err is not None:
                raise SystemExit(f"OAI error: {err.attrib.get('code')} {err.text}")

            for rec in root.iter(f"{OAI}record"):
                meta = rec.find(f"{OAI}metadata/{AX}arXiv")
                if meta is None:  # deleted record
                    continue
                cats = clean(meta.findtext(f"{AX}categories"))
                if not set(cats.split()) & KEEP:
                    continue
                abstract = clean(meta.findtext(f"{AX}abstract"))
                if len(abstract) < 100:
                    continue
                fout.write(json.dumps({
                    "id": meta.findtext(f"{AX}id"),
                    "title": clean(meta.findtext(f"{AX}title")),
                    "abstract": abstract,
                    "categories": cats,
                    "date": meta.findtext(f"{AX}updated") or meta.findtext(f"{AX}created"),
                }) + "\n")
                kept += 1

            rt = root.find(f"{OAI}ListRecords/{OAI}resumptionToken")
            token = rt.text.strip() if rt is not None and rt.text else None
            state_file.write_text(json.dumps({"token": token, "kept": kept}))
            fout.flush()
            print(f"kept {kept}")
            if not token:
                break
            time.sleep(DELAY)
    print(f"done: {kept} papers -> {out}")


if __name__ == "__main__":
    main()
