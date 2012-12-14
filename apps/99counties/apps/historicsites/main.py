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
from mapview import IowaMap, MapMarker
from dualdisplay import DualDisplay
import latlon

class HistoricSitesDisplay(DualDisplay):
    pass

class ContextTitle(F.Label):
    pass

class MapContext(F.BoxLayout):
    data = ListProperty([])
    def on_map(self, *args):
        pass

    def on_data(self, *args):
        self.clear_widgets()
        for item in self.data:
            try:
                self.add_widget(ContextTitle(text=item.name))
            except:
                self.add_widget(ContextTitle(text=item.__class__.__name__))


class LayerMarker(MapMarker):
    def __init__(self, **kwargs):
        super(LayerMarker, self).__init__(**kwargs)
        lat = random.random()* (latlon.N-latlon.S) + latlon.S
        lon = random.random()* (latlon.W-latlon.E) + latlon.E
        self.color = (1,1,1,1)
        self.loc = (lat, lon)
        self.layer = ''
        self.alpha = 0.0

    def update(self, ctx):
        r,g,b,a = self.color
        if ctx.layers.get(self.layer):
            a = interpolate(a, 1.0)
        else:
            a = interpolate(a, 0.0)
        self.color = (r,g,b,a)
        super(LayerMarker, self).update(ctx)

import random
from kivy.utils import interpolate
class MedalMarker(LayerMarker):
    def __init__(self, **kwargs):
        super(MedalMarker, self).__init__(**kwargs)
        self.layer = 'medals'
        self.color = (1,1,0,1)

class IowanMarker(LayerMarker):
    def __init__(self, **kwargs):
        super(IowanMarker, self).__init__(**kwargs)
        self.layer = 'iowans'
        self.color = (0,1,0,1)


class SiteMarker(LayerMarker):
    def __init__(self, site, **kwargs):
        super(SiteMarker, self).__init__(**kwargs)
        self.data = site
        self.name = site['name']
        self.loc = map(float, (site['latitude'], site['longitude']))
        self.color = (1,0,0,1)
        self.pos = [0,0]
        self.layer = 'sites'



class LayerMenu(F.Widget):
    pass

class SHSMap(IowaMap):
    selection = ListProperty([])
    def __init__(self, **kwargs):
        super(SHSMap, self).__init__(**kwargs)
        self.layers = {}
        self.scatter.scale_max = 7.0
        self.sites = App.get_running_app().historic_sites
        for s in self.sites.values():
            self.add_marker(SiteMarker(s))
        for i in range(4):
            self.add_marker(IowanMarker())
        for i in range(6):
            self.add_marker(IowanMarker())


    def on_touch_down(self, touch):
        self.selection = [m.data for m in self.markers]
        print self.scatter.scale
        return super(SHSMap, self).on_touch_down(touch)

