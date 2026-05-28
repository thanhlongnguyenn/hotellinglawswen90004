# Hotelling's Law

This repository contains a Python implementation of Hotelling's Law model from NetLogo, including an extension to support 'chains' of stores. This README explains how to set up the environment and run both experiments.

## Prerequisites

- NetLogo 7.0.3
- Python 3.14

## Experiment 1: Python Model Replication

In this experiment, we want to validate that the Python model accurately replicates the NetLogo model.

### NetLogo Model execution

The steps to execute the NetLogo model setup is as follows:

1. Open NetLogo version 7.0.3
2. Open the "Models Library" and select Hotelling's Law.
3. Open the "Behaviour Space", and import the experiment setup: `Hotelling's Law-Baseline-experiment.xml`
4. Run the experiment, and save the table output for post analysis.

### Python Model execution

The steps to execute the Python model component of the experiment is as follows:

1. Open a terminal, and navigate to the project's root folder.
2. Run the following command: `python experiment1.py`
3. Wait for the execution to complete. Please note that this took around 1 hour to complete on the machine that generated the results.

## Experiement 2: Chain Behaviour Extension

In this experiment, we want to investigate our hypothesis that if there is a chain with cnetral control of multiple stores, then the similarity between stores within a chain will decrease over time, and that stores within a chain will increase in similarity to its closes competitor.

The steps to execute the experiment is as follows:

1. Open a terminal, and navigate to the project's root folder.
2. Run the following command: `python experiment2.py`
3. Wait for the execution to complete.

## Notes about execution and outputs

The scripts use Python's `multiprocessing.Pool()` to parallelise test cases across available CPU cores. They will print progress messages such as `Created new log file at: <path>` and `Completed: ...` for each completed parameter combination.
