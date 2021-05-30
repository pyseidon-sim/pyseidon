# Required data

A detailed description of the datasets and their formats is presented after this section. The bare minimum data required to run the port simulation is the following (see the example model for further information):

- Definition of different vessel size classes and their parameters as well as different vessel content types. See `vessel_class.py`, `vessel_content_type.py`, `vessel_type.py`, `vessel_distribution_factory.py` in `example_model`.
- Polygons of sections of the port. See `sections.geojson` in `example_data`.
- Locations and parameters of berths. See `berths.csv` in `example_data`.
- The polygons of anchorages. See `anchorages.geojson` in `example_data`.
- Spawn areas of vessels. See `spawn.geojson` in `example_data`.
- Vessel inter-arrival mean times. See `vessel_distribution_factory.py` in `example_model`.
- The vessel service times at berths. See `terminal-service-times.csv` in `example_data`.
- Traces (paths) from the sea/ocean to the berths. See `traces.geojson` in `example_data/traces`.

The following sections will explain some requirements in more details

### Sections

Sections are defined as a GeoJSON `FeatureCollection` where each `Feature` is a polygon defining the section area along with the following properties:

- **name**: the section name
- **speed**: the minimum and maximum speed (in knots) allowed in this section
  - Speed limitations are only applied to vessels, not to tugboats

_Note that the numbers in the example are random._
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "name": "section_1",
        "speed": {
            "class_1": {
                "min": 0.0,
                "max": 10.0
            },
            "class_2": {
                "min": 0.0,
                "max": 10.0
            }
        },
        "allowed_classes": []
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [1.1111231, 11.23421],
            [1.1111231,11.23421],
            [1.1111231,11.23421],
            [1.1111231,11.23421],
            [1.1111231,11.23421]
          ]
        ]
      }
    }, ...]
}
```

### Vessel traces/paths

In order to make navigation possible the following kind of paths (in GeoJSON format) must be specified:

- ocean -> berth
  - Each berth should have at least one of these paths, if such path does not exist the berth will not be used by the simulator
- ocean -> rendezvous
  - Each rendezvous must have at least one path connecting it to the ocean
- rendezvous -> berth
  - Usually each rendezvous location concerns a subset of the berths in the port, thus it is only required to connect berths to the rendezvous location(s) used in practice, not to all
- berth -> berth (optional)
  - These paths are not currently used but they will be required when shifting (berth -> berth) voyages are implemented
- waiting location -> rendezvous
  - These paths are used by tugboats to navigate between waiting locations and rendezvous points. At least one path for each `(waiting location, rendezvous)` pair is required

Multiple paths concerning the same pair of elements (e.g. ocean -> berth:54) can be specified. In this case when such a path is needed the simulatior will choose one of the available paths at random.

As an example, the following GeoJSON snipped describes a path connecting the ocean to berth 129 (described as `berth:129`). The IDs of berths and rendezvous location must match the ones assigned to berths and rendezvous in their respective data files.

The GeoJSON file must be a `FeatureCollection` where each `Feature` describes a path using a `LineString` element. The coordinates of the `LineString` define the path and must include origin and destination.

_Note that the numbers in the example are random._

```json
{
    "type": "FeatureCollection",
    "features": [{
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [
                [1.1111231, 11.23421],
                [1.1111231,11.23421],
                [1.1111231,11.23421],
                [1.1111231,11.23421],
                [1.1111231,11.23421]
            ]
        },
        "properties": {
            "origin": "ocean",
            "destination": "berth:129"
        }
    }, ...]
}
```

### Vessel spawn area

The vessel spawn area defines a polygon where vessels are to be generated in (at a random point withing the polygon). The spawn area is defined by a GeoJSON file with a single polygon (and no properties) as in the example below:

_Note that the numbers in the example are random._
```json
{
    "type": "FeatureCollection",
    "features": [{
        "type": "Feature",
        "properties": {},
        "geometry": {
            "type": "Polygon",
            "coordinates": [
              [
                1.1111231,
                11.23421
              ],
              [
                1.1111231,
                11.23421
              ],
              [
                1.1111231,
                11.23421
              ],
              [
                1.1111231,
                11.23421
              ],
              [
                1.1111231,
                11.23421
              ]
            ]
        }
    }]
}
```

### Berths

The set of berths in the simulated port must be provided as a csv file with the following columns:

- **id**: the berth ID, expressed as an integer
- **name**: the berth name
- **lat, lon**: coordinates (in WSG 84 format, a.k.a the standard one)
- **description**: optional berth description (not used by the simulator)
- **type**: the berth type (can be either jetty, berth or quay)
- **max_quay_length**: maximum allowed vessel length
- **max_depth**: the maximum allowed draught at this berth
- **ship_types**: corresponds to the content type the berth can process.
  1. liquid bulk
  2. container
  3. dry bulk
  4. chemical
- **terminal** (string): the terminal that the berth belongs to
  - This is used for retrieving the time it takes to service a vessel (see `terminal-service-times.csv`) since service times are given on a per-terminal basis
- **section**: the section of the port this berth is in

See an exmple below:

```sh
id,name,lat,lon,type,max_quay_length,max_depth,ship_types,terminal,section
0,Berth 1,31.52251026784937,1.227441038275049,quay,200,20,2,terminal 2,3
```

### Terminal service times

Terminal service times are defined by a csv file with the following columns:

- **terminal**: name of the terminal
- **section**: the section this terminal is in (unused?)
- **class x**: the mean amount of time (in seconds) it takes for berths in this terminal to process the vessel of class x

Example:

```sh
terminal,section,class 1,class 2
terminal 1,3,12000,12000
terminal 2,6,17000,20000
```

### Anchorages

Anchorages are defined by a GeoJSON file containing a `FeatureCollection` where each `Feature` defines a polygonal area for the anchorage plus the following properties:

- **name**: name of the anchorage 
- **max_draught**: maximum draught (meters) of a ship for this anchorage
- **id**: id of the anchorage (unused)

_Note that the numbers in the example are random._
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "name": "1",
        "max_draught": 20,
        "id": 0
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [
            [
              1.1111231,
              11.23421
            ],
            [
              1.1111231,
              11.23421
            ],
            [
              1.1111231,
              11.23421
            ],
            [
              1.1111231,
              11.23421
            ],
            [
              1.1111231,
              11.23421
            ]
        ]
      }
    }, ...]
}
```

