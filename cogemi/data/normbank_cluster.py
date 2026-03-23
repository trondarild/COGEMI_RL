# cogemi/data/normbank_cluster.py
"""
Cluster NormBank's 6 938 unique behavior strings into semantic action groups.

Pipeline
--------
1. Embed each unique behavior with nomic-embed-text (via Ollama).
2. Cluster the embeddings with k-means (default k=50).
3. Label each cluster by asking an LLM for a short canonical action phrase.
4. Write two CSV files:
   - data/normbank_behavior_clusters.csv
       behavior, cluster_id, cluster_label
   - data/normbank_cluster_labels.csv
       cluster_id, cluster_label, n_behaviors, example_behaviors (semicolon-sep)

Resumable: embeddings are cached to data/normbank_embeddings.npy +
           data/normbank_behavior_index.json so interrupted runs
           continue from where they left off.

Usage
-----
    python -m cogemi.data.normbank_cluster [--k 50] [--embed-model nomic-embed-text]
                                           [--label-model qwen3:1.7b] [--batch 64]
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
from collections import defaultdict
from pathlib import Path
from typing import List, Optional

import numpy as np

# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------

def embed_behaviors(
    behaviors: List[str],
    model: str = "nomic-embed-text",
    cache_npy: Path = Path("data/normbank_embeddings.npy"),
    cache_idx: Path = Path("data/normbank_behavior_index.json"),
    batch_size: int = 64,
    delay_s: float = 0.0,
) -> np.ndarray:
    """Return (N, D) embedding matrix for the given behaviors.

    Loads from cache if available; otherwise calls Ollama and saves.
    Behaviors are processed in the order given; the cache stores them by
    string value so partial runs are resumed correctly.
    """
    import ollama

    # Load existing cache
    cached_map: dict[str, list] = {}
    if cache_npy.exists() and cache_idx.exists():
        stored = np.load(cache_npy)
        index: list = json.loads(cache_idx.read_text())
        cached_map = {b: stored[i].tolist() for i, b in enumerate(index)}
        print(f"  Loaded {len(cached_map)} cached embeddings.")

    missing = [b for b in behaviors if b not in cached_map]
    if missing:
        print(f"  Embedding {len(missing)} new behaviors with {model!r} …")
        for i in range(0, len(missing), batch_size):
            chunk = missing[i : i + batch_size]
            for b in chunk:
                r = ollama.embeddings(model=model, prompt=b)
                cached_map[b] = r["embedding"]
            pct = min(i + batch_size, len(missing))
            print(f"    {pct}/{len(missing)}", end="\r")
            if delay_s:
                time.sleep(delay_s)
        print()
        # Save updated cache (index = ordered list of behavior strings)
        index_out = list(cached_map.keys())
        arr_out = np.array([cached_map[b] for b in index_out], dtype=np.float32)
        np.save(cache_npy, arr_out)
        cache_idx.write_text(json.dumps(index_out))
        print(f"  Saved {len(index_out)} embeddings to cache.")

    # Return matrix in the order of `behaviors`
    return np.array([cached_map[b] for b in behaviors], dtype=np.float32)


# ---------------------------------------------------------------------------
# Clustering
# ---------------------------------------------------------------------------

def cluster_embeddings(X: np.ndarray, k: int = 50, seed: int = 42) -> np.ndarray:
    """k-means clustering; returns integer label array of shape (N,)."""
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import normalize

    X_norm = normalize(X)
    km = KMeans(n_clusters=k, random_state=seed, n_init=10, max_iter=300)
    return km.fit_predict(X_norm)


# ---------------------------------------------------------------------------
# Cluster labelling
# ---------------------------------------------------------------------------

_LABEL_PROMPT = """\
Below is a sample of behavior descriptions from a social-norms dataset. \
They all belong to the same semantic cluster.

Behaviors:
{examples}

Write ONE short canonical action phrase (3–7 words) that best describes \
what all these behaviors have in common. Use infinitive form, e.g. \
"to use electronic devices", "to discuss personal finances".

