# Simulation Architecture

The simulation framework is based on the ESC [Esper](https://github.com/benmoran56/esper). This ECS system consists of the following elements:

- **Entities**: labels that represent simulated entities (vessels, berths, etc.). They have no properties or methods. Components provide properties and processors provide method implementations
- **Components**: data objects (such as position, velocity, etc.). They should **NOT** include any method or computation
- **Processors**: classes that process a set of entities identified by their components. For example a vessel entity might be characterized by a position, velocity and vessel_info components

Please refer to the official Esper [documentation](https://github.com/benmoran56/esper) for learning more.

## Packages

The simulation framework is divided in the following packages:

### Components

Contains data and finite state machines components for vessels and berths.

### Processors

Contains the classes that interact directly with the simulation, such as generators (e.g. vessel generation), renderers etc.

Following a reference of the main processors

##### VesselGeneratorProcessor

Generates new vessels provided an inter-arrival time distribution and a user-provided vessel properties generator, that generates vessel length, width, etc. (see `VesselInfo` for details)

```python
    VesselGeneratorProcessor(
        # Simulation world
        world,
        # The inter-arrival time distribution
        lambda: np.random.exponential(scale=1),
        # The vessel properties generator
        lambda: return VesselInfo(...))
```

##### Renderers

These components take care of rendering entities on-screen

##### Timer Processor

This processor is in charge of advancing the currently scheduled timer's internal clock

##### Movement processor

This processor simulates the vessel movement, currently using a simple fixed speed based model. 

##### Vessel Goal Formulator

This processor insructs incoming vessels on their next goal, such as selecting and navigating to a target berth or departing.

### Environment

This package wraps the packages used for interacting with the environment. The current packages are:

##### Initializers

Contains one-shot generation processed, used for setting up the simulation

##### Navigation

Contains classes used for generating vessel (or tugboats, etc.) paths

##### Queries

Contains utility functions and classes for fetching entities from the simulation world

### Layers

This package contains layers used for the visualization but rendering code should be added via renderer processors.

### Model

This package contains model-specific code that is **FORBIDDEN** from being used in other parts of the simulator. Instead model specific code should be injected to the consumer classes. For a practical example consider the `VesselGeneratorProcessor`. This class accepts two functions, one that generates an inter arrival time and one that generates the vessel properties:

```python
vessel_generator = VesselGeneratorProcessor(
    world,
    lambda: np.random.exponential(scale=15.0) * SECONDS_IN_MINUTE,
    lambda: VesselInfo(...))
```

This allow the `VesselGeneratorProcessor` to be model-agnostic and reusable.

**Note:** some model-specific code is currently used by framework classes, this should be addressed.

### Utils

Package for storing utilities functions and classes. The sub-package `timer` contains a `SimulationTimer` class that is used for dispatching future events and accepts a duration in seconds and a `TimerScheduler` singleton that is used to add timers to the simulation. Timers can be scheduled using the following code:

```python
timer = SimulationTimer(
    duration=1000,
    # The function to be executed after the timer has completed
    target_function=lambda: ...) 

TimerScheduler.get_instance().schedule(timer)
```