The decision rules for allocating vessels to anchorages are defined in the model.

### Tugboat locations

#### Rendezvous

The rendezvous location(s) are defined by a GeoJSON file with a `FeatureCollection` where each `Feature` represents a waiting location as a `Point` with the following properties:

- **id:** the id of the waiting location
- **vessel_final_destination**: the destination sections for which this rendezvous point is used or, in other words: if a vessel needs to reach (following the example below) sections 11, 12 or 13 and needs tugging it will have to pass through this rendezvous point

_Note that the numbers in the example are random._
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "id": "1",
        "vessel_final_destination": [11, 12, 13]
      },
      "geometry": {
        "type": "Point",
        "coordinates": [
          1.1111231,
          11.23421
        ]
      }
    }, ...]
}
```

#### Waiting locations

The tugboats waiting location(s) are defined by a GeoJSON file with a `FeatureCollection` where each `Feature` represents a waiting location as a `Polygon` with the following properties:

- **id**: id of the tugboat waiting location 
- **name**: name of the tugboat waiting location
- **companies**: the companies that have tugboats standing by at this location
- **tug_per_company**: number of tugboats per company at this waiting location
  - The length of this array must match the length of the `companies` array

To simulate a single tugboat company simply specify an one-element array for both the `companies` and the `tugs_per_company` properties.

_Note that the numbers in the example are random._
```json
{
  "type": "FeatureCollection",
  "features": [{
      "type": "Feature",
      "properties": {
          "id": 11,
          "tugboats_count": 8,
          "name": "Tug 1",
          "companies": ["Company 1", "Company 2", "Company 3"],
          "tugs_per_company": [6, 4, 1]
      },
      "geometry": {
          "type": "Polygon",
          "coordinates": [
                [
                  [
                    1.2222222,
                    11.2222223
                  ],
                  [
                    1.2222322,
                    11.2222222
                  ],
                  [
                    1.1111231,
                    11.23421
                  ],
                  [
                    1.1111231,
                    11.23421
                  ],
                  [
                    1.1111231,
                    11.23421
                  ],
                  [
                    1.1111231,
                    11.23421
                  ],
                  [
                    1.1111231,
                    11.23421
                  ]
                ]
            ]
          }
      }, ...]
}
```