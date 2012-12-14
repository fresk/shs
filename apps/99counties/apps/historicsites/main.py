import json
import random
from kivy.app import App
from kivy.factory import Factory as F
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.utils import interpolate
from kivy.properties import *
from kivy.graphics.transformation import Matrix
from kivy.graphics.texture import *
from kivy.graphics.opengl import *
from kivy.graphics import *

from objloader import *
from mapview import *
from latlon import iowa_relative


m_cube = ObjFile("data/map/unitcube.obj").objects.values()[0]




def gScale(sx, sy, sz):
    mi = MatrixInstruction()
    mi.matrix = Matrix().scale(sx, sy, sz)
    return mi

def gZaxis():
    PushMatrix()
    Color(0,0,1)
    gScale(0.01, 0.01, 1.0)
    gMesh(m_cube)
    PopMatrix()

def gYaxis():
    PushMatrix()
    Color(0,1,0)
    gScale(0.01, 1.0, 0.01)
    gMesh(m_cube)
    PopMatrix()

def gXaxis():
    PushMatrix()
    Color(1,0,0)
    gScale(1,0.01,0.01)
    gMesh(m_cube)
    PopMatrix()

def gDrawAxes():
    gYaxis()
    gXaxis()
    gZaxis()

class _gMesh(Mesh):
    pass

def gMesh(m, source=None):
    mesh = _gMesh(
        vertices=m.vertices,
        indices=m.indices,
        fmt = m.vertex_format,
        mode = 'triangles',
        source = source )
    return mesh

def gCube(scale=1.0, pos=(0,0,0), color=(1,1,1,1), source=None):
    PushMatrix()
    c = Color(*color)
    t = Translate(*pos)
    s = gScale(scale,scale,scale)
    mesh = gMesh(m_cube, source)
    mesh.g_color = c
    mesh.g_translate = t
    mesh.g_scale = s
    PopMatrix()
    return mesh

def marker_pos(mdata):
    lat, lon = map(float, (mdata['latitude'], mdata['longitude']))
    x,y = iowa_relative((lat, lon))
    return (x - .5, y - .5, 0.025)

def gMarker(mdata):
    mdata['map_pos'] = mdata.get('map_pos', marker_pos(mdata))
    m = gCube(0.05, mdata['map_pos'])
    m.source = "data/map/marker-%s.png" % mdata.get('icon', 'medal')
    return m




class SHSMap(IowaMap):

    def render(self):
        super(SHSMap, self).render()
        with self.map_space:
            self.render_markers()

    def render_markers(self):
        self.markers = []
        PushMatrix()
        Translate(0,0, -0.025)
        self.marker_space = Canvas()
        with self.marker_space:
            for m in self.app.historic_sites.values():
                self.markers.append(gMarker(m))
        PopMatrix()














class TestApp(App):
    def build(self):
        self.load_data()
        return SHSMap()

    def load_data(self, *args):
        self.map_model = ObjFile("data/map/iowa2.obj")
        mesh_ids = json.load(open('data/mesh_ids.json', 'r'))
        historic_sites = json.load(open('resources/historicsites.json', 'r'))
        county_wiki = json.load(open('resources/countywiki.json'))

        self.counties = {}
        for c in county_wiki:
            n = c['name'].replace("'","").replace("-", "_")
            mid = mesh_ids[n]
            c['name'] = n
            self.counties[n] = c
            self.counties[n]['mesh'] = self.map_model.objects[mid]

        self.historic_sites = {}
        for site in historic_sites:
            n = site['name'].replace("'","").replace("-", "_")
            site['name']= n
            self.historic_sites[n] = site

if __name__ == "__main__":
    TestApp().run()
