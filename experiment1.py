import multiprocessing
import log_utils
from simulation import run_simulation_experiment
import random

if __name__ == "__main__":
    """EXPERIMENT 1: Python Model Replication

    Number of runs: 20
    Number of stores: [2, 3, ..., 9, 10]
    Geographic Space: {"line", "plane"}
    Rules: {"normal", "pricing-only", "moving-only"}
    Max Ticks: 500
    """
    # Set random seed for repeatability.
    random.seed(42)

    # Initialise test logging file.
    csv_file, csv_writer = log_utils.create_log_file("experiment1")
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
    number_of_runs: range = range(20)
    number_of_stores: range = range(2, 11, 1)
    geographic_space: set = {"line", "plane"}
    rules: set = {"normal", "pricing-only", "moving-only"}

    # Build test cases
    test_case: list[tuple] = []
    run_id: int = 1
    for run in number_of_runs:
        for num_store in number_of_stores:
            for layout in geographic_space:
                for rule in rules:
                    test_case.append(
                        (run_id, max_ticks, num_store, layout, rule, 0, "store", [])
                    )
                    run_id += 1

    try:
        # Run test cases on multiple cores.
        with multiprocessing.Pool() as pool:
            results = list(pool.imap_unordered(run_simulation_experiment, test_case))

        # Write logs to files
        for result in results:
            for entry in result:
                csv_writer.writerow(entry)

    except KeyboardInterrupt:
        pass
    finally:
        csv_file.close()
