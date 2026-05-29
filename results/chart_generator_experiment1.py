import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import sys
import os
import re

output_directory = "output/experiment-1/"
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
        fig.suptitle(f"{source_label} Model: {ylabel} Over Time Ticks", fontsize=14, weight='bold')

        for row, layout in enumerate(LAYOUTS):
            for col, rule in enumerate(RULES):
                ax = axes[row][col]
                subset = agg[(agg["layout"] == layout) & (agg["rules"] == rule)]
                for n in STORE_COUNTS:
                    run_data = subset[subset["number-of-stores"] == n]
                    ax.plot(run_data["[step]"], run_data[metric], label=f"{n} stores")
                ax.set_title(f"Layout: {layout.upper()} | Rule: {rule.upper()}", fontsize=9, weight='semibold')
                ax.set_xlabel("Step")
                ax.set_ylabel(ylabel)
                ax.grid(True, linestyle="--", alpha=0.5)
                ax.legend(fontsize=7, loc="best")

        plt.tight_layout()
        filename = f"{source_label.lower().replace(' ', '_')}_{metric}.png"
        plt.savefig(os.path.join(output_directory, filename))
        print(f"Saved: {filename}")
        plt.close()


def plot_comparison(py_agg: pd.DataFrame, nl_agg: pd.DataFrame):
    for metric, ylabel in [("avg_pairwise_dist", "Avg Pairwise Distance"), ("avg_price_diff", "Avg Pairwise Price Diff")]:
        fig, axes = plt.subplots(2, 3, figsize=(15, 8), sharey=False)
        fig.suptitle(f"NetLogo vs Python: {ylabel} Over Time Ticks", fontsize=14, weight='bold')

        for row, layout in enumerate(LAYOUTS):
            for col, rule in enumerate(RULES):
                ax = axes[row][col]
                for n in STORE_COUNTS:
                    py_data = py_agg[(py_agg["layout"] == layout) & (py_agg["rules"] == rule) & (py_agg["number-of-stores"] == n)]
                    nl_data = nl_agg[(nl_agg["layout"] == layout) & (nl_agg["rules"] == rule) & (nl_agg["number-of-stores"] == n)]
                    ax.plot(py_data["[step]"], py_data[metric], color="steelblue", alpha=0.6, linewidth=1.0)
                    ax.plot(nl_data["[step]"], nl_data[metric], color="darkorange", alpha=0.6, linewidth=1.0)
                ax.set_title(f"Layout: {layout.upper()} | Rule: {rule.upper()}", fontsize=9, weight='semibold')
                ax.set_xlabel("Step")
                ax.set_ylabel(ylabel)
                ax.grid(True, linestyle="--", alpha=0.5)

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

    for metric, ylabel in [("diff_avg_pairwise_dist", "Difference in Avg Pairwise Distance"), ("diff_avg_price_diff", "Difference in Avg Pairwise Price Diff")]:
        fig, axes = plt.subplots(9, 2, figsize=(8, 10), sharex='col', sharey=False)
        fig.suptitle(f"NetLogo vs Python: {ylabel} Over Time Ticks", fontsize=14, weight='bold')
        fig.supylabel(ylabel)

        for row, n in enumerate(STORE_COUNTS):
            for col, layout in enumerate(LAYOUTS):
                # Define axes
                ax = axes[row][col]
                ax.axhline(0, color='black', alpha=0.5, linestyle='-') 
                ax.set_ylim(-3, 3)
                ax.set_xlim(0, 500)
                ax.set_title(f"Layout: {layout.upper()} | Num Stores: {n}", fontsize=9, weight='semibold')

                # Plot data
                diff_data = diff_agg[(diff_agg["layout"] == layout) & (diff_agg["number-of-stores"] == n)]
                normal_data = diff_data[diff_data["rules"] == "normal"]
                ax.plot(normal_data["[step]"], normal_data[metric], label="normal", linewidth=1.0, color="steelblue")
                ax.grid(True, linestyle="--", alpha=0.5)
                if metric == "diff_avg_pairwise_dist":
                    moving_only_data = diff_data[diff_data["rules"] == "moving-only"]
                    ax.plot(moving_only_data["[step]"], moving_only_data[metric], label="moving-only", linewidth=1.0, color="darkorange")
                    ax.grid(True, linestyle="--", alpha=0.5)
                if metric == "diff_avg_price_diff":
                    pricing_only_data = diff_data[diff_data["rules"] == "pricing-only"]
                    ax.plot(pricing_only_data["[step]"], pricing_only_data[metric], label="pricing-only", linewidth=1.0, color="darkgreen")
                    ax.grid(True, linestyle="--", alpha=0.5)

                if (n == 10):
                    ax.set_xlabel("Step")

        # shared legend
        handles = []
        handles.append(plt.Line2D([0], [0], color="steelblue", label="normal"))
        if metric == "diff_avg_pairwise_dist":
            handles.append(plt.Line2D([0], [0], color="darkorange", label="moving-only"))
        if metric == "diff_avg_price_diff":
            handles.append(plt.Line2D([0], [0], color="darkgreen", label="pricing-only"))
        fig.legend(handles=handles, loc="lower center", ncol=2)
        plt.tight_layout(rect=(0, 0.05, 1, 1))
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
