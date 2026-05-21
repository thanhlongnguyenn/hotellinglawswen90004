"""
Table Version 2.0 logging utilities.
"""

import csv
from datetime import datetime

def create_log_file(experiment_name: str):
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
    print(f"Created new log file at: {filepath}")

    # Write header row.
    csv_writer.writerow(["Python Complex Model results", "Table version 2.0"])
    csv_writer.writerow(["Simulation.py"])
    csv_writer.writerow([experiment_name])
    csv_writer.writerow([f"{curr_time.isoformat()}"])

    return csv_file, csv_writer

def serialise_list(a_list) -> str:
    """Convert a list to a string format compatible with NetLogo Table Version 2.0.

    Example:
        [[1, 2, 3], 2, 3] -> [[1 2 3] 2 3]
    """
    first_elem: bool = True
    out = "["

    for a in a_list:
        if isinstance(a, list):
            out += serialise_list(a)
        else:
            if (not first_elem):
                out += " "
            out += str(a)
            first_elem = False

    out += "]"
    return out