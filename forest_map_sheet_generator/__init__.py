"""QGIS entry point."""


def classFactory(iface):
    from .plugin import ForestMapSheetGeneratorPlugin
    return ForestMapSheetGeneratorPlugin(iface)
