"""Starts PyQt event loop."""
import sys
import os
import ctypes
import warnings
import matplotlib as mpl
import matplotlib.backends.backend_pdf # pylint: disable = unused-import # required to assure backend is included
from PyQt6.QtQuick import QQuickWindow, QSGRendererInterface
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSharedMemory
from esibd.core import EsibdExplorer, PROGRAM_NAME, PROGRAM_VERSION

mpl.use('Qt5Agg')
mpl.rcParams['savefig.format']  = 'pdf' # make pdf default export format
mpl.rcParams['savefig.bbox']  = 'tight' # trim white space by default (also when saving from toolBar)
mpl.rcParams['figure.max_open_warning']  = 50 # not uncommon to exceed the default of 20 when using multiple plugins
warnings.filterwarnings("ignore" , message='constrained_layout') # suppress UserWarning: constrained_layout not applied because axes sizes collapsed to zero.
# TODO open bug with clearing shared log axis https://github.com/matplotlib/matplotlib/issues/9970
warnings.filterwarnings("ignore", message="Attempted to set non-positive left xlim on a log-scaled axis.\nInvalid limit will be ignored.")
warnings.filterwarnings("ignore", message="Attempt to set non-positive ylim on a log-scaled axis will be ignored.")
warnings.filterwarnings("ignore", message="Data has no positive values, and therefore cannot be log-scaled.")
warnings.filterwarnings("ignore", message="loadtxt: input contained no data:")
warnings.filterwarnings("ignore", message="Covariance of the parameters could not be estimated")
warnings.filterwarnings("ignore", message="overflow encountered in scalar subtract")
warnings.filterwarnings("ignore", message="overflow encountered in scalar add")

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--enable-logging --log-level=1"
    appStr = f'{PROGRAM_NAME} {PROGRAM_VERSION}'
    if sys.platform == 'win32':
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appStr)
    QQuickWindow.setGraphicsApi(QSGRendererInterface.GraphicsApi.OpenGL) # https://forum.qt.io/topic/130881/potential-qquickwidget-broken-on-qt6-2/4
    shared = QSharedMemory(appStr)
    if not shared.create(512, QSharedMemory.AccessMode.ReadWrite):
        print(f"Can't start more than one instance of {appStr}.")
        sys.exit(0)
    app.mainWindow = EsibdExplorer()
    app.mainWindow.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
