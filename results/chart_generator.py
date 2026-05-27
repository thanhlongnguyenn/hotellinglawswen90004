import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import sys
import os
import re

output_directory = "output/"
os.makedirs(output_directory, exist_ok=True)

LAYOUTS = ["line", "plane"]
RULES = ["normal", "moving-only", "pricing-only"]
STORE_COUNTS = list(range(2, 11))


def parse_position(s: str) -> list[tuple[int, int]]:
    return [(int(g.split()[1]), int(g.split()[2])) for g in re.findall(r"\[([^\[\]]+)\]", s)]


def parse_price(s: str) -> list[int]:
    return [int(g.split()[1]) for g in re.findall(r"\[([^\[\]]+)\]", s)]


def avg_pairwise_distance(positions: list[tuple[int, int]]) -> float:
    dists = [
        np.sqrt((positions[i][0] - positions[j][0]) ** 2 + (positions[i][1] - positions[j][1]) ** 2)
        for i in range(len(positions))
        for j in range(i + 1, len(positions))
    ]
    return float(np.mean(dists)) if dists else 0.0


def avg_pairwise_price_diff(prices: list[int]) -> float:
    diffs = [abs(prices[i] - prices[j]) for i in range(len(prices)) for j in range(i + 1, len(prices))]
    return float(np.mean(diffs)) if diffs else 0.0


def compute_metrics(df: pd.DataFrame, position_col: str, price_col: str) -> pd.DataFrame:
    df = df.copy()
    df["avg_pairwise_dist"] = df[position_col].apply(lambda s: avg_pairwise_distance(parse_position(s)))
    df["avg_price_diff"] = df[price_col].apply(lambda s: avg_pairwise_price_diff(parse_price(s)))
    return df


def aggregate_metrics(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["layout", "rules", "number-of-stores", "[step]"], as_index=False)
        [["avg_pairwise_dist", "avg_price_diff"]]
        .mean()
    )


def plot_experiment1(agg: pd.DataFrame, source_label: str):
    for metric, ylabel in [("avg_pairwise_dist", "Avg Pairwise Distance"), ("avg_price_diff", "Avg Pairwise Price Diff")]:
        fig, axes = plt.subplots(2, 3, figsize=(15, 8), sharey=False)
        fig.suptitle(f"{source_label} — {ylabel} (Experiment 1)")

        for row, layout in enumerate(LAYOUTS):
            for col, rule in enumerate(RULES):
                ax = axes[row][col]
                subset = agg[(agg["layout"] == layout) & (agg["rules"] == rule)]
                for n in STORE_COUNTS:
                    run_data = subset[subset["number-of-stores"] == n]
                    ax.plot(run_data["[step]"], run_data[metric], label=f"{n} stores")
                ax.set_title(f"{layout} / {rule}")
                ax.set_xlabel("Step")
                ax.set_ylabel(ylabel)
                ax.legend(fontsize=6)

        plt.tight_layout()
        filename = f"{source_label.lower().replace(' ', '_')}_{metric}.png"
        plt.savefig(os.path.join(output_directory, filename))
        print(f"Saved: {filename}")
        plt.close()


