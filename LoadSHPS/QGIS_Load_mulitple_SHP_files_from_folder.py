from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QInputDialog
from qgis.core import QgsVectorLayer, QgsProject, QgsWkbTypes
from qgis.utils import iface
from qgis.PyQt.QtWidgets import QAction
import os

class LoadmulitpleSHPfilesPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None

    def initGui(self):
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.png')
        self.action = QAction(QIcon(icon_path), " Load mulitple SHP files", self.iface.mainWindow())
        self.action.triggered.connect(self.load_and_group_shapefiles)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&Load SHP files", self.action)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        self.iface.removePluginMenu("&Load SHP files", self.action)

    def load_and_group_shapefiles(self):
        # ---------------------------
        # Ask user for folder path
        # ---------------------------
        folder, ok = QInputDialog.getText(None, "Folder Path", 
                                        "Enter the parent folder path:")

        if not ok or not folder.strip():
            raise SystemExit("❌ No folder path entered.")

        folder = folder.strip()

        if not os.path.isdir(folder):
            raise SystemExit("❌ Invalid folder path.")

        project = QgsProject.instance()
        root = project.layerTreeRoot()

        # Track groups
        group_dict = {}

        def get_geom_name(layer):
            """Return readable geometry type"""
            return QgsWkbTypes.displayString(layer.wkbType())

        # ---------------------------
        # Load + Group layers
        # ---------------------------
        for root_dir, dirs, files in os.walk(folder):
            for file in files:
                if file.lower().endswith(".shp"):
                    full_path = os.path.join(root_dir, file)

                    layer = QgsVectorLayer(full_path, os.path.splitext(file)[0], "ogr")
                    if not layer.isValid():
                        print("❌ Invalid:", file)
                        continue

                    geom_type = get_geom_name(layer)
                    print(f"Loaded: {file} | Geometry: {geom_type}")

                    # Create geometry group if not exists
                    if geom_type not in group_dict:
                        group = root.addGroup(geom_type)
                        group_dict[geom_type] = group
                        print("Created group:", geom_type)

                    # Add layer to the group
                    project.addMapLayer(layer, False)
                    group_dict[geom_type].addLayer(layer)

        print("\n✔ Done! All shapefiles loaded and grouped by geometry type.")
