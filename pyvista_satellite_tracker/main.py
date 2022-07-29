import numpy as np
from sgp4.api import Satrec, jday
from sgp4.conveniences import jday_datetime
import pyvista as pv
from pyvista import examples
from requests import get
from datetime import datetime
from math import sqrt, pi, atan, atan2, asin
import progressbar

RAD = 1
KM = (RAD*2)/12742

def split(list_a, chunk_size):
  for i in range(0, len(list_a), chunk_size):
    yield list_a[i:i + chunk_size]

def calculate_dist(point1, point2):
    x, y, z = point1
    a, b, c = point2
    
    distance = sqrt(pow(a - x, 2) +
        pow(b - y, 2) +
        pow(c - z, 2)* 1.0)

    return distance

urls = [
    "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"
]

tle_text = ""
for url in urls:
    result = get(url)
    if result.status_code != 200:
        raise Exception("Failed to retrive TLE data")
    tle_text += result.text

tle_list = tle_text.split("\r\n")

sat_data = list(split(tle_list, 3))
satellites = [[0.0, 0.0, 0.0] for _ in sat_data]
densities = [0 for _ in sat_data]

for i, data in enumerate(sat_data):
    if len(data) < 3:
        sat_data.remove(data)

dt = datetime.now()
jd, fr = jday_datetime(dt)

for i, satellite in enumerate(sat_data):
    sat = Satrec.twoline2rv(satellite[1], satellite[2])
    _, r, _ = sat.sgp4(jd, fr)
    satellites[i] = [r[0]*KM, r[1]*KM, r[2]*KM]

for i in progressbar.progressbar(range(len(satellites))):
    satellite = satellites[i]
    for other_satellite in satellites:
        if calculate_dist(satellite, other_satellite) < KM*1000:
            densities[i] += 1

points = satellites

point_cloud = pv.PolyData(points)
point_cloud['point_color'] = densities

sphere = pv.Sphere(radius=RAD, theta_resolution=120, phi_resolution=120, start_theta=270.001, end_theta=270)
sphere.t_coords = np.zeros((sphere.points.shape[0], 2))
for i in range(sphere.points.shape[0]):
    sphere.t_coords[i] = [
        0.5 + atan2(-sphere.points[i, 0], sphere.points[i, RAD])/(2 * pi),
        0.5 + asin(sphere.points[i, 2])/pi
    ]

sphere.rotate_z(40)

tex = pv.read_texture("earth2k.jpg")

stars = examples.download_stars_jpg()

camera = pv.Camera()

plotter = pv.Plotter()
plotter.add_background_image(stars)
plotter.add_mesh(sphere, texture=tex)
plotter.add_mesh(point_cloud)
plotter.show_axes()
plotter.camera.focal_point = (0.0, 0.0, 0.0)

plotter.show()