def plot_comparison(py_agg: pd.DataFrame, nl_agg: pd.DataFrame):
    for metric, ylabel in [("avg_pairwise_dist", "Avg Pairwise Distance"), ("avg_price_diff", "Avg Pairwise Price Diff")]:
        fig, axes = plt.subplots(2, 3, figsize=(15, 8), sharey=False)
        fig.suptitle(f"Python vs NetLogo — {ylabel}")

        for row, layout in enumerate(LAYOUTS):
            for col, rule in enumerate(RULES):
                ax = axes[row][col]
                for n in STORE_COUNTS:
                    py_data = py_agg[(py_agg["layout"] == layout) & (py_agg["rules"] == rule) & (py_agg["number-of-stores"] == n)]
                    nl_data = nl_agg[(nl_agg["layout"] == layout) & (nl_agg["rules"] == rule) & (nl_agg["number-of-stores"] == n)]
                    ax.plot(py_data["[step]"], py_data[metric], color="steelblue", alpha=0.6, linewidth=0.8)
                    ax.plot(nl_data["[step]"], nl_data[metric], color="darkorange", alpha=0.6, linewidth=0.8)
                ax.set_title(f"{layout} / {rule}")
                ax.set_xlabel("Step")
                ax.set_ylabel(ylabel)

        # shared legend
        handles = [
            plt.Line2D([0], [0], color="steelblue", label="Python"),
            plt.Line2D([0], [0], color="darkorange", label="NetLogo"),
        ]
        fig.legend(handles=handles, loc="lower center", ncol=2)
        plt.tight_layout(rect=(0, 0.05, 1, 1))
        filename = f"comparison_{metric}.png"
        plt.savefig(os.path.join(output_directory, filename))
        print(f"Saved: {filename}")
        plt.close()

def plot_diff(py_agg: pd.DataFrame, nl_agg: pd.DataFrame):
    diff_agg = pd.merge(py_agg, nl_agg, on=["layout", "rules", "number-of-stores", "[step]"], suffixes=["_py", "_nl"])
    diff_agg["diff_avg_pairwise_dist"] = diff_agg["avg_pairwise_dist_nl"] - diff_agg["avg_pairwise_dist_py"]
    diff_agg["diff_avg_price_diff"] = diff_agg["avg_price_diff_nl"] - diff_agg["avg_price_diff_py"]

    for metric, ylabel in [("diff_avg_pairwise_dist", "Avg Pairwise Distance Difference"), ("diff_avg_price_diff", "Avg Pairwise Price Diff Difference")]:
        fig, axes = plt.subplots(2, 3, figsize=(15, 8), sharey=False)
        fig.suptitle(f"Python vs NetLogo — {ylabel}")

        for row, layout in enumerate(LAYOUTS):
            for col, rule in enumerate(RULES):
                ax = axes[row][col]
                for n in STORE_COUNTS:
                    diff_data = diff_agg[(diff_agg["layout"] == layout) & (diff_agg["rules"] == rule) & (diff_agg["number-of-stores"] == n)]
                    ax.plot(diff_data["[step]"], diff_data[metric], label=f"{n} stores", alpha=0.5, linewidth=0.8)
                ax.set_title(f"{layout} / {rule}")
                ax.set_xlabel("Step")
                ax.set_ylabel(ylabel)
                ax.legend(fontsize=6)

        # shared legend
        plt.tight_layout()
        filename = f"comparison_{metric}.png"
        plt.savefig(os.path.join(output_directory, filename))
        print(f"Saved: {filename}")
        plt.close()

if __name__ == "__main__":
    # Read command line arguments
    if len(sys.argv) != 3:
        raise RuntimeError("To run: python chart_generator.py <python_csv> <netlogo_csv>")
    python_filepath: str = sys.argv[1]
    netlogo_filepath: str = sys.argv[2]

    # Load datasets
    py_df = pd.read_csv(python_filepath, skiprows=6)
    nl_df = pd.read_csv(netlogo_filepath, skiprows=6)

    # Compute pairwise metrics
    print("Computing Python metrics...")
    py_df = compute_metrics(py_df, "store-positions", "store-prices")

    print("Computing NetLogo metrics...")
    nl_df = compute_metrics(nl_df, "[(list who xcor ycor)] of turtles", "[(list who price)] of turtles")

    # Average across runs per (layout, rules, number-of-stores, step)
    py_agg = aggregate_metrics(py_df)
    nl_agg = aggregate_metrics(nl_df)

    # Plot experiment 1 graphs (per source)
    plot_experiment1(py_agg, "Python")
    plot_experiment1(nl_agg, "NetLogo")

    # Plot Python vs NetLogo comparison
    plot_comparison(py_agg, nl_agg)
    plot_diff(py_agg, nl_agg)

    print("Done.")
