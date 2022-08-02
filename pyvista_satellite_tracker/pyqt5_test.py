import numpy as np
from sgp4.api import Satrec
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
PLANET_TEXTURE = "pyvista_satellite_tracker/earth2k.jpg"

class App(MainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.setup_qt_frame()

        self.sat_data = self.get_sat_data(TLE_URLS) # base satellite data
        self.point_cloud = pv.PolyData(self.calculate_positions()) # create point cloud
        self.setup_plotter(self.setup_earth()) # add point cloud as mesh, background image, central globe, camera starting pos

        thread = Thread(target=self.update)
        thread.start()
    
    def update(self):
        while True:
            self.point_cloud.points = self.calculate_positions()
            #self.plotter.app.processEvents() # needs the QTInteractor event processor

    def setup_qt_frame(self):
        # create the frame
        self.frame = QtWidgets.QFrame()
        vlayout = QtWidgets.QVBoxLayout()

        # add the pyvista interactor object
        self.plotter = QtInteractor(self.frame)
        vlayout.addWidget(self.plotter.interactor)
        self.signal_close.connect(self.plotter.close)

        self.frame.setLayout(vlayout)
        self.setCentralWidget(self.frame)
        self.build_menus() # not working atm

    def build_menus(self):
        # simple menu to demo functions
        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('File')
        exitButton = QtWidgets.QAction('Exit', self)
        exitButton.setShortcut('Ctrl+Q')
        exitButton.triggered.connect(self.close)
        fileMenu.addAction(exitButton)

    def setup_earth(self):
        temp_globe = pv.Sphere(radius=RADIUS, theta_resolution=120, phi_resolution=120, start_theta=270.001, end_theta=270)
        temp_globe.t_coords = np.zeros((temp_globe.points.shape[0], 2))
        for i in range(temp_globe.points.shape[0]):
            temp_globe.t_coords[i] = [
                0.5 + atan2(-temp_globe.points[i, 0], temp_globe.points[i, RADIUS])/(2 * pi),
                0.5 + asin(temp_globe.points[i, 2])/pi
            ]
        # bad attempt at aligning point cloud to the sphere
        temp_globe.rotate_z(40)
        return temp_globe

    def setup_plotter(self, globe):
        tex = pv.read_texture(PLANET_TEXTURE)
        stars = pv.examples.download_stars_jpg()
        self.camera = pv.Camera()

        # create plotter and add meshes
        self.plotter.add_background_image(stars)
        self.plotter.add_mesh(globe, texture=tex)
        self.plotter.add_mesh(self.point_cloud)
        self.plotter.show_axes()
        self.plotter.camera.focal_point = (0.0, 0.0, 0.0)

    # splits a list into equal chunks
    def split_tle(self, list_a, chunk_size):
        for i in range(0, len(list_a), chunk_size):
            yield list_a[i:i + chunk_size]

    # calculates the distance between 2 points in 3d space
    def calculate_dist(self, point1, point2):
        x, y, z = point1
        a, b, c = point2
        distance = sqrt(pow(a - x, 2) +
            pow(b - y, 2) +
            pow(c - z, 2)* 1.0)
        return distance

    def get_sat_data(self, url_list):
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

    def calculate_densities(self, satellites):
        densities = [0 for _ in self.sat_data]

        for i in range(len(satellites)):
            satellite = satellites[i]
            for other_satellite in satellites:
                if self.calculate_dist(satellite, other_satellite) < KM*1000: # search for other satellites within 1000KM
                    densities[i] += 1
        
        return densities

if __name__ == "__main__":
    qtapp = QtWidgets.QApplication(sys.argv)
    app = App()
    app.show()
    sys.exit(qtapp.exec_())
