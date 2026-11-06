"""Overview figure across batches (replicating injection only): two side-by-side panels.
Left: downstream hijack rate; right: legitimate task success. Points = proportion, bars = Wilson 95% CI.
Usage: python scripts/overview_figure.py  -> results/overview.png + results/overview.csv"""
import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from analyze import wilson  # noqa: E402

BATCHES = [  # label, directory, condition-name prefix
    ("Main", "main_mistral-small-2603", "replicating"),
    ("R (replication)", "replication_mistral-small-2603", "replicating"),
    ("N (native tools)", "native_mistral-small-2603", "replicating"),
    ("T (shared board)", "board_mistral-small-2603", "replicating"),
    ("A: sanitizer_bypass", "adversarial_mistral-small-2603", "sanitizer_bypass"),
    ("M (GPT agents)", "model_gpt-5.4-mini", "replicating"),
]
MODES = [("none", "No monitor", "#2a78d6"), ("llm", "Block", "#eb6834"), ("sanitize", "Sanitize", "#1baf7a")]


def rows():
    out = []
    for label, d, pre in BATCHES:
        path = os.path.join(ROOT, "results", d, "episodes.jsonl")
        if not os.path.exists(path):
            continue
        recs = [json.loads(line) for line in open(path)]
        for mode, mlab, _ in MODES:
            S = [r["summary"] for r in recs if r["config"]["condition"] == f"{pre}_{mode}" and r["summary"]["completed"]]
            if not S:
                continue
            n = len(S)
            out.append({"batch": label, "mode": mlab, "n": n,
                        **{f"down_{k}": v for k, v in zip("plh", wilson(sum(s["n_hijacked_downstream"] > 0 for s in S), n))},
                        **{f"task_{k}": v for k, v in zip("plh", wilson(sum(s["task_success"] for s in S), n))}})
    return out


def main():
    R = rows()
    with open(os.path.join(ROOT, "results", "overview.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(R[0]))
        w.writeheader()
        w.writerows(R)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ink, ink2, surface, grid = "#0b0b0b", "#52514e", "#fcfcfb", "#e4e3df"
    batches = [b for b, _, _ in BATCHES if any(r["batch"] == b for r in R)]
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 0.42 * len(batches) + 1.4), dpi=200, sharey=True, facecolor=surface)
    for ax, key, title in ((axes[0], "down", "Downstream agent hijacked"), (axes[1], "task", "Legitimate task success")):
        ax.set_facecolor(surface)
        for j, (_, mlab, col) in enumerate(MODES):
            labeled = False
            for i, b in enumerate(batches):
                r = next((r for r in R if r["batch"] == b and r["mode"] == mlab), None)
                if r is None:
                    continue
                y = i + (j - 1) * 0.24
                ax.plot([r[f"{key}_l"], r[f"{key}_h"]], [y, y], color=col, linewidth=1.5, solid_capstyle="round")
                ax.plot(r[f"{key}_p"], y, "o", color=col, markersize=5, markeredgecolor=surface, markeredgewidth=1,
                        label=None if labeled else mlab)
                labeled = True
        ax.set_xlim(-0.03, 1.03)
        ax.set_title(title, fontsize=8, color=ink, loc="left")
        ax.tick_params(axis="x", labelsize=7, colors=ink2)
        ax.grid(axis="x", color=grid, linewidth=0.6)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color("#c9c8c2")
    axes[0].set_yticks(range(len(batches)), batches, fontsize=7, color=ink)
    axes[0].invert_yaxis()
    axes[0].set_xlabel("Proportion of episodes (n = 30, Wilson 95% CI)", fontsize=7, color=ink2)
    axes[1].set_xlabel("Proportion of episodes (n = 30, Wilson 95% CI)", fontsize=7, color=ink2)
    axes[1].legend(fontsize=7, frameon=False, loc="lower left", bbox_to_anchor=(0, 1.08), ncol=3)
    fig.tight_layout()
    fig.savefig(os.path.join(ROOT, "results", "overview.png"), facecolor=surface)
    print(f"wrote results/overview.png ({len(R)} rows)")


if __name__ == "__main__":
    main()
