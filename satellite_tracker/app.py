from math import pi, atan2, asin
from functools import partial
import time
import os
import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor, MainWindow
from qtpy import QtWidgets
from .utils import (
    StoppableThread, calculate_densities, get_sat_data,
    calculate_positions, load_tle_datasets_from_file,
    parse_tle, filter_sat_data, RADIUS
)

os.environ["QT_API"] = "pyqt5"

PLANET_TEXTURE = "resources/earth2k.jpg"


class App(MainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.datasets = load_tle_datasets_from_file()  # 2d list of urls to get tle data from
        self.offset = 0  # time offset in secs
        self.positions_changed = False
        self.scalar_mode = "density"
        self.slider_mode = "mins"
        self.dataset_name = list(self.datasets.keys())[0]
        self.setup_qt_frame()
        # add point cloud as mesh, background image, central globe, camera starting pos
        self.setup_plotter(self.setup_earth())
        if self.initalise_data_set():
            self.start_threads()
        else:
            print(f"Error: dataset \"{self.dataset_name}\" is empty or could not be loaded.")
            exit()

    @property
    def dataset(self):
        # returns the current dataset
        return self.datasets[self.dataset_name]

    def start_threads(self):
        self.position_update_thread = StoppableThread(target=self.position_update, daemon=True)
        self.position_update_thread.start()
        self.density_update_thread = StoppableThread(target=self.density_update, daemon=True)
        self.density_update_thread.start()

    def stop_threads(self):
        if hasattr(self, 'position_update_thread') and hasattr(self, 'density_update_thread'):
            self.position_update_thread.stop()
            self.position_update_thread.join()
            self.density_update_thread.stop()
            self.density_update_thread.join()

    def position_update(self):
        while True:
            if self.position_update_thread.stopped:
                break

            # calculate positions with sgp4 from the tle data
            self.positions = calculate_positions(self.sat_data, offset=self.offset)
            # update point cloud
            self.point_cloud.points = self.positions

    def density_update(self):
        if self.scalar_mode != "density":
            return
        while True:
            # calculate densities and update the point cloudsss
            self.densities = calculate_densities(self.point_cloud.points)
            self.point_cloud['Density'][:] = self.densities

            # sleep for 8s but continously check stop events
            for i in range(16):
                if self.density_update_thread.stopped:
                    return
                if self.positions_changed:
                    self.positions_changed = False
                    break

                time.sleep(0.5)

    def change_dataset(self, dataset_name):
        # loads a new dataset and re-inits plotter and threads

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

    def set_offset(self, value):
        # offsets time by specified amount

        if value == 0:
            self.offset = 0
            return

        if self.slider_mode == "hours":
            offset = round(value * 60 * 60, 3)
        elif self.slider_mode == "mins":
            offset = round(value * 60, 3)

        if len(calculate_positions(self.sat_data, offset)) == \
                len(calculate_positions(self.sat_data, self.offset)):
            self.offset = offset
            self.positions_changed = True
        else:
            # if the amount of points has changed, the mesh needs to be re-initialised
            self.stop_threads()
            self.plotter.remove_actor(self.sat_mesh)
            self.offset = offset
            self.initalise_data_set()
            self.start_threads()

    def live_time(self):
        self.slider.GetRepresentation().SetValue(0.0)
        self.set_offset(0)

    def set_slider_mins(self):
        self.slider.GetRepresentation().SetMinimumValue(-120)
        self.slider.GetRepresentation().SetMaximumValue(120)
        self.slider.GetRepresentation().SetTitleText("Time offset (mins)")
        self.slider_mode = "mins"

    def set_slider_hours(self):
        self.slider.GetRepresentation().SetMinimumValue(-96)
        self.slider.GetRepresentation().SetMaximumValue(96)
        self.slider.GetRepresentation().SetTitleText("Time offset (hours)")
        self.slider_mode = "hours"

    def set_color_mode(self, mode):
        self.scalar_mode = mode
        self.stop_threads()
        self.plotter.remove_actor(self.sat_mesh)
        self.initalise_data_set()
        self.start_threads()

    def initalise_data_set(self):
        # load and display a new dataset
        self.sat_data = get_sat_data(self.dataset)
        if len(self.sat_data) < 1:
            return False

        self.positions = calculate_positions(self.sat_data, offset=self.offset)
        self.point_cloud = pv.PolyData(self.positions)  # create point cloud

        if self.scalar_mode == "density":
            self.densities = calculate_densities(self.point_cloud.points)
            self.point_cloud['Density'] = self.densities
        elif self.scalar_mode == "debris":
            debris_list = []
            for sat in filter_sat_data(self.sat_data, offset=self.offset):
                if parse_tle(sat)["debris"]:
                    debris_list.append(0)
                else:
                    debris_list.append(1)

            self.point_cloud['    Debris / Not Debris'] = debris_list

        self.sat_mesh = self.plotter.add_mesh(self.point_cloud, colormap="rainbow", categories=True)
        return True

    def setup_qt_frame(self):
        self.frame = QtWidgets.QFrame()  # create a qt frame for plotter
        vlayout = QtWidgets.QVBoxLayout()
        self.plotter = QtInteractor(self.frame)
        vlayout.addWidget(self.plotter.interactor)  # add the pyvista plotter to qt frame
        self.signal_close.connect(self.plotter.close)
        self.frame.setLayout(vlayout)
        self.setCentralWidget(self.frame)
        self.build_menus()

    def build_menus(self):
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
        live = QtWidgets.QAction('Live', self)
        live.setShortcut('Ctrl+L')
        live.triggered.connect(self.live_time)
        time_menu.addAction(live)

        slider_menu = main_menu.addMenu("Slider")
        hours = QtWidgets.QAction('Hours', self)
        hours.setShortcut('Ctrl+H')
        hours.triggered.connect(self.set_slider_hours)
        slider_menu.addAction(hours)
        mins = QtWidgets.QAction('Minutes', self)
        mins.setShortcut('Ctrl+M')
        mins.triggered.connect(self.set_slider_mins)
        slider_menu.addAction(mins)

        scalar_menu = main_menu.addMenu("Scalar")
        density_button = QtWidgets.QAction('Density', self)
        density_button.setShortcut('Ctrl+D')
        density_button.triggered.connect(lambda: self.set_color_mode("density"))
        scalar_menu.addAction(density_button)
        type_button = QtWidgets.QAction('Type', self)
        type_button.setShortcut('Ctrl+E')
        type_button.triggered.connect(lambda: self.set_color_mode("debris"))
        scalar_menu.addAction(type_button)

    def setup_earth(self):
        # create a sphere mesh and wrap the earth texture
        temp_globe = pv.Sphere(
            radius=RADIUS, theta_resolution=120, phi_resolution=120,
            start_theta=270.001, end_theta=270
        )
        temp_globe.t_coords = np.zeros((temp_globe.points.shape[0], 2))
        for i in range(temp_globe.points.shape[0]):
            temp_globe.t_coords[i] = [
                0.5 + atan2(-temp_globe.points[i, 0], temp_globe.points[i, RADIUS]) / (2 * pi),
                0.5 + asin(temp_globe.points[i, 2]) / pi
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
        self.slider = self.plotter.add_slider_widget(
            self.set_offset, [-120, 120],
            title='Time offset (mins)'
        )
        self.slider.GetRepresentation().SetLabelFormat('%0.2f')
