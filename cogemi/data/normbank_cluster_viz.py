# cogemi/data/normbank_cluster_viz.py
"""
Visualise NormBank behavior clusters via UMAP + matplotlib.

Produces two plots:
  data/normbank_clusters_umap.png  — scatter of all 6938 behaviors,
                                     coloured by cluster, with cluster
                                     centroids labelled
  data/normbank_clusters_umap.html — interactive version (if plotly available)

Usage
-----
    python -m cogemi.data.normbank_cluster_viz
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ---------------------------------------------------------------------------
# Load embeddings + cluster assignments
# ---------------------------------------------------------------------------

EMB_NPY   = Path("data/normbank_embeddings.npy")
EMB_IDX   = Path("data/normbank_behavior_index.json")
CLUST_CSV = Path("data/normbank_behavior_clusters.csv")
LABEL_CSV = Path("data/normbank_cluster_labels.csv")


def load_data():
    # Embeddings
    X = np.load(EMB_NPY).astype(np.float32)
    index = json.loads(EMB_IDX.read_text())          # list of behavior strings
    b2i = {b: i for i, b in enumerate(index)}

    # Cluster assignments (preserving embedding row order)
    b2cluster: dict[str, int] = {}
    b2label:   dict[str, str] = {}
    with open(CLUST_CSV, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            b2cluster[row["behavior"]] = int(row["cluster_id"])
            b2label[row["behavior"]]   = row["cluster_label"]

    # Cluster id → label
    id2label: dict[int, str] = {}
    with open(LABEL_CSV, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            lbl = row["cluster_label"] or f"C{int(row['cluster_id']):02d}"
            id2label[int(row["cluster_id"])] = lbl

    # Align arrays
    behaviors = [b for b in index if b in b2cluster]
    idx       = [b2i[b] for b in behaviors]
    X_aligned = X[idx]
    cluster_ids = np.array([b2cluster[b] for b in behaviors])

    return X_aligned, cluster_ids, behaviors, id2label


# ---------------------------------------------------------------------------
# UMAP reduction
# ---------------------------------------------------------------------------

def reduce_umap(X: np.ndarray, n_neighbors: int = 20, min_dist: float = 0.05) -> np.ndarray:
    import umap
    print("  Running UMAP …")
    reducer = umap.UMAP(
        n_components=2,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        metric="cosine",
        random_state=42,
        verbose=False,
    )
    return reducer.fit_transform(X)


# ---------------------------------------------------------------------------
# Static matplotlib plot
# ---------------------------------------------------------------------------

def plot_static(
    xy: np.ndarray,
    cluster_ids: np.ndarray,
    id2label: dict[int, str],
    out_path: Path,
) -> None:
    k = len(id2label)
    cmap = matplotlib.colormaps.get_cmap("tab20").resampled(k)

    fig, ax = plt.subplots(figsize=(16, 13))
    ax.set_facecolor("#f8f9fa")
    fig.patch.set_facecolor("#f8f9fa")

    # Scatter points
    for cid in sorted(id2label):
        mask = cluster_ids == cid
        ax.scatter(
            xy[mask, 0], xy[mask, 1],
            c=[cmap(cid)], s=6, alpha=0.55, linewidths=0,
            label=id2label[cid],
        )

    # Label cluster centroids
    for cid in sorted(id2label):
        mask = cluster_ids == cid
        cx, cy = xy[mask, 0].mean(), xy[mask, 1].mean()
        label = id2label[cid]
        # Shorten label for display
        short = label.replace("to ", "").replace(" with ", "\n").replace(" in ", "\n")
        ax.text(
            cx, cy, short,
            fontsize=6.5, ha="center", va="center", fontweight="bold",
            color="white",
            bbox=dict(boxstyle="round,pad=0.25", fc=cmap(cid), ec="none", alpha=0.82),
        )

    ax.set_title(
        f"NormBank behavior clusters (k=50, UMAP, cosine)\n"
        f"n={len(xy):,} unique behaviors",
        fontsize=13, pad=14,
    )
    ax.set_xlabel("UMAP 1", fontsize=10)
    ax.set_ylabel("UMAP 2", fontsize=10)
    ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
    for spine in ax.spines.values():
        spine.set_visible(False)

    plt.tight_layout()
    plt.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close()
    print(f"  Saved → {out_path}")


# ---------------------------------------------------------------------------
# Interactive plotly plot (optional)
# ---------------------------------------------------------------------------

def plot_interactive(
    xy: np.ndarray,
    cluster_ids: np.ndarray,
    behaviors: list[str],
    id2label: dict[int, str],
    out_path: Path,
) -> None:
    try:
        import plotly.graph_objects as go
        import plotly.express as px
    except ImportError:
        print("  plotly not installed — skipping interactive plot.")
        return

    labels  = [id2label.get(int(c), str(c)) for c in cluster_ids]
    fig = px.scatter(
        x=xy[:, 0], y=xy[:, 1],
        color=labels,
        hover_name=behaviors,
        title="NormBank behavior clusters (UMAP, cosine, k=50)",
        labels={"x": "UMAP 1", "y": "UMAP 2", "color": "Cluster"},
        opacity=0.6,
        width=1100, height=850,
        color_discrete_sequence=px.colors.qualitative.Dark24
            + px.colors.qualitative.Light24,
    )
    fig.update_traces(marker_size=4)
    fig.update_layout(
        plot_bgcolor="#f8f9fa", paper_bgcolor="#f8f9fa",
        legend=dict(font_size=9, itemsizing="constant"),
    )
    fig.write_html(str(out_path))
    print(f"  Saved → {out_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("Loading data …")
    X, cluster_ids, behaviors, id2label = load_data()
    print(f"  {len(behaviors)} behaviors, {len(id2label)} clusters.")

    xy = reduce_umap(X)

    print("Plotting …")
    plot_static(
        xy, cluster_ids, id2label,
        Path("data/normbank_clusters_umap.png"),
    )
    plot_interactive(
        xy, cluster_ids, behaviors, id2label,
        Path("data/normbank_clusters_umap.html"),
    )
    print("Done.")


if __name__ == "__main__":
    main()
