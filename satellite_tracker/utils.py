import time
import os
from threading import Thread, Event
from datetime import datetime
from math import sqrt
from json import load

import numpy as np
import grequests
from requests import Session
from sgp4.api import Satrec
from sgp4.conveniences import jday_datetime
import scipy.spatial as spatial
from dotenv import load_dotenv

load_dotenv()

RADIUS = 1  # radius of the globe
KM = (RADIUS * 2) / 12742  # kilometer scalar
TLE_DATASETS_FILE = "resources/tle_datasets.json"


class StoppableThread(Thread):
    #  custom thread with stop event
    def __init__(self,  *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = Event()

    def stop(self):
        self._stop_event.set()

    @property
    def stopped(self):
        return self._stop_event.is_set()


def calculate_densities(points):
    # calculates how many other satellites are within 1000 KM
    points = np.array(points)
    tree = spatial.KDTree(np.array(points))
    neighbors = tree.query_ball_tree(tree, KM*1000)

    return [len(i) for i in neighbors]


def calculate_positions(sat_data, offset=0):
    sat_pos_list = []

    # calculate julian date from datetime and offset
    dt = datetime.fromtimestamp(time.time() + offset)
    jd, fr = jday_datetime(dt)
    errs = 0

    for satellite in sat_data:
        sat = Satrec.twoline2rv(satellite[1], satellite[2])  # load tle data
        # calculate earth-centered inertial position
        e, r, _ = sat.sgp4(jd, fr)
        # check for errors or anomalous results
        if e == 0 and r[0]*KM < 1000 and r[1]*KM < 1000 and r[2]*KM < 1000:
            # set position of the point
            sat_pos_list.append([r[0]*KM, r[1]*KM, r[2]*KM])
        else:
            errs += 1

    return sat_pos_list


def filter_sat_data(sat_data, offset=0):
    filtered = []

    jd, fr = jday_datetime(datetime.fromtimestamp(time.time() + offset))

    for satellite in sat_data:
        sat = Satrec.twoline2rv(satellite[1], satellite[2])  # load tle data
        if sat.sgp4(jd, fr)[0] == 0:
            filtered.append(satellite)

    return filtered


def calculate_dist(point1, point2):
    x, y, z = point1
    a, b, c = point2
    distance = sqrt(
        pow(a - x, 2) +
        pow(b - y, 2) +
        pow(c - z, 2) * 1.0
    )
    return distance


# splits a list into equal chunks
def split_tle(list_a, chunk_size):
    for i in range(0, len(list_a), chunk_size):
        yield list_a[i:i + chunk_size]


def get_spacetrack_sat_data(url):
    # loads tle data from space-track.org with login details in ".env" file

    credentials = {
        "identity": os.getenv("EMAIL"),
        "password": os.getenv("PASSWORD")
    }

    with Session() as session:
        # post credentials
        resp = session.post(
            "https://www.space-track.org/ajaxauth/login",
            data=credentials
        )

        # rertive tle data
        resp = session.get(url)
        if resp.status_code == 401:
            print("Could not get data from space-track.org. Please make sure you have an account and have filled out the .env file.")

        return resp


def get_sat_data(url_list):
    # retrives tle data and returns a list of lists

    urls = url_list
    tle_text = ""

    spacetrack_urls = []
    rs = []
    for u in urls:
        if "space-track.org" not in u:
            rs.append(grequests.get(u))
        else:
            # if the url is space-track, handle it with get_spacetrack_sat_data
            spacetrack_urls.append(u)

    responses = grequests.map(rs)
    for response in responses:
        if response.status_code not in [200, 204]:
            print(response.status_code)
            raise Exception("Failed to retrive TLE data")
        tle_text += response.text

    for u in spacetrack_urls:
        response = get_spacetrack_sat_data(u)
        if response.status_code == 200:
            tle_text += response.text

    tle_list = tle_text.replace("\r", "").split("\n")
    # Two line element sets in a list [["line1", "line2", "line3"]]
    sat_data = list(split_tle(tle_list, 3))

    for sat in sat_data:
        if len(sat) != 3 or len(sat[2]) < 3:
            # remove incomplete tle sets
            sat_data.remove(sat)

    cat_nums = set()

    for sat in sat_data:
        cat_num = parse_tle(sat)["cat_num"]

        if cat_num in cat_nums:
            # remove duplicates
            sat_data.remove(sat)
        else:
            cat_nums.add(cat_num)

    return sat_data


def parse_tle(tle):
    ln0 = tle[0]
    ln1 = list(filter(('').__ne__, tle[1].split(" ")))
    return {
        "cat_num": ln1[1],
        "name": ln0,
        "debris": "DEB" in ln0
    }


def load_tle_datasets_from_file():
    with open(TLE_DATASETS_FILE, 'r', encoding="utf-8") as f:
        return load(f)
