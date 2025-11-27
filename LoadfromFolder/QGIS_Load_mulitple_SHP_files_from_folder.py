from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QInputDialog, QFileDialog
from qgis.core import QgsVectorLayer, QgsProject, QgsWkbTypes, QgsRasterLayer
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
        folder = QFileDialog.getExistingDirectory(
            self.iface.mainWindow(),
            "Select the parent folder"
        )

        if not folder:
            raise SystemExit("❌ Folder selection cancelled.")

        if not os.path.isdir(folder):
            raise SystemExit("❌ Invalid folder path.")

        data_type_options = {
            "Shapefiles (.shp)": {
                "exts": [".shp"],
                "kind": "vector"
            },
            "GeoTIFF (.tif/.tiff)": {
                "exts": [".tif", ".tiff"],
                "kind": "raster"
            },
            "ECW (.ecw)": {
                "exts": [".ecw"],
                "kind": "raster"
            },
            "Raster (tif/tiff/ecw)": {
                "exts": [".tif", ".tiff", ".ecw"],
                "kind": "raster"
            }
        }

        type_choice, ok = QInputDialog.getItem(
            None,
            "Data Type",
            "Select the data type to load:",
            list(data_type_options.keys()),
            editable=False
        )

        if not ok:
            raise SystemExit("❌ Data type selection cancelled.")

        selected_type = data_type_options[type_choice]
        target_exts = tuple(selected_type["exts"])
        selected_kind = selected_type["kind"]

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
        loaded_any = False
        for root_dir, dirs, files in os.walk(folder):
            for file in files:
                if not file.lower().endswith(target_exts):
                    continue

                full_path = os.path.join(root_dir, file)
                layer_name = os.path.splitext(file)[0]

                if selected_kind == "vector":
                    layer = QgsVectorLayer(full_path, layer_name, "ogr")
                else:
                    layer = QgsRasterLayer(full_path, layer_name)

                if not layer.isValid():
                    print("❌ Invalid:", file)
                    continue

                loaded_any = True

                if selected_kind == "vector":
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
                else:
                    # Group all rasters under a single node
                    raster_group_name = "Raster Layers"
                    if raster_group_name not in group_dict:
                        group = root.addGroup(raster_group_name)
                        group_dict[raster_group_name] = group
                        print("Created group:", raster_group_name)

                    print(f"Loaded raster: {file}")
                    project.addMapLayer(layer, False)
                    group_dict[raster_group_name].addLayer(layer)

        if loaded_any:
            print("\n✔ Done! All layers loaded.")
        else:
            print("⚠ No files found matching the selected data type.")
