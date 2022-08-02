from sgp4.api import Satrec
from sgp4.conveniences import jday_datetime
from requests import get
from datetime import datetime
from math import sqrt, pi, atan, atan2, asin
import progressbar

RADIUS = 1 # radius of the self.globe in visualisation - RAD is a unit of measurement Radian, so renamed to RADIUS
KM = (RADIUS*2)/12742 # kilometer scalar
TLE_URLS = [
        "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"
]

def get_sat_data(url_list):
    urls = url_list
    tle_text = ""
    for url in urls:
        result = get(url)
        if result.status_code != 200:
            raise Exception("Failed to retrive TLE data")
        tle_text += result.text
    tle_list = tle_text.split("\r\n")
    sat_data = list(self.split_tle(tle_list, 3)) # Two line element sets in a list [["line1", "line2", "line3"]]
    for data in sat_data:
        if len(data) < 3:
            sat_data.remove(data) # remove incomplete data
    return sat_data

def calculate_positions(self):
    sat_pos_list = [[0.0, 0.0, 0.0] for _ in range(len(self.sat_data))]

    dt = datetime.now()
    jd, fr = jday_datetime(dt)

    for i, satellite in enumerate(self.sat_data):
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

def calculate_densities(point_cloud):
    densities = [0 for _ in point_cloud]
    density_range = KM*1000 # scaled range for our model
    for i in range(len(point_cloud.points)):
        satellite = point_cloud.points[i]
        for other_satellite in point_cloud.points:
            x, y, z = satellite
            a, b, c = other_satellite
            # crude approximation
            if (
                (density_range >= x - a >= density_range * -1) and
                (density_range >= y - b >= density_range * -1) and
                (density_range >= z - c >= density_range * -1)
            ):
                if calculate_dist(satellite, other_satellite) < density_range: # search for other satellites within 1000KM
                    densities[i] += 1
    
    return densities

def run():
    sat_data = get_sat_data(TLE_URLS) # base satellite data
    point_cloud = pv.PolyData(calculate_positions(sat_data)) # create point cloud
    point_cloud['point_color'] = self.calculate_densities(point_cloud)


if __name__ == "__main__":
    run()
