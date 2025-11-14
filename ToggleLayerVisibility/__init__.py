from .toggle_layer_visibility import ToggleLayerVisibilityPlugin

def classFactory(iface):
    return ToggleLayerVisibilityPlugin(iface)
