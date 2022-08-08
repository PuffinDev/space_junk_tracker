import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor, MainWindow
from math import pi, atan2, asin
from functools import partial
from qtpy import QtWidgets
from space_tracker_resources import StoppableThread, calculate_densities, get_sat_data, calculate_positions, RADIUS, KM
from tle_datasets import TLE_DATASETS
import time
import sys
import os
os.environ["QT_API"] = "pyqt5"

PLANET_TEXTURE = "resources/earth2k.jpg"

class App(MainWindow):
    def __init__(self, datasets, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.datasets = datasets
        self.dataset_name = list(self.datasets.keys())[0]
        self.setup_qt_frame()
        self.setup_plotter(self.setup_earth()) # add point cloud as mesh, background image, central globe, camera starting pos
        self.initalise_data_set()
        self.start_threads()

    @property
    def dataset(self):
        return self.datasets[self.dataset_name]

    def start_threads(self):
        self.position_update_thread = StoppableThread(target=self.position_update, daemon=True)
        self.position_update_thread.start()
        self.density_update_thread = StoppableThread(target=self.density_update, daemon=True)
        self.density_update_thread.start()

    def position_update(self):
        while True:
            if self.position_update_thread.stopped:
                break
            self.point_cloud.points = calculate_positions(self.sat_data)
            self.plotter.update()
            time.sleep(0.2)

    def density_update(self):
        while True:
            if self.position_update_thread.stopped:
                break
            self.densities = calculate_densities(self.point_cloud)
            self.point_cloud['Density'][:] = self.densities
            time.sleep(0.2)

    def change_dataset(self, dataset_name):
        self.position_update_thread.stop()
        self.position_update_thread.join()
        self.density_update_thread.stop()
        self.density_update_thread.join()

        self.dataset_name = dataset_name
        self.plotter.remove_actor(self.sat_mesh)
        self.initalise_data_set()
        self.start_threads()

    def initalise_data_set(self):
        self.sat_data = get_sat_data(self.dataset)
        self.point_cloud = pv.PolyData(calculate_positions(self.sat_data)) # create point cloud
        self.densities = calculate_densities(self.point_cloud)
        self.point_cloud['Density'] = self.densities
        self.sat_mesh = self.plotter.add_mesh(self.point_cloud, clim=(0, max(self.densities)), colormap="rainbow")

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
        main_menu = self.menuBar()
        file_menu = main_menu.addMenu('File')
        exit_button = QtWidgets.QAction('Exit', self)
        exit_button.setShortcut('Ctrl+Q')
        exit_button.triggered.connect(self.close)
        file_menu.addAction(exit_button)
        dataset_menu = main_menu.addMenu("Change Dataset")
        for dataset_name in self.datasets.keys():
            change_dataset_button = QtWidgets.QAction(dataset_name, self)
            change_dataset_button.triggered.connect(partial(self.change_dataset, dataset_name))
            dataset_menu.addAction(change_dataset_button)

    def setup_earth(self):
        temp_globe = pv.Sphere(radius=RADIUS, theta_resolution=120, phi_resolution=120, start_theta=270.001, end_theta=270)
        temp_globe.t_coords = np.zeros((temp_globe.points.shape[0], 2))
        for i in range(temp_globe.points.shape[0]):
            temp_globe.t_coords[i] = [
                0.5 + atan2(-temp_globe.points[i, 0], temp_globe.points[i, RADIUS])/(2 * pi),
                0.5 + asin(temp_globe.points[i, 2])/pi
            ]
        # bad attempt at aligning point cloud to the sphere
        temp_globe.rotate_z(132)
        return temp_globe

    def setup_plotter(self, globe):
        tex = pv.read_texture(PLANET_TEXTURE)
        stars = pv.examples.download_stars_jpg()
        self.camera = pv.Camera()
        # create plotter and add meshes
        self.plotter.add_background_image(stars)
        self.plotter.add_mesh(globe, texture=tex)
        self.plotter.show_axes()
        self.plotter.camera.focal_point = (0.0, 0.0, 0.0)

if __name__ == "__main__":
    qtapp = QtWidgets.QApplication(sys.argv)
    app = App(TLE_DATASETS)
    app.show()
    sys.exit(qtapp.exec_())
