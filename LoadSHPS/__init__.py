from .QGIS_Load_mulitple_SHP_files_from_folder import LoadmulitpleSHPfilesPlugin

def classFactory(iface):
    return LoadmulitpleSHPfilesPlugin(iface)
    