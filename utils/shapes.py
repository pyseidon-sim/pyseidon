"""Collection of functions that manipulate shapes"""
import random
import numpy as np
import json
from shapely.geometry import Point, Polygon


def random_point_in_polygon(polygon):
    """Returns a random point in a given polygon."""
    minx, miny, maxx, maxy = polygon.bounds
    while True:
        generated_point = Point(
            random.uniform(minx, maxx),
            random.uniform(miny, maxy))

        if polygon.contains(generated_point):
            return np.array(generated_point.coords[:][0])


def geojson_to_polygons(geojson_filename):
    """Returns a polygon given a geojson file with the following structure
    
        "features":{
            "geometry":{
                "coordinates":{
                    [0, 0],
                    [0, 0]
                }
            }
        }
    """
    polygons = []

    with open(geojson_filename) as geo_file:
        geo_data = json.loads(geo_file.read())

        for feature in geo_data['features']:
            polygons.append(Polygon(feature['geometry']['coordinates'][0]))

    return polygons


def geojson_to_points(geojson_filename):
    points = []

    with open(geojson_filename) as geo_file:
        geo_data = json.loads(geo_file.read())

        for feature in geo_data['features']:
            points.append(Point(feature['geometry']['coordinates']))

    return points
