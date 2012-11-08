from kivy.app import App
from kivy.uix.scatter import ScatterPlane
from kivy.properties import StringProperty
from kivy.graphics import Line, Triangle, Color
from kivy.clock import Clock

import os
import p2t
from xml.etree import ElementTree

DEV_PATH = os.path.dirname(__file__)
SHS_PATH = os.path.dirname(DEV_PATH)


class SVGImage(ScatterPlane):
    source = StringProperty("")

    def on_source(self, *args):
        Clock.schedule_once(self.parse_svg)

    def parse_svg(self, *args):
        self.svg_tree = ElementTree.parse(self.source)
        self.svg_root = self.svg_tree.getroot()
        for elem in self.svg_root:
            if elem.tag == "path":
                self.add_path(elem)

    def add_path(self, svg_path):
        height = float(self.svg_root.attrib['height'])
        verts = map(eval, svg_path.attrib['d'][2:-2].split("L"))
        verts = [(p[0], height - p[1]) for p in verts]
        polyline = [p2t.Point(v[0], v[1]) for v in verts]
        triangles = p2t.CDT(polyline).triangulate()
        outline = sum(verts + [verts[0]], ())
        with self.canvas:
            Color(.3, .3, .3, 1)
            for t in triangles:
                Triangle(points=(t.a.x, t.a.y, t.b.x, t.b.y, t.c.x, t.c.y))
            Color(1, 1, 1, 1)
            Line(points=outline, width=1.2)


class SVGTestApp(App):
    def build(self):
        src = os.path.join(SHS_PATH, "counties/des_moines/map.svg")
        return SVGImage(source=src)


SVGTestApp().run()
