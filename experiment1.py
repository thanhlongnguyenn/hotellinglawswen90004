import multiprocessing
import log_utils
from simulation import Simulation


def experiment_one(params):
    """Experiment 1 test case runner for multiprocessing.

    Args:
        params (_type_): _description_

    Returns:
        _type_: _description_
    """

    run_id, max_ticks, num_store, rule, layout = params

    # Build simulation environment.
    sim = Simulation(
        number_of_stores=num_store,
        rules=rule,
        layout=layout,
    )

    # Execute test iteration.
    for _ in range(max_ticks):
        sim.step()
    print(f"Completed: Num stores: {num_store}, Layout: {layout}, Rule: {rule}")

    # Build results.
    state: dict = sim.export_state()
    results = [
        run_id,
        layout,
        num_store,
        rule,
        state["step"],
        log_utils.serialise_list(state["store-positions"]),
        log_utils.serialise_list(state["store-market-shares"]),
        log_utils.serialise_list(state["store-prices"]),
    ]
    return results


if __name__ == "__main__":
    """EXPERIMENT 1: Python Model Validation

    Number of stores: [2, 3, ..., 9, 10]
    Geographic Space: {"line", "plane"}
    Rules: {"normal", "pricing-only", "moving-only"}
    Max Ticks: 500
    """

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
            "ticks",
            "store-positions",
            "store-market-shares",
            "store-prices",
        ]
    )

    # Define test iterations.
    max_ticks: int = 500
    number_of_stores: range = range(2, 10, 1)
    geographic_space: set = {"line", "plane"}
    rules: set = {"normal", "pricing-only", "moving-only"}

    # Build test cases
    test_case: list[tuple] = []
    run_counter: int = 1
    for num_store in number_of_stores:
        for layout in geographic_space:
            for rule in rules:
                test_case.append((run_counter, max_ticks, num_store, layout, rule))

    try:
        # Run test cases on multiple cores.
        with multiprocessing.Pool() as pool:
            results = list(pool.imap_unordered(experiment_one, test_case))

        # Write logs to files
        for result in results:
            csv_writer.writerow(result)

    except KeyboardInterrupt:
        pass
    finally:
        csv_file.close()
