def classFactory(iface):
    from .plugin import ForestMapSheetGenerator
    return ForestMapSheetGenerator(iface)
