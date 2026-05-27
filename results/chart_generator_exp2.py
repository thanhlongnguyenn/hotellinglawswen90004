import os
import re
import sys
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OUTPUT_DIRECTORY = "output/"
os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)

LAYOUTS = ["line", "plane"]
RULES = ["normal", "moving-only", "pricing-only"]
CONFIGS = ["4 Independent", "1 Chain (2-Store) + 2 Ind", "2 Chains (2x2)"]

# -----------------------------------------------------------------------------
# PARSING UTILITIES
# -----------------------------------------------------------------------------

def parse_position(s: str) -> dict[int, tuple[int, int]]:
    """Parses "[[0 10 20] [1 -5 2]]" -> {0: (10, 20), 1: (-5, 2)}"""
    matches = re.findall(r"\[([^\[\]]+)\]", s)
    return {int(g.split()[0]): (int(g.split()[1]), int(g.split()[2])) for g in matches}


def parse_price(s: str) -> dict[int, int]:
    """Parses "[[0 10] [1 12]]" -> {0: 10, 1: 12}"""
    matches = re.findall(r"\[([^\[\]]+)\]", s)
    return {int(g.split()[0]): int(g.split()[1]) for g in matches}


def parse_chains(s: str) -> dict[int, list[int]]:
    """Parses "[[0 -1] [1 -1]]" -> {-1: [0, 1]}"""
    if pd.isna(s) or s.strip() == "[]" or not s.strip():
        return {}
    matches = re.findall(r"\[([^\[\]]+)\]", s)
    chain_groups = {}
    for match in matches:
        parts = match.split()
        store_id, chain_id = int(parts[0]), int(parts[1])
        if chain_id not in chain_groups:
            chain_groups[chain_id] = []
        chain_groups[chain_id].append(store_id)
    return chain_groups


def identify_configuration(chain_str: str) -> str:
    """Classifies rows into the 3 Experiment 2 profiles."""
    groups = parse_chains(chain_str)
    if not groups:
        return "4 Independent"
    if len(groups) == 1:
        return "1 Chain (2-Store) + 2 Ind"
    return "2 Chains (2x2)"

# -----------------------------------------------------------------------------
# METRIC CALCULATIONS
# -----------------------------------------------------------------------------

def compute_chain_metrics(row) -> tuple[float, float]:
    """Calculates intra-chain distance and minimum competitor proximity."""
    pos_map = parse_position(row["store-positions"])
    chain_groups = parse_chains(row["store-chain-ids"])
    
    if not chain_groups:
        return np.nan, np.nan
    
    all_chain_stores = [sid for stores in chain_groups.values() for sid in stores]
    hostile_stores = [sid for sid in pos_map.keys() if sid not in all_chain_stores]
    
    intra_dists = []
    min_comp_dist = float('inf')
    
    for chain_id, store_ids in chain_groups.items():
        if len(store_ids) >= 2:
            for i in range(len(store_ids)):
                for j in range(i + 1, len(store_ids)):
                    p1, p2 = pos_map[store_ids[i]], pos_map[store_ids[j]]
                    intra_dists.append(np.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2))
                    
        for s_id in store_ids:
            p_curr = pos_map[s_id]
            for h_id in hostile_stores:
                p_hostile = pos_map[h_id]
                dist = np.sqrt((p_curr[0]-p_hostile[0])**2 + (p_curr[1]-p_hostile[1])**2)
                if dist < min_comp_dist:
                    min_comp_dist = dist
            for other_chain_id, other_store_ids in chain_groups.items():
                if other_chain_id != chain_id:
                    for o_id in other_store_ids:
                        p_rival = pos_map[o_id]
                        dist = np.sqrt((p_curr[0]-p_rival[0])**2 + (p_curr[1]-p_rival[1])**2)
                        if dist < min_comp_dist:
                            min_comp_dist = dist

    avg_intra = float(np.mean(intra_dists)) if intra_dists else np.nan
    final_min_comp = float(min_comp_dist) if min_comp_dist != float('inf') else np.nan
    
    return avg_intra, final_min_comp

# -----------------------------------------------------------------------------
# PLOTTING ENGINES
# -----------------------------------------------------------------------------

def plot_time_series_metrics(df: pd.DataFrame):
    """Generates the aggregated line charts."""
    print("Computing metrics and aggregating time-series data...")
    
    df["market_config"] = df["store-chain-ids"].apply(identify_configuration)
    metrics_res = df.apply(compute_chain_metrics, axis=1)
    df["avg_intra_chain_dist"] = [res[0] for res in metrics_res]
    df["min_competitor_dist"] = [res[1] for res in metrics_res]
    
    agg = df.groupby(["layout", "rules", "market_config", "[step]"], as_index=False)[
        ["avg_intra_chain_dist", "min_competitor_dist"]
    ].mean()

    targets = [
        ("avg_intra_chain_dist", "Mean Intra-Chain Spread Distance", "time_series_intra_chain_spread.png"),
        ("min_competitor_dist", "Minimum Distance to Competitor", "time_series_min_competitor_proximity.png")
    ]

    for column_key, ylabel, filename in targets:
        fig, axes = plt.subplots(2, 3, figsize=(16, 9))
        fig.suptitle(f"Evolution Tracking Profile: {ylabel} Over Time Ticks", fontsize=14, weight='bold')

        for r_idx, layout in enumerate(LAYOUTS):
            for c_idx, rule in enumerate(RULES):
                ax = axes[r_idx][c_idx]
                subset = agg[(agg["layout"] == layout) & (agg["rules"] == rule)]
                
                for config in CONFIGS:
                    config_data = subset[subset["market_config"] == config]
                    if config_data[column_key].dropna().empty:
                        continue
                    ax.plot(config_data["[step]"], config_data[column_key], label=config, linewidth=1.5)
                
                ax.set_title(f"Layout: {layout.upper()} | Strategy: {rule.upper()}", fontsize=9, weight='semibold')
                ax.set_xlabel("Ticks", fontsize=8)
                ax.set_ylabel(ylabel, fontsize=8)
                ax.grid(True, linestyle="--", alpha=0.5)
                ax.legend(fontsize=7, loc="best")

        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIRECTORY, filename), dpi=200)
        print(f"Saved Metric Chart: {OUTPUT_DIRECTORY}{filename}")
        plt.close()


