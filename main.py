from qtpy import QtWidgets
from satellite_tracker.app import App
import sys

if __name__ == "__main__":
    qtapp = QtWidgets.QApplication(sys.argv)
    app = App()
    app.show()

    try:
        qtapp.exec_()
    except KeyboardInterrupt:
        pass
    app.stop_threads()
    sys.exit()
