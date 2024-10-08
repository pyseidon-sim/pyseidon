# PySeidon - A Data-Driven Maritime Port Simulator 🌊 

<img src="docs/images/preview.jpg" alt="Image of the simulation software" width="1000"/>

Extendable and modular software for maritime port simulation. Read our [paper](https://dl.acm.org/doi/abs/10.1145/3474963.3474986). 

This software uses [entity-component system](https://en.wikipedia.org/wiki/Entity_component_system) approach making it highly customizable for various end goals and easily built upon.

## Overview

PySeidon was primarily designed for port scenario testing, but can be used for a variety of other tasks. Software can be adapted to simulate any maritime port provided that the [required data is available](https://pyseidon-sim.github.io/pyseidon/data/).
The simulator can be tested with different factors, such as:
- New/different anchorage location
- Different number of tugboat/pilots available
- Different priority order depending on ship class/size
- Etc...

PySeidon's output can then give useful insights whether the given change improves certain Key Performance Indicators (check [this repository](https://gitlab.com/pyseidon/ais-tools) for scripts to analyse simulation results).

PySeidon can be used to create new data for various downstream tasks (e.g. anomaly detection), approximate impact on Key Performance Indicators of some decision, novelty introduced in a port.
The supplemental visualization software can be used to analyse general (or created by simulation) [AIS data over time](https://gitlab.com/pyseidon/ais-visualization) or [analyse simulation states](https://gitlab.com/pyseidon/simulator-flow-analysis) (for debugging).

## Installation and Demo

The framework is bundled with an example model to get you started. To run it first install the dependencies by running `pip install -r requirements.txt`. Pip might complain about `libgeos` not being installed on your system. On Ubuntu you can install it by running `sudo apt-get install libgeos-dev`.

Once the required libraries are installed run the example model with the following command (it may take a bit for the first vessel to spawn)

```sh
python main.py          \
    --out sim-output    \
    --step 10           \
    --verbose y         \
    --graphics y        \
    --cache y           \
    --seed 567
```

## Features

- Simulation of the following agents and infrastructure elements
  - Agents: vessel, tugboats, pilots
  - Infrastructure components: berths, anchorages, tugboat rendezvous and storage locations, pilot rendezvous and storage locations
  - Introduction of anomalies such as randomized berth inspections, tugboat malfunctions, anomalous vessel velocity. These can be used to create
  datasets that are currently not available
- Visualization of the simulation: infrastructure components and agents, including an overview of vessel and berth information at any moment in time
- Simulation of anomalies: random berth inspection, tugboat malfunctions, unusual vessel velocities
- Clean way of conducting experiments of the simulation (multiple runs, no graphics, aggregating output data of the simulation)
- The simulation engine relies on the input data, minimal actual code modification (model and `main.py`) is required to adapt to different maritime ports if no additional features are to be implemented


## Documentation

For detailed instructions how to install and use PySeidon, see the [Documentation](https://pyseidon-sim.github.io/pyseidon/).

## Citation

If you use this repository in your work, please cite it as 
```
@inproceedings{10.1145/3474963.3474986,
author = {Skaisgiris, Paulius and Simoncini, Walter and Barbero, Fabio and Ahangi, Amir and Mockel, Rico},
title = {PySeidon - A Data-Driven Maritime Port Simulation Framework},
year = {2021},
isbn = {9781450389792},
publisher = {Association for Computing Machinery},
address = {New York, NY, USA},
url = {https://doi.org/10.1145/3474963.3474986},
doi = {10.1145/3474963.3474986},
abstract = {Due to a continuous increase in the amount of goods transported via water in the world, ports have become places of high maritime vessel traffic density. Because of this, the complexity of ports as systems has increased. Ports are pressured to constantly invest and to improve policies to increase the ports’ efficiency while maintaining a high level of safety and robustness. Proposed policies can be tested using simulation in a cost effective and safe way, but there is a lack of freely available, open-source harbour simulators for research and policy testing. In this paper, we present PySeidon, an open-source, modular, and generic port simulation framework written in Python. A proof-of-concept model of the Port of Rotterdam has been developed in PySeidon. We demonstrate the usefulness of this framework by performing scenario testing and comparing normal and anomalous agent behavior as well as two tugboat company policies with the model of the Port of Rotterdam.},
booktitle = {Proceedings of the 13th International Conference on Computer Modeling and Simulation},
pages = {164–171},
numpages = {8},
keywords = {Computer Simulation, Maritime Port Modelling, Open-Source, Port of Rotterdam},
location = {Melbourne, VIC, Australia},
series = {ICCMS '21}
}
```

## Future work

- Various external factors such as weather, tide, etc.  
- Implement proper nautical rules
- Loading simulation from a saved state
- GUI to enable non-experts be able to use the software
- Boatmen agent
- Better vessel acceleration model, PID controller
- Automatic data analysis at the end of simulation
