import multiprocessing
import log_utils
from simulation import run_simulation_experiment
import random

if __name__ == "__main__":
    """EXPERIMENT 2: Chain Behaviour Extension

    Number of runs: 30
    Total stores per simulation: Fixed at 4
    Configurations:
        1. 4 independent stores
        2. 1 chain of 2 stores and 2 independent stores
        3. 2 chains of 2 stores
    Geographic Space: {"line", "plane"}
    Rules: {"normal", "pricing-only", "moving-only"}
    Max Ticks: 500
    """
    # Set random seed for repeatability.
    random.seed(42)

    # Initialise test logging file.
    csv_file, csv_writer = log_utils.create_log_file("experiment2")
    csv_writer.writerow(["min-pxcor", "max-pxcor", "min-pycor", "max-pycor"])
    csv_writer.writerow(["-20", "20", "-20", "20"])
    csv_writer.writerow(
        [
            "[run number]",
            "layout",
            "number-of-stores",
            "rules",
            "[step]",
            "store-positions",
            "store-market-shares",
            "store-prices",
            "store-chain-ids",
        ]
    )

    # Define test iterations.
    max_ticks: int = 500
    number_of_runs: range = range(30)
    geographic_space: set = {"line", "plane"}
    rules: set = {"normal", "pricing-only", "moving-only"}
    configurations = [
        {"num_stores": 4, "mode": "store", "num_chains": 0, "chain_allocations": []},
        {"num_stores": 4, "mode": "chain", "num_chains": 1, "chain_allocations": [2]},
        {
            "num_stores": 4,
            "mode": "chain",
            "num_chains": 2,
            "chain_allocations": [2, 2],
        },
    ]

    # Build test cases
    test_cases: list[tuple] = []
    run_counter: int = 1

    for run in number_of_runs:
        for config in configurations:
            for layout in geographic_space:
                for rule in rules:
                    test_cases.append(
                        (
                            run_counter,
                            max_ticks,
                            config["num_stores"],
                            layout,
                            rule,
                            config["num_chains"],
                            config["mode"],
                            config["chain_allocations"],
                        )
                    )
                    run_counter += 1

    try:
        # Run test cases on multiple cores.
        with multiprocessing.Pool() as pool:
            results = list(pool.imap_unordered(run_simulation_experiment, test_cases))

        # Write logs sequentially back down to disk
        for result in results:
            for entry in result:
                csv_writer.writerow(entry)

    except KeyboardInterrupt:
        pass
    finally:
        csv_file.close()
