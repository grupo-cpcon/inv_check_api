from enum import Enum

class HierarchyStandChoice(str, Enum):
    PARENT = "PARENT"
    CHILD = "CHILD"

class ImageExportModeChoice(str, Enum):
    EXPORT_ALL = "EXPORT_ALL"
    EXPORT_TREE = "EXPORT_TREE"
    EXPORT_SINGLE = "EXPORT_SINGLE"