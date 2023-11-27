# TODO TITLE

Short description

## Content

The bash files can be used to run the attack graph generation and analysis on Windows (main.bat) and Linux (main.sh) systems.
Python scripts can be found in src\ folder. The main ones are the following:

- sampling.py (implements the sampling and statistics analyses)
- steering.py (implements the steerin mechanism)
- generation.py (implements the generation of the complete attack graph as ground truth)

Additionally, the following scripts have their own main functions to be executed individually, if necessary:

- main.py (implements the main logic of the whole approach StatAG and SteerAG in a multicore enviroment)
- plot_analysis.py (implements the charts for the analysis of StatAG and SteerAG)

## Configuration Parameters

The following parameters can be configured in the config.py file:

- SAMPLING algorithms between BFS, DFS, and Random Walks
- Number of SAMPLES for each iteration (default 100)
- Whether include the steering mechanism or not
- Additional parameters to control the accuracy among the different iterations

In addition, scalability parameters can be configured, such as:

- the number of cores on which run the system
- the number of repeated experiments to perform multiple experiments
- number of hosts, vulnerabilities, topology, and distribution of the synthetic networks to generate
- queries to consider for the analysis

## Prerequisites

The following python packages are required:

- pandas
- networkx
- matplotlib
- sklearn
- numpy
- pebble

## Installation Instructions

0. Unzip the file inventory.zip and put the folder named "inventory" inside src/ folder.

### Using Docker container:

1. Build the docker container in the main folder of the project
2. Inside the container, move inside the "src/" directory
3. Configure the file src/config.py
4. Launch the file main.py

```
python main.py
```

### Without Docker:

1. Configure the file src/config.py
2. Launch the bash file (main.bat for Windows, main.sh for Linux)

```
.\main.bat
```