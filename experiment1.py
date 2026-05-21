import csv
from datetime import datetime
from simulation import Simulation


def create_table_version_2_0_log_file(experiment_name: str):
    """Create a CSV file that is compatible with NetLogo Table Version 2.0.

    Returns:
        Tuple of (csv_file, csv_writer) where csv_file is the opened file object and
        csv_writer is the csv.writer object for writing to the file.
    """

    curr_time: datetime = datetime.now()

    # Create file and writer.
    filepath = f"{curr_time.strftime('%Y%m%d-%H%M%S')}_{experiment_name}.csv"
    csv_file = open(filepath, mode="w", newline="")
    csv_writer = csv.writer(csv_file)

    # Write header row.
    csv_writer.writerow(["Python Complex Model results", "Table version 2.0"])
    csv_writer.writerow(["Simulation.py"])
    csv_writer.writerow([experiment_name])
    csv_writer.writerow([f"{curr_time.isoformat()}"])

    return csv_file, csv_writer

def dump_list_to_table_version_2_0_format(a_list) -> str:
    """Convert a list to a string format compatible with NetLogo Table Version 2.0.

    Example:
        [[1, 2, 3], 2, 3] -> [[1 2 3] 2 3]
    """
    first_elem: bool = True
    out = "["

    for a in a_list:
        if isinstance(a, list):
            out += dump_list_to_table_version_2_0_format(a)
        else:
            if (not first_elem):
                out += " "
            out += str(a)
            first_elem = False

    out += "]"
    return out


def experiment_one():
    """EXPERIMENT 1: Python Model Validation

    Number of stores: [2, 3, ..., 9, 10]
    Geographic Space: {"line", "plane"}
    Rules: {"normal", "pricing-only", "moving-only"}
    Max Ticks: 500
    """

    # Initialise test logging file.
    csv_file, csv_writer = create_table_version_2_0_log_file("experiment1")
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
                    state:dict = sim.export_state()
                    csv_writer.writerow([
                        run_counter,
                        layout,
                        num_store,
                        rule,
                        state["step"],
                        dump_list_to_table_version_2_0_format(state["store-positions"]),
                        dump_list_to_table_version_2_0_format(state["store-market-shares"]),
                        dump_list_to_table_version_2_0_format(state["store-prices"]),
                    ])
    except KeyboardInterrupt:
        pass
    finally:
        csv_file.close()

if __name__ == "__main__":
    experiment_one()
