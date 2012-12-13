import json
from kivy.app import App
from kivy.factory import Factory as F
from kivy.resources import resource_find
from kivy.properties import *
from kivy.uix.listview import ListItemButton, ListView
from kivy.adapters.dictadapter import DictAdapter
from viewport import TransformLayer
from kivy.graphics.transformation import Matrix
from kivy.clock import Clock
from kivy.animation import Animation
from mapview import MarkerMapView, MapMarker
from dualdisplay import DualDisplay

class HistoricSitesDisplay(DualDisplay):
    selected_county = StringProperty("")



class SiteMarker(MapMarker):
    def __init__(self, site):
        self.data = site
        self.name = site['name']
        self.loc = map(float, (site['latitude'], site['longitude']))


class HistoricSitesMap(MarkerMapView):
    def __init__(self, **kwargs):
        super(HistoricSitesMap, self).__init__(**kwargs)
        self.sites = App.get_running_app().historic_sites
        for s in self.sites.values():
            self.add_marker(SiteMarker(s))

