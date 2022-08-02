import pyvista as pv
from sgp4.api import Satrec
from sgp4.conveniences import jday_datetime
from requests import get
from datetime import datetime
from math import ceil, floor, sqrt, pi, atan, atan2, asin
import progressbar

RADIUS = 1 # radius of the self.globe in visualisation - RAD is a unit of measurement Radian, so renamed to RADIUS
KM = (RADIUS*2)/12742 # kilometer scalar
TLE_URLS = [
        "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"
]

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

def calculate_positions(sat_data):
    sat_pos_list = [[0.0, 0.0, 0.0] for _ in range(len(sat_data))]
    sat_dist = 0
    dt = datetime.now()
    jd, fr = jday_datetime(dt)
    print('plot points')
    for i in progressbar.progressbar(range(len(sat_data))):
        satellite = sat_data[i]
        sat = Satrec.twoline2rv(satellite[1], satellite[2]) # Load tle data
        _, r, _ = sat.sgp4(jd, fr) # calculate earth-centered inertial position 
        try:
            floor(r[0]) # test for nan in data set
            sat_pos_list[i] = [r[0]*KM, r[1]*KM, r[2]*KM] # set position of the point
            if calculate_dist( (0, 0, 0), sat_pos_list[i]) > sat_dist: # find max dist from earth core
                sat_dist = ceil(calculate_dist( (0, 0, 0), sat_pos_list[i]))
        except:
            pass
    # it would be good to only update boxy_space when a satellite moves between boxes, but that might be a bit complicated
    boxy_list = boxy_space(sat_dist, sat_pos_list)
    return sat_pos_list, boxy_list

def boxy_space(max_dist, point_list):
    # divide our 'space' in to 3D grid using max range as basic unit
    mid_point = ceil(max_dist)
    boxy_list = [[[[] for _ in range(mid_point*2 + 1)] for _ in range(mid_point*2 + 1)] for _ in range(mid_point*2 + 1)]
    for sat in point_list:
        x, y, z = sat
        # normalised around (0, 0, 0) space coords = (size, size, size) box coords
        boxy_list[floor(mid_point + x)][floor(mid_point + y)][floor(mid_point + z)].append(sat)
    # most cells will be empty
    return boxy_list

def calculate_dist(point1, point2):
    x, y, z = point1
    a, b, c = point2
    distance = sqrt(pow(a - x, 2) +
        pow(b - y, 2) +
        pow(c - z, 2)* 1.0)
    return distance

def calculate_densities_accurate(point_cloud):
    densities = [0 for _ in point_cloud.points]
    density_range = KM*1000 # scaled range for our model
    print('accurate')
    for i in progressbar.progressbar(range(len(point_cloud.points))):
        satellite = point_cloud.points[i]
        for other_satellite in point_cloud.points:
            if calculate_dist(satellite, other_satellite) < density_range: # search for other satellites within 1000KM
                densities[i] += 1
    
    return densities

def calculate_densities_cube_approx(point_cloud):
    densities = [0 for _ in point_cloud.points]
    density_range = KM*1000 # scaled range for our model
    print('cube est')
    for i in progressbar.progressbar(range(len(point_cloud.points))):
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
                densities[i] += 1
    return densities

def boxy_densities(boxy_points, point_cloud):
    densities = [0 for _ in point_cloud.points]
    density_range = KM*1000 # scaled range for our model
    print('boxy')
    mid_point = int(len(boxy_points) / 2)
    for i in progressbar.progressbar(range(len(point_cloud.points))):
        satellite = point_cloud.points[i]
        x, y, z = satellite
        space_box = boxy_points[floor(mid_point + x)][floor(mid_point + y)][floor(mid_point + z)]
        # we should probably also check adjoining boxes... not sure how yet
        # this is not it - turns a run time of 4s into +hrs
        '''
        for i in range(-1, 2):
            for j in range(-1, 2):
                for k in range(-1, 2):
                    space_box.extend(boxy_points[floor(mid_point + x + i)][floor(mid_point + y + j)][floor(mid_point + z + k)])
        '''
        for other_satellite in space_box:
            if calculate_dist(satellite, other_satellite) < density_range: # search for other satellites within 1000KM
                densities[i] += 1
    return densities

def run():
    print('get data')
    sat_data = get_sat_data(TLE_URLS) # base satellite data
    all_points, boxy_points = calculate_positions(sat_data)
    print('start processing')
    point_cloud = pv.PolyData(all_points) # create point cloud
    point_cloud['point_color'] = boxy_densities(boxy_points, point_cloud)
    point_cloud['point_color'] = calculate_densities_accurate(point_cloud)
    point_cloud['point_color'] = calculate_densities_cube_approx(point_cloud)

if __name__ == "__main__":
    run()
