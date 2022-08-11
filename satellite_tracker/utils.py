from math import sqrt, isnan
import numpy as np
from threading import Thread, Event
from requests import get
from sgp4.api import Satrec, SGP4_ERRORS
from sgp4.conveniences import jday_datetime
from datetime import datetime
import scipy.spatial as spatial
from json import load

RADIUS = 1 # radius of the self.globe in visualisation - RAD is a unit of measurement Radian, so renamed to RADIUS
KM = (RADIUS*2)/12742 # kilometer scalar
TLE_DATASETS_FILE = "resources/tle_datasets.json"

class StoppableThread(Thread):
    def __init__(self,  *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = Event()

    def stop(self):
        self._stop_event.set()

    @property
    def stopped(self):
        return self._stop_event.is_set()

def calculate_densities(points):
    points = np.array(points)
    tree = spatial.KDTree(np.array(points))
    neighbors = tree.query_ball_tree(tree, KM*1000)

    return [len(i) for i in neighbors]

def calculate_positions(sat_data):
    sat_pos_list = []

    dt = datetime.now()
    jd, fr = jday_datetime(dt)

    for i, satellite in enumerate(sat_data):
        sat = Satrec.twoline2rv(satellite[1], satellite[2]) # Load tle data
        e, r, _ = sat.sgp4(jd, fr) # calculate earth-centered inertial position
        if e == 0 and r[0]*KM < 1000 and r[1]*KM < 1000 and r[2]*KM < 1000: # check for errors or anomalous results
            sat_pos_list.append([r[0]*KM, r[1]*KM, r[2]*KM]) # set position of the point

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
        if result.status_code not in [200, 204]:
            print(result.status_code)
            raise Exception("Failed to retrive TLE data")
        tle_text += result.text

    tle_list = tle_text.replace("\r", "").split("\n")
    sat_data = list(split_tle(tle_list, 3)) # Two line element sets in a list [["line1", "line2", "line3"]]

    for sat in sat_data:
        if len(sat) != 3 or len(sat[2]) < 3:
            sat_data.remove(sat)

    cat_nums = set()

    for sat in sat_data:
        cat_num = list(filter(('').__ne__, sat[1].split(" ")))[1]

        if cat_num in cat_nums:
            sat_data.remove(sat)
        else:
            cat_nums.add(cat_num)

    return sat_data

def load_tle_datasets_from_file():
    with open(TLE_DATASETS_FILE) as f:
        return load(f)
