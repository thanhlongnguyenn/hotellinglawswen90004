import log_utils
from simulation import Simulation


def experiment_one():
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
    number_of_stores: range = range(2, 10, 1)
    geographic_space: set = {"line", "plane"}
    rules: set = {"normal", "pricing-only", "moving-only"}
    max_ticks: int = 500

    try:
        run_counter: int = 1
        for num_store in number_of_stores:
            for layout in geographic_space:
                for rule in rules:
                    # Build simulation environment.
                    sim = Simulation(
                        number_of_stores=num_store,
                        rules=rule,
                        layout=layout,
                    )

                    # Execute test iteration.
                    for _ in range(max_ticks):
                        sim.step()
                    print(
                        f"Completed: Num stores: {num_store}, Layout: {layout}, Rule: {rule}"
                    )

                    # Log results to CSV.
                    state: dict = sim.export_state()
                    csv_writer.writerow(
                        [
                            run_counter,
                            layout,
                            num_store,
                            rule,
                            state["step"],
                            log_utils.serialise_list(state["store-positions"]),
                            log_utils.serialise_list(state["store-market-shares"]),
                            log_utils.serialise_list(state["store-prices"]),
                        ]
                    )
    except KeyboardInterrupt:
        pass
    finally:
        csv_file.close()


if __name__ == "__main__":
    experiment_one()
