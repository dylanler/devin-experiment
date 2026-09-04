from beacon.origins.empty_objects import EmptyObject, build_object
from beacon.origins.graph_site import SiteGraph, generate as generate_graph
from beacon.origins.sidechannel import SideChannel, mount as mount_sidechannel
from beacon.origins.static_pages import page_for

__all__ = [
    "EmptyObject",
    "build_object",
    "SiteGraph",
    "generate_graph",
    "SideChannel",
    "mount_sidechannel",
    "page_for",
]
