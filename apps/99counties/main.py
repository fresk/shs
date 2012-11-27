import os
import jsonkv
import kivy
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.factory import Factory as F
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.scatter import Scatter, ScatterPlane
from kivy.properties import StringProperty, ObjectProperty, DictProperty, NumericProperty
from viewport import Viewport
from svg import SVGImage


DEV_PATH = os.path.dirname(__file__)
SHS_PATH = os.path.dirname(DEV_PATH)

class County(Scatter):
    id = StringProperty("")
    name = StringProperty("")
    svg = ObjectProperty()
    population = DictProperty()
    year = NumericProperty(0)

    def on_name(self, name, *args):
        Clock.schedule_once(self.load_map)

    def on_year(self, *args):
        self.set_color()

    def load_map(self, *args):
        self.year = 1900
        if self.svg:
            self.remove_widget(self.svg)
        svg_file = "{0}/map.svg".format(self.id)
        self.svg = SVGImage(source=svg_file)
        self.add_widget(self.svg)

    def set_color(self, *args):
        a = self.population["%d"%self.year]/330000.0
        try:
            self.svg.fill_color.rgb = (a,a,a)
        except:
            pass

class TopDisplay(RelativeLayout):
    def on_parent(self, *args):
        self.population_data = json_load('county_population.json')
        self.map_view = Scatter(scale=.7)
        self.map_view.x += 400
        self.map_view.y += 100
        county_data = json_load('counties.json')
        for county, data in county_data.iteritems():
            data['population'] = self.population_data[county]
            self.map_view.add_widget(County(**data))
        self.add_widget(self.map_view)



class BottomDisplay(RelativeLayout):
    year = NumericProperty(1900)

    def on_year(self, *args):
        if not self.parent:
            return
        map_view = App.get_running_app().top_display.map_view
        for c in map_view.children:
            c.year = self.year


class CountiesApp(App):
    def build(self):
        self.root = Viewport(size=(1920,2160))
        self.bottom_display = BottomDisplay()
        self.top_display = TopDisplay()
        self.root.add_widget(self.bottom_display)
        self.root.add_widget(self.top_display)
        return self.root





def json_load(fname):
    fname = kivy.resources.resource_find(fname)
    return jsonkv.json_load(fname)


kivy.resources.resource_add_path('../../data/county_population')
kivy.resources.resource_add_path('../../data/counties')
CountiesApp().run()
