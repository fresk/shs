import json
import glob

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter, ScatterPlane
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle
from kivy.properties import *


class StateMap(ScatterPlane):
    def __init__(self, **kwargs):
        self._counties = json.load(open("data/counties.json", "r"))
        super(StateMap, self).__init__(**kwargs)
        for c in self._counties.values():
            pos = c['pos'][0] , 1204 - c['pos'][1]
            size = size=c['size']
            src = "data/{0}".format(c['png'])
            county_sprite = Scatter(pos=pos, size=size)
            img = Image(source=src, size=size, pos=(0,0), mipmap=True)
            county_sprite.add_widget(img)
            self.add_widget(county_sprite)


    def render_counties(self):
        for c in self._counties.values():
            print "Rect:", p, c['size']
            Rectangle(
                size = c['size'],
                pos = p,
                source = c['png']
            )



class CountiesApp(App):
    def build(self):
        return StateMap()

if __name__ == "__main__":
    CountiesApp().run()
