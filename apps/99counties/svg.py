import p2t
import xml.etree.ElementTree
import kivy
from kivy.clock import Clock
from kivy.uix.scatter import Widget
from kivy.graphics import Line, Triangle, Color
from kivy.properties import StringProperty


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

    def add_point(self, x, y):
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
            s = point.x / self.bounding_box.width
            t = point.x / self.bounding_box.height
        except ZeroDivisionError:
            s, t = 0, 0
        return (s, t)

    def _mesh_vertex(self, p):
        #s,t = self._tex_coords(p)
        s, t = .5, .5
        self.vertices.extend((p.x, p.y, s, t))
        self.indices.append(self._idx)
        self._idx = self._idx + 1

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
        height = float(self.svg_root.attrib['height'])
        self.width = min(self.width, width)
        self.height = min(self.width, height)

        verts = map(eval, svg_path.attrib['d'][2:-2].split("L"))
        verts = [(p[0], self.height - p[1]) for p in verts]
        outline = sum(verts + [verts[0]], ())
        poly = PolyMesh(verts)
        with self.canvas:
            self.fill_color = Color(.3, .3, .3, 1)
            for t in poly.triangles:
                Triangle(points=(t.a.x, t.a.y, t.b.x, t.b.y, t.c.x, t.c.y))
            Color(1, 1, 1, 1)
            Line(points=outline, width=1.2)