def plot_spatial_trajectories(df: pd.DataFrame):
    """Maps full time-series movements by grouping matching configuration scenarios safely."""
    print("Generating complete time-series spatial trajectory maps...")
    
    df["market_config"] = df["store-chain-ids"].apply(identify_configuration)
    
    # Group data by layout, rule, and config combination
    grouped = df.groupby(["layout", "rules", "market_config"])
    
    independent_colors = ["#FF5733", "#33FF57", "#3357FF", "#FFD700"]
    corporate_colors = {-1: "#000000", -2: "#FF7F0E"}

    for (layout, rule, config), group in grouped:
        # Use the first run for each configuration
        min_run = group["[run number]"].min()
        scenario_run = group[group["[run number]"] == min_run].sort_values(by="[step]")
        
        fig, ax = plt.subplots(figsize=(7, 7))
        store_histories = {}
        
        for _, row in scenario_run.iterrows():
            tick = int(row["[step]"])
            pos_map = parse_position(row["store-positions"])
            chain_groups = parse_chains(row["store-chain-ids"])
            
            for s_id, (x, y) in pos_map.items():
                if s_id not in store_histories:
                    assigned_chain = next((c_id for c_id, stores in chain_groups.items() if s_id in stores), None)
                    store_histories[s_id] = {"x": [], "y": [], "tick": [], "chain_id": assigned_chain}
                
                store_histories[s_id]["x"].append(x)
                store_histories[s_id]["y"].append(y)
                store_histories[s_id]["tick"].append(tick)

        # Plot each store's path history on the canvas
        for s_id, s_data in store_histories.items():
            ticks = np.array(s_data["tick"])
            x_vals = np.array(s_data["x"])
            y_vals = np.array(s_data["y"])
            chain_id = s_data["chain_id"]
            
            if chain_id is not None:
                base_color = corporate_colors.get(chain_id, "#7F7F7F")
                label = f"Chain {int(chain_id)} (Store {s_id})"
            else:
                base_color = independent_colors[s_id % len(independent_colors)]
                label = f"Independent Store {s_id}"

            # Line layout: y-axis indicates progression of time
            if layout == "line":
                ax.plot(y_vals, ticks, color=base_color, linewidth=2, label=label)
                ax.scatter(y_vals[0], ticks[0], color=base_color, s=60, marker="o", edgecolors='black', zorder=4)
                ax.scatter(y_vals[-1], ticks[-1], color=base_color, s=80, marker="^", edgecolors='black', zorder=4)
                
                ax.set_xlabel("Spatial Position (Y-Coordinate)", fontsize=9)
                ax.set_ylabel("Time Passing (Ticks)", fontsize=9)
                ax.set_xlim(-22, 22)
                ax.set_ylim(0, max(500, ticks.max()))

            # Plane layout: use colour shading to indicate progression of time
            else:
                ax.plot(x_vals, y_vals, color=base_color, alpha=0.3, linewidth=1.5, zorder=2)
                
                # Apply fading sequentially across steps
                max_t = ticks.max() if ticks.max() > 0 else 1
                alphas = (ticks / float(max_t)) * 0.9 + 0.1
                
                for idx in range(len(ticks)):
                    ax.scatter(x_vals[idx], y_vals[idx], color=base_color, alpha=alphas[idx], s=12, zorder=3)
                
                ax.scatter(x_vals[-1], y_vals[-1], color=base_color, s=120, marker="X", edgecolors='black', zorder=5, label=f"{label} (Final Equilibrium)")
                
                ax.set_xlabel("X Coordinate", fontsize=9)
                ax.set_ylabel("Y Coordinate", fontsize=9)
                ax.set_xlim(-22, 22)
                ax.set_ylim(-22, 22)
                ax.axhline(0, color='black', linewidth=0.5, linestyle=':')
                ax.axvline(0, color='black', linewidth=0.5, linestyle=':')

        ax.set_title(f"{config}\nLayout: {layout.upper()} | Rule: {rule.upper()} (Full Timeline Path)", fontsize=10, weight='bold')
        ax.grid(True, linestyle="--", alpha=0.3)
        ax.legend(fontsize=7, loc="lower right" if layout == "plane" else "best")
        
        clean_name = f"trajectory_map_{config.split()[0]}_{layout}_{rule}.png".lower()
        plt.savefig(os.path.join(OUTPUT_DIRECTORY, clean_name), dpi=150)
        plt.close()
        print(f"Saved Trajectory Map: {OUTPUT_DIRECTORY}{clean_name}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("To run: python chart_generator_exp2.py <your_experiment2_csv>")
        sys.exit(1)
        
    csv_path = sys.argv[1]
    print(f"Reading target log data file: {csv_path}...")
    
    raw_df = pd.read_csv(csv_path, skiprows=6)
    
    plot_time_series_metrics(raw_df)
    plot_spatial_trajectories(raw_df)
    
    print("\nDone.")
