import numpy as np
from sgp4.api import Satrec, jday
from sgp4.conveniences import jday_datetime
import pyvista as pv
from pyvistaqt import BackgroundPlotter, QtInteractor, MainWindow
from requests import get
from datetime import datetime
from math import sqrt, pi, atan, atan2, asin
from threading import Thread
from qtpy import QtWidgets
import progressbar
import time
import sys
import os
os.environ["QT_API"] = "pyqt5"

RADIUS = 1 # radius of the self.globe in visualisation - RAD is a unit of measurement Radian, so renamed to RADIUS
KM = (RADIUS*2)/12742 # kilometer scalar

TLE_URLS = [
        "https://celestrak.org/NORAD/elements/gp.php?GROUP=last-30-days&FORMAT=tle"
]

# splits a list into equal chunks
def split(list_a, chunk_size):
    for i in range(0, len(list_a), chunk_size):
        yield list_a[i:i + chunk_size]

# calculates the distance between 2 points in 3d space
def calculate_dist(point1, point2):
    x, y, z = point1
    a, b, c = point2
    distance = sqrt(pow(a - x, 2) +
        pow(b - y, 2) +
        pow(c - z, 2)* 1.0)
    return distance

def get_sat_data(url_list):
    urls = url_list
    tle_text = ""
    for url in urls:
        result = get(url)
        if result.status_code != 200:
            raise Exception("Failed to retrive TLE data")
        tle_text += result.text
    tle_list = tle_text.split("\r\n")
    sat_data = list(split(tle_list, 3)) # Two line element sets in a list [["line1", "line2", "line3"]]
    for data in sat_data:
        if len(data) < 3:
            sat_data.remove(data) # remove incomplete data
    return sat_data

def calculate_positions(sat_data):
    satellites = [[0.0, 0.0, 0.0] for _ in sat_data]

    dt = datetime.now()
    jd, fr = jday_datetime(dt)

    for i, satellite in enumerate(sat_data):
        sat = Satrec.twoline2rv(satellite[1], satellite[2]) # Load tle data
        _, r, _ = sat.sgp4(jd, fr) # calculate earth-centered inertial position 
        satellites[i] = [r[0]*KM, r[1]*KM, r[2]*KM] # set position of the point
    
    return satellites

def calculate_densities(satellites):
    densities = [0 for _ in sat_data]

    for i in range(len(satellites)):
        satellite = satellites[i]
        for other_satellite in satellites:
            if calculate_dist(satellite, other_satellite) < KM*1000: # search for other satellites within 1000KM
                densities[i] += 1
    
    return densities

class App(MainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)

        # create the frame
        self.frame = QtWidgets.QFrame()
        vlayout = QtWidgets.QVBoxLayout()

        # add the pyvista interactor object
        self.plotter = QtInteractor(self.frame)
        vlayout.addWidget(self.plotter.interactor)
        self.signal_close.connect(self.plotter.close)

        self.frame.setLayout(vlayout)
        self.setCentralWidget(self.frame)

        # simple menu to demo functions
        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('File')
        exitButton = QtWidgets.QAction('Exit', self)
        exitButton.setShortcut('Ctrl+Q')
        exitButton.triggered.connect(self.close)
        fileMenu.addAction(exitButton)

        self.sat_data = get_sat_data(TLE_URLS)
        self.satellites = calculate_positions(self.sat_data)

        self.point_cloud = pv.PolyData(self.satellites) # create point cloud

        # generate mesh sphere to hold earth image
        self.globe = pv.Sphere(radius=RADIUS, theta_resolution=120, phi_resolution=120, start_theta=270.001, end_theta=270)
        self.globe.t_coords = np.zeros((self.globe.points.shape[0], 2))
        for i in range(self.globe.points.shape[0]):
            self.globe.t_coords[i] = [
                0.5 + atan2(-self.globe.points[i, 0], self.globe.points[i, RADIUS])/(2 * pi),
                0.5 + asin(self.globe.points[i, 2])/pi
            ]

        # bad attempt at aligning point cloud to the sphere
        self.globe.rotate_z(40)

        tex = pv.read_texture("earth2k.jpg")
        stars = pv.examples.download_stars_jpg()
        self.camera = pv.Camera()

        # create plotter and add meshes
        self.plotter.add_background_image(stars)
        self.plotter.add_mesh(self.globe, texture=tex)
        self.plotter.add_mesh(self.point_cloud)
        self.plotter.show_axes()
        self.plotter.camera.focal_point = (0.0, 0.0, 0.0)

        thread = Thread(target=self.update)
        thread.start()
    
    def update(self):
        while True:
            self.satellites = calculate_positions(self.sat_data)
            self.point_cloud.points = self.satellites
            self.plotter.app.processEvents()

if __name__ == "__main__":
    qtapp = QtWidgets.QApplication(sys.argv)
    app = App()
    app.show()
    sys.exit(qtapp.exec_())
