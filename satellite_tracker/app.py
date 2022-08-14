import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor, MainWindow, BackgroundPlotter
from math import pi, atan2, asin
from functools import partial
from qtpy import QtWidgets
from datetime import datetime
from .utils import StoppableThread, calculate_densities, get_sat_data, calculate_positions, load_tle_datasets_from_file, RADIUS, KM
import time
import os
os.environ["QT_API"] = "pyqt5"

PLANET_TEXTURE = "resources/earth2k.jpg"

class App(MainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.datasets = load_tle_datasets_from_file()
        self.live = True
        self.dataset_name = list(self.datasets.keys())[0]
        self.setup_qt_frame()
        self.setup_plotter(self.setup_earth()) # add point cloud as mesh, background image, central globe, camera starting pos
        if self.initalise_data_set():
            self.start_threads()
        else:
            print(f"Error: dataset \"{self.dataset_name}\" is empty or could not be loaded.")
            exit()

    @property
    def dataset(self):
        return self.datasets[self.dataset_name]

    def start_threads(self):
        self.position_update_thread = StoppableThread(target=self.position_update, daemon=True)
        self.position_update_thread.start()
        self.density_update_thread = StoppableThread(target=self.density_update, daemon=True)
        self.density_update_thread.start()
        self.update_thread = StoppableThread(target=self.update, daemon=True)
        self.update_thread.start()

    def update(self):
        if self.update_thread.stopped:
            return
        self.plotter.update()

    def position_update(self):
        while True:
            if self.position_update_thread.stopped:
                break

            dt = datetime.now() if self.live else datetime.fromtimestamp(self.unix_time)
            self.positions = calculate_positions(self.sat_data, dt=dt)
            self.point_cloud.points = self.positions

    def density_update(self):
        while True:
            if self.density_update_thread.stopped:
                break

            self.densities = calculate_densities(self.point_cloud.points)
            self.point_cloud['Density'][:] = self.densities
            time.sleep(5)

    def change_dataset(self, dataset_name):
        self.stop_threads()

        prev_dataset = self.dataset_name
        self.dataset_name = dataset_name
        self.plotter.remove_actor(self.sat_mesh)
        if self.initalise_data_set():
            self.start_threads()
        else:
            print(f"Error: dataset \"{self.dataset_name}\" is empty or could not be loaded.")
            print("Reverting to previous dataset...")
            self.change_dataset(prev_dataset)
    
    def set_time(self):
        text, ok = QtWidgets.QInputDialog.getText(self, 'Input Dialog', 'Enter unix time:')
        if ok:
            self.live = False
            self.unix_time = float(text)
    
    def live_time(self):
        self.live = True

    def stop_threads(self):
        if hasattr(self, 'update_thread') and hasattr(self, 'position_update_thread') and hasattr(self, 'density_update_thread'):
            self.position_update_thread.stop()
            self.position_update_thread.join()
            self.density_update_thread.stop()
            self.density_update_thread.join()
            self.update_thread.stop()
            self.update_thread.join()

    def initalise_data_set(self):
        self.sat_data = get_sat_data(self.dataset)
        if len(self.sat_data) < 1:
            return False

        self.positions = calculate_positions(self.sat_data)
        self.point_cloud = pv.PolyData(self.positions) # create point cloud
        self.densities = calculate_densities(self.point_cloud.points)
        self.point_cloud['Density'] = self.densities
        self.sat_mesh = self.plotter.add_mesh(self.point_cloud, clim=(0, max(self.densities)), colormap="rainbow")
        return True

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
        self.build_menus()
        self.dateedit = QtWidgets.QDateEdit(calendarPopup=True)

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
        
        time_menu = main_menu.addMenu("Time")
        set_time = QtWidgets.QAction('Set time', self)
        set_time.setShortcut('Ctrl+T')
        set_time.triggered.connect(self.set_time)
        live = QtWidgets.QAction('Live', self)
        live.setShortcut('Ctrl+L')
        live.triggered.connect(self.live_time)
        time_menu.addAction(set_time)
        time_menu.addAction(live)
        

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
        cubemap = pv.cubemap("resources/cubemap")
        self.camera = pv.Camera()
        self.plotter.add_mesh(globe, texture=tex, lighting=False)
        self.plotter.show_axes()
        self.plotter.camera.focal_point = (0.0, 0.0, 0.0)
        self.plotter.add_actor(cubemap.to_skybox())
        self.plotter.set_environment_texture(cubemap, True)
