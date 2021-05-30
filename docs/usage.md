# Usage

## Example simulation

We have provided an example simulation to illustrate the results and introduce the construction of a custom maritime port simulation. The example simulation was built for the Port of Antwerp and based on **mock data** made manually using [geojson.io](https://geojson.io/), thus, of course, no real-life decisions can be discerned from this.

The example model has the following characteristics:

- Two vessel classes
- Three cargo types (dry bulk, chemicals, containers)
- Three berths. Each berth has two distinct ocean -> berth traces
- Two anchorage areas

When a vessel is generated, the simulation checks if some berth that can serve it is available. Specifically, it asks if the content can be processed there, if the size class can be handled, is the quay long enough and if the berth is deep enough for the vessel.

If the answer to any of these is no, then the vessel is sent to an anchorage to wait until a berth is available. If the answer to all of these is yes, the vessel proceeds to go to the assigned berth and is serviced there for a time sampled from service time distribution. Afterwards it goes back to the spawn point and leaves the simulation.
