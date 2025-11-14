from .QGIS_Merge_By_Element_type import MergeByElementTypePlugin

def classFactory(iface):
    return MergeByElementTypePlugin(iface)
    