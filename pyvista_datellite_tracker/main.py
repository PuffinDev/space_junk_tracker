import numpy as np
from sgp4.api import Satrec, jday
from sgp4.conveniences import jday_datetime
import pyvista as pv
from pyvista import examples
from requests import get
from datetime import datetime

KM = 100/12742
RAD = 50

def split(list_a, chunk_size):
  for i in range(0, len(list_a), chunk_size):
    yield list_a[i:i + chunk_size]

urls = [
    "http://celestrak.org/NORAD/elements/gp.php?GROUP=cosmos-2251-debris&FORMAT=tle",
    "http://celestrak.org/NORAD/elements/gp.php?GROUP=iridium-33-debris&FORMAT=tle",
    "http://celestrak.org/NORAD/elements/gp.php?GROUP=1999-025&FORMAT=tle",
    "http://celestrak.org/NORAD/elements/gp.php?GROUP=1982-092&FORMAT=tle"]

tle_text = ""
for url in urls:
    result = get(url)
    if result.status_code != 200:
        raise Exception("Failed to retrive TLE data")
    tle_text += result.text

tle_list = tle_text.split("\r\n")

sat_data = list(split(tle_list, 3))
satellites = [[0.0, 0.0, 0.0] for _ in sat_data[:-1]]

for i, data in enumerate(sat_data):
    if len(data) < 3:
        sat_data.remove(data)
    # if "DEB" not in data[0]:
    #     satellites[i].color = color.red
    #     satellites[i].scale = .5


dt = datetime.now()
jd, fr = jday_datetime(dt)

for i, satellite in enumerate(sat_data):
    sat = Satrec.twoline2rv(satellite[1], satellite[2])
    _, r, _ = sat.sgp4(jd, fr)
    satellites[i] = [r[1]*KM, r[2]*KM, r[0]*KM*-1]


points = satellites
print(points)

point_cloud = pv.PolyData(points)

point_cloud.plot(eye_dome_lighting=True)
