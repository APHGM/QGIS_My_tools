from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.core import QgsProject
from qgis.utils import iface
import os

class ToggleLayerVisibilityPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None

    def initGui(self):
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.png')
        self.action = QAction(QIcon(icon_path), "Toggle Layer Visibility", self.iface.mainWindow())
        self.action.triggered.connect(self.toggle_visibility)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&Layer Visibility", self.action)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        self.iface.removePluginMenu("&Layer Visibility", self.action)

    def toggle_visibility(self):
        current_layer = self.iface.activeLayer()
        if not current_layer:
            QMessageBox.warning(self.iface.mainWindow(), "No Active Layer", "Please select a layer.")
            return

        root = QgsProject.instance().layerTreeRoot()
        all_nodes = root.findLayers()

        # Count how many are currently visible
        visible_count = sum(1 for node in all_nodes if node.isVisible())

        if visible_count > 1:
            # Turn off all except current
            for node in all_nodes:
                node.setItemVisibilityChecked(node.layer() == current_layer)
        else:
            # Turn all back on
            for node in all_nodes:
                node.setItemVisibilityChecked(True)
