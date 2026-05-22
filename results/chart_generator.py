import matplotlib as plt
import pandas as pd
import sys


if __name__ == "__main__":
    # Read command line arguments
    if len(sys.argv) != 2:
        raise RuntimeError("Invalid number of command line arguments, need filepath!")
    filepath: str = sys.argv[1]  # sys.argv[0] is the script name

    # Load in dataset
    df = pd.read_csv(filepath, skiprows=6, header="infer")
    print(df.head(10))

    # TODO: Calculate sum of pairwise distance for each step in each run

    # TODO: Calculate sum of pairwise difference in price for each step in each run

    # TODO: Average metrics for distance and price difference for each test case
    # (i.e. aggregate the 20 runs for the test case)

    # TODO: Plot graphs (thinking grey lines to represent the specific run results
    # over time, and then the average metrics in a different colour that pops.

