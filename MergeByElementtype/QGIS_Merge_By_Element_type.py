from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QInputDialog
from qgis.core import QgsVectorLayer, QgsProject, QgsWkbTypes
from qgis.utils import iface
from qgis.PyQt.QtWidgets import QAction
import os
from qgis.core import (
    QgsProject, QgsFeature, QgsVectorFileWriter,
    QgsFields, QgsField, QgsWkbTypes, QgsGeometry,
    QgsVectorLayer, QgsCoordinateReferenceSystem
)
from PyQt5.QtCore import QVariant


class MergeByElementTypePlugin:
    def __init__(self, iface)-> None:
        self.iface = iface
        self.action = None

    def initGui(self)-> None:
        icon_path: str = os.path.join(os.path.dirname(__file__),'icon.png')
        self.action = QAction(QIcon(icon_path), "Merge SHP files by Element type", self.iface.mainWindow())
        self.action.triggered.connect(self.Merge_by_Element_type)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&Merge SHP Files", self.action)

    def unload(self)-> None:
        self.iface.removeToolBarIcon(self.action)
        self.iface.removePluginMenu("&Merge SHP files", self.action)

    def Merge_by_Element_type(self)->None:
        # ---------------------
        # Configuration
        # ---------------------
        output_folder = QInputDialog.getText(None, "Folder Path", "Enter the parent folder path:")
        output_file = os.path.join(output_folder, "merged.shp")

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # ---------------------
        # Collect all polygon-type layers
        # ---------------------
        layers = []
        for lyr in QgsProject.instance().mapLayers().values():
            geom_type = QgsWkbTypes.displayString(lyr.wkbType())
            # Accept both Polygon and MultiPolygon
            if geom_type in ["Polygon", "MultiPolygon"]:
                layers.append(lyr)
                print(f"Found layer: {lyr.name()} ({geom_type})")

        if not layers:
            raise SystemExit("❌ No Polygon or MultiPolygon layers found.")

        # ---------------------
        # Use first layer's CRS
        # ---------------------
        base_crs = layers[0].crs()
        print(f"\n📍 Using CRS: {base_crs.authid()}")

        # ---------------------
        # Create minimal schema (just an ID field)
        # ---------------------
        fields = QgsFields()
        fields.append(QgsField("fid", QVariant.Int))
        fields.append(QgsField("source", QVariant.String, len=50))

        # ---------------------
        # Create memory layer as MultiPolygon
        # ---------------------
        merged_mem = QgsVectorLayer(
            "MultiPolygon?crs=" + base_crs.authid(),
            "merged_mem",
            "memory"
        )

        prov = merged_mem.dataProvider()
        prov.addAttributes(fields)
        merged_mem.updateFields()

        print("✔ Created memory layer for merge")

        # ---------------------
        # Copy and convert features
        # ---------------------
        feature_count = 0
        for lyr in layers:
            print(f"Processing: {lyr.name()}")
            
            for feat in lyr.getFeatures():
                geom = feat.geometry()
                
                # Skip if no geometry
                if geom.isNull() or geom.isEmpty():
                    continue
                
                # Convert Polygon to MultiPolygon if needed
                if QgsWkbTypes.displayString(geom.wkbType()) == "Polygon":
                    geom.convertToMultiType()
                
                # Create new feature with minimal attributes
                new_feat = QgsFeature(merged_mem.fields())
                new_feat.setGeometry(geom)
                new_feat['fid'] = feature_count
                new_feat['source'] = lyr.name()[:50]  # Truncate to fit field length
                
                prov.addFeatures([new_feat])
                feature_count += 1

        print(f"✔ All features copied to memory ({feature_count} features)")

        # ---------------------
        # Update layer extent
        # ---------------------
        merged_mem.updateExtents()

        # ---------------------
        # Write to shapefile with save options
        # ---------------------
        save_options = QgsVectorFileWriter.SaveVectorOptions()
        save_options.driverName = "ESRI Shapefile"
        save_options.fileEncoding = "UTF-8"

        print(f"\n💾 Writing to: {output_file}")

        # Use the newer writeAsVectorFormatV2 if available (QGIS 3.x)
        try:
            error = QgsVectorFileWriter.writeAsVectorFormatV2(
                merged_mem,
                output_file,
                QgsProject.instance().transformContext(),
                save_options
            )
            
            if error[0] == QgsVectorFileWriter.NoError:
                print("\n🎉 DONE – MultiPolygon merged successfully!")
                print(f"Output: {output_file}")
                print(f"Total features: {feature_count}")
                
                # Load the result into QGIS
                result_layer = QgsVectorLayer(output_file, "merged_output", "ogr")
                if result_layer.isValid():
                    QgsProject.instance().addMapLayer(result_layer)
                    print("✔ Result layer added to project")
            else:
                print(f"❌ ERROR: {error}")
                
        except AttributeError:
            # Fallback for older QGIS versions
            error = QgsVectorFileWriter.writeAsVectorFormat(
                merged_mem,
                output_file,
                "UTF-8",
                base_crs,
                "ESRI Shapefile"
            )
            
            if error == QgsVectorFileWriter.NoError:
                print("\n🎉 DONE – MultiPolygon merged successfully!")
                print(f"Output: {output_file}")
                print(f"Total features: {feature_count}")
                
                # Load the result into QGIS
                result_layer = QgsVectorLayer(output_file, "merged_output", "ogr")
                if result_layer.isValid():
                    QgsProject.instance().addMapLayer(result_layer)
                    print("✔ Result layer added to project")
            else:
                print(f"❌ ERROR: {error}")