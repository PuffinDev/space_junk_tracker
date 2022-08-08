from qtpy import QtWidgets
from tle_datasets import TLE_DATASETS
from satellite_tracker.app import App
import sys

if __name__ == "__main__":
    qtapp = QtWidgets.QApplication(sys.argv)
    app = App(TLE_DATASETS)
    app.show()
    sys.exit(qtapp.exec_())