Reply with ONLY the canonical phrase, no explanation."""


def label_cluster(examples: List[str], model: str = "qwen3:1.7b") -> str:
    """Ask an LLM for a canonical label for a cluster of behaviors."""
    import ollama

    prompt = _LABEL_PROMPT.format(examples="\n".join(f"- {e}" for e in examples[:15]))
    raw = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.0},
    ).message.content.strip()
    # Strip <think> blocks
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    # Strip leading "to " if present for consistency, then normalise
    raw = raw.strip('"\'').strip()
    return raw


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(
    normbank_csv: Path = Path("data/NormBank.csv"),
    out_behavior: Path = Path("data/normbank_behavior_clusters.csv"),
    out_labels: Path = Path("data/normbank_cluster_labels.csv"),
    k: int = 50,
    embed_model: str = "nomic-embed-text",
    label_model: str = "qwen3:1.7b",
    batch_size: int = 64,
) -> None:
    # ── 1. Collect unique behaviors ──────────────────────────────────────────
    print("Reading NormBank …")
    behavior_set: list[str] = []
    seen: set[str] = set()
    with open(normbank_csv, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            b = (row.get("behavior") or "").strip()
            if b and b not in seen:
                behavior_set.append(b)
                seen.add(b)
    print(f"  {len(behavior_set)} unique behaviors.")

    # ── 2. Embed ─────────────────────────────────────────────────────────────
    print("Embedding …")
    X = embed_behaviors(behavior_set, model=embed_model, batch_size=batch_size)

    # ── 3. Cluster ───────────────────────────────────────────────────────────
    print(f"Clustering into k={k} groups …")
    labels = cluster_embeddings(X, k=k)

    # Group behaviors by cluster
    clusters: dict[int, list[str]] = defaultdict(list)
    for behavior, cluster_id in zip(behavior_set, labels):
        clusters[int(cluster_id)].append(behavior)

    sizes = {cid: len(bs) for cid, bs in clusters.items()}
    print(f"  Cluster sizes: min={min(sizes.values())}  max={max(sizes.values())}  "
          f"mean={np.mean(list(sizes.values())):.0f}")

    # ── 4. Label clusters with LLM ───────────────────────────────────────────
    print(f"Labelling clusters with {label_model!r} …")
    cluster_labels: dict[int, str] = {}
    for cid in sorted(clusters):
        examples = clusters[cid]
        label = label_cluster(examples, model=label_model)
        cluster_labels[cid] = label
        print(f"  C{cid:02d} ({len(examples):3d} behaviors): {label!r}")

    # ── 5. Write outputs ─────────────────────────────────────────────────────
    print(f"Writing {out_behavior} …")
    with open(out_behavior, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["behavior", "cluster_id", "cluster_label"],
                           quoting=csv.QUOTE_ALL)
        w.writeheader()
        for behavior, cluster_id in zip(behavior_set, labels):
            w.writerow({
                "behavior":      behavior,
                "cluster_id":    int(cluster_id),
                "cluster_label": cluster_labels[int(cluster_id)],
            })

    print(f"Writing {out_labels} …")
    with open(out_labels, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=["cluster_id", "cluster_label", "n_behaviors", "example_behaviors"],
            quoting=csv.QUOTE_ALL,
        )
        w.writeheader()
        for cid in sorted(clusters):
            examples = clusters[cid]
            w.writerow({
                "cluster_id":       cid,
                "cluster_label":    cluster_labels[cid],
                "n_behaviors":      len(examples),
                "example_behaviors": "; ".join(examples[:8]),
            })

    print("Done.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main() -> None:
    parser = argparse.ArgumentParser(description="Cluster NormBank behaviors.")
    parser.add_argument("--normbank",     default="data/NormBank.csv")
    parser.add_argument("--k",            type=int,   default=50)
    parser.add_argument("--embed-model",  default="nomic-embed-text")
    parser.add_argument("--label-model",  default="qwen3:1.7b")
    parser.add_argument("--batch",        type=int,   default=64)
    args = parser.parse_args()

    run(
        normbank_csv=Path(args.normbank),
        k=args.k,
        embed_model=args.embed_model,
        label_model=args.label_model,
        batch_size=args.batch,
    )


if __name__ == "__main__":
    _main()
