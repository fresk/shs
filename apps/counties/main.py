import os
import jsonkv
import glob
import p2t
import xml.etree.ElementTree

import kivy
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.scatter import Widget
from kivy.uix.scatter import Scatter, ScatterPlane
from kivy.graphics import Line, Triangle, Color, Mesh
from kivy.properties import *


DEV_PATH = os.path.dirname(__file__)
SHS_PATH = os.path.dirname(DEV_PATH)



class BoundingBox(object):
    def __init__(self, points=None):
        self.x = float('inf')
        self.y = float('-inf')
        self.xmax = float('-inf')
        self.ymin = float('inf')
        self.height = 0
        if points:
            for p in points:
                self.add_point(*p)

    def add_point(self, x,y):
        self.x = min(x, self.x)
        self.y = max(y, self.y)
        self.xmax = max(x, self.xmax)
        self.ymin = min(y, self.ymin)

        self.width = self.xmax - self.x
        self.height = self.y - self.ymin
        self.pos = (self.x, self.y)
        self.size = (self.width, self.height)


class PolyMesh(object):
    def __init__(self, verts):
        self.polyline = verts

        self.vertices = []
        self.indices = []
        self.bounding_box = BoundingBox(self.polyline)
        self.point_list = [p2t.Point(v[0], v[1]) for v in self.polyline]

        self.triangulate()

    def _tex_coords(self, point):
        try:
            s = point.x/self.bounding_box.width
            t = point.x/self.bounding_box.height
        except ZeroDivisionError:
            s,t = 0,0
        return (s,t)

    def _mesh_vertex(self, p):
        #s,t = self._tex_coords(p)
        s,t = .5, .5
        self.vertices.extend((p.x, p.y, s, t))
        self.indices.append(self._idx)
        self._idx = self._idx+1


    def triangulate(self):
        self.triangles = p2t.CDT(self.point_list).triangulate()
        self._idx = 0
        for t in self.triangles:
            self._mesh_vertex(t.a)
            self._mesh_vertex(t.b)
            self._mesh_vertex(t.c)









class SVGImage(Widget):
    source = StringProperty("")

    def on_source(self, *args):
        self.source = kivy.resources.resource_find(self.source)
        Clock.schedule_once(self.parse_svg)

    def parse_svg(self, *args):
        self.svg_tree = xml.etree.ElementTree.parse(self.source)
        self.svg_root = self.svg_tree.getroot()
        for elem in self.svg_root:
            if elem.tag == "path":
                self.add_path(elem)

    def add_path(self, svg_path):
        width = float(self.svg_root.attrib['height'])
        height =  float(self.svg_root.attrib['height'])
        self.width = min(self.width, width)
        self.height = min(self.width, height)

        verts = map(eval, svg_path.attrib['d'][2:-2].split("L"))
        verts = [(p[0], self.height - p[1]) for p in verts]
        outline = sum(verts + [verts[0]], ())
        poly = PolyMesh(verts)
        with self.canvas:
            Color(.3, .3, .3, 1)
            #Mesh(vertices=poly.vertices, indicies=poly.indices, mode="triangles")
            for t in poly.triangles:
                Triangle(points=(t.a.x, t.a.y, t.b.x, t.b.y, t.c.x, t.c.y))
            Color(1, 1, 1, 1)
            Line(points=outline, width=1.2)



class County(Scatter):
    id = StringProperty("")
    name = StringProperty("")
    svg = ObjectProperty()

    def on_name(self, name, *args):
        Clock.schedule_once(self.load_map)

    def load_map(self, *args):
        if self.svg:
            self.remove_widget(self.svg)
        svg_file = "{0}/map.svg".format(self.id)
        self.svg = SVGImage(source=svg_file)
        self.add_widget(self.svg)



class SVGTestApp(App):
    def build(self):
        self.root = ScatterPlane()
        county_data = json_load('counties.json')
        for county in county_data.values():
            self.root.add_widget(County(**county))
        return self.root


def json_load(fname):
    fname = kivy.resources.resource_find(fname)
    return jsonkv.json_load(fname)



kivy.resources.resource_add_path('../../data/counties')
SVGTestApp().run()




"""

import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter, ScatterPlane
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle
from kivy.properties import *


def load_json(fname):
    fname =kivy.resources.resource_find(fname)
    return json.load(open(fname, "r"))


class StateMap(ScatterPlane):
    def __init__(self, **kwargs):
        super(StateMap, self).__init__(**kwargs)
        self._counties = json_load('counties.json')
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
    kivy.resources.resource_add_path('../../counties')
    CountiesApp().run()

"""
