from qtpy import QtWidgets
from satellite_tracker.app import App
import sys

if __name__ == "__main__":
    qtapp = QtWidgets.QApplication(sys.argv)
    app = App()
    app.show()
    sys.exit(qtapp.exec_())
