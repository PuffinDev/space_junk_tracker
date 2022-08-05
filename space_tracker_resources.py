from math import sqrt
from threading import Thread, Event
from requests import get
from sgp4.api import Satrec
from sgp4.conveniences import jday_datetime
from datetime import datetime

RADIUS = 1 # radius of the self.globe in visualisation - RAD is a unit of measurement Radian, so renamed to RADIUS
KM = (RADIUS*2)/12742 # kilometer scalar

class StoppableThread(Thread):
    def __init__(self,  *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = Event()

    def stop(self):
        self._stop_event.set()

    @property
    def stopped(self):
        return self._stop_event.is_set()

def calculate_densities(point_cloud):
    densities = [0 for _ in range(len(point_cloud.points))]

    for i in range(len(point_cloud.points)):
        satellite = point_cloud.points[i]
        for other_satellite in point_cloud.points:
            if calculate_dist(satellite, other_satellite) < KM*1000: # search for other satellites within 1000KM
                densities[i] += 1
    
    return densities

def calculate_positions(sat_data):
    sat_pos_list = [[0.0, 0.0, 0.0] for _ in range(len(sat_data))]

    dt = datetime.now()
    jd, fr = jday_datetime(dt)

    for i, satellite in enumerate(sat_data):
        sat = Satrec.twoline2rv(satellite[1], satellite[2]) # Load tle data
        _, r, _ = sat.sgp4(jd, fr) # calculate earth-centered inertial position 
        sat_pos_list[i] = [r[0]*KM, r[1]*KM, r[2]*KM] # set position of the point
    return sat_pos_list

def calculate_dist(point1, point2):
    x, y, z = point1
    a, b, c = point2
    distance = sqrt(pow(a - x, 2) +
        pow(b - y, 2) +
        pow(c - z, 2)* 1.0)
    return distance

# splits a list into equal chunks
def split_tle(list_a, chunk_size):
    for i in range(0, len(list_a), chunk_size):
        yield list_a[i:i + chunk_size]

def get_sat_data(url_list):
    urls = url_list
    tle_text = ""
    for url in urls:
        result = get(url)
        if result.status_code != 200:
            raise Exception("Failed to retrive TLE data")
        tle_text += result.text
    tle_list = tle_text.split("\r\n")
    sat_data = list(split_tle(tle_list, 3)) # Two line element sets in a list [["line1", "line2", "line3"]]
    for data in sat_data:
        if len(data) < 3:
            sat_data.remove(data) # remove incomplete data
    return sat_data