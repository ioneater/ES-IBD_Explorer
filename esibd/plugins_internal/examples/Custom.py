# pylint: disable=[missing-module-docstring] # only single class in module

from PyQt6.QtWidgets import QGridLayout, QPushButton, QDialog, QLabel,QSizePolicy
from esibd.core import PluginManager
from esibd.plugins import Plugin

def providePlugins():
    return [CustomControl]

class CustomControl(Plugin):
    """The minimal code in "examples/Custom.py" demonstrates how to integrate your own
    custom elements to the ESIBD Explorer. This should be sufficient as
    long as your code does not requires interaction with any other elements
    of the ESIBD Explorer. See :ref:`sec:plugin_system` for more information."""
    documentation = """The minimal code in examples/Custom.py demonstrates how to integrate your own
    custom elements to the ESIBD Explorer. This should be sufficient as
    long as your code does not requires interaction with any other elements
    of the ESIBD Explorer."""

    name = 'CustomControl'
    version = '1.0'
    pluginType = PluginManager.TYPE.CONTROL
    previewFileTypes = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.icon = self.makeIcon('cookie.png')

    def initGUI(self):
        """Initialize your custom user interface"""
        super().initGUI()
        lay = QGridLayout()
        self.btn = QPushButton()
        lay.addWidget(self.btn)
        self.btn.setText('Click Me!')
        self.btn.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding)
        self.btn.clicked.connect(self.onClick)
        self.addContentLayout(lay)

    def onClick(self):
        """Execute your custom code"""
        dlg = QDialog(self)
        dlg.setWindowTitle('Custom Dialog')
        lbl = QLabel('This could run your custom code.')
        lay = QGridLayout()
        lay.addWidget(lbl)
        dlg.setLayout(lay)
        dlg.exec()
