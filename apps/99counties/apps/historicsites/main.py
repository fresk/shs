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
    mesh.color = color
    mesh.icon = source
    mesh.g_color = c
    mesh.g_translate = t
    mesh.g_scale = s
    PopMatrix()
    return mesh


import random
import math

PICK_ID_INCR = 1024
PICK_ID = 0
PICKABLE_OBJECTS = {}

def rgba2pickid(r,g,b,a):
    ri = r * 256**2
    bi = b * 256**1
    gi = g
    return ri + bi + gi

def pickid2rgba(pid):
    b = (pid) & 255
    g = (pid >> 8) & 255
    r = (pid >> 16) & 255
    return (r/255.0, g/255.0, b/255.0, 1.0)

def make_pickable(mesh):
    global PICK_ID, PICKABLE_OBJECTS
    PICK_ID = PICK_ID + PICK_ID_INCR
    PICKABLE_OBJECTS[PICK_ID] = mesh
    mesh.pick_id = PICK_ID
    mesh.pick_color = pickid2rgba(PICK_ID)


def marker_pos(mdata):
    lat, lon = map(float, (mdata['latitude'], mdata['longitude']))
    x,y = iowa_relative((lat, lon))
    return (x - .5, y - .5, 0.025)


def gMarker(mdata):
    mdata['map_pos'] = mdata.get('map_pos', marker_pos(mdata))
    m = gCube(0.05, mdata['map_pos'])
    m.source = "data/map/marker-%s.png" % mdata.get('icon', 'medal')
    m.icon = "data/map/marker-%s.png" % mdata.get('icon', 'medal')
    make_pickable(m)
    m.data = mdata
    return m


ATTR_STASH = {}


class SHSMap(IowaMap):
    selection = DictProperty({})

    def setup(self):
        self.markers = []
        self.places = self.app.historic_sites.values()
        self.selection = self.places[0]
        self._map_vs = open(resource_find('data/shaders/map.vs')).read()
        self._map_fs = open(resource_find('data/shaders/map.fs')).read()
        self._picking_vs = open(resource_find('data/shaders/picking.vs')).read()
        self._picking_fs = open(resource_find('data/shaders/picking.fs')).read()
        self._picking = False

    def on_touch_up(self, touch):
        self.selection_query(*touch.pos)

    def render(self):
        super(SHSMap, self).render()
        with self.map_space:
            self.render_markers()

    def render_markers(self):
        PushMatrix()
        Translate(0,0, -0.025)
        self.marker_space = Canvas()
        PopMatrix()

        with self.marker_space:
            for i in range(len(self.places)):
                m = gMarker(self.places[i])
                self.markers.append(m)

    def selection_query(self, x,y):
        self.enable_picking()
        self.fbo.clear_color = (0,0,0,1)
        self.fbo.bind()
        self.fbo.clear_buffer()
        self.render_ctx.draw()
        self.fbo.release()

        self.fbo.bind()
        pixel = glReadPixels(x, y, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE)
        self.fbo.release()

        self.disable_picking()
        self.fbo.clear_color = (0,0,0,0)
        self.fbo.bind()
        self.fbo.clear_buffer()
        self.render_ctx.draw()
        self.fbo.release()



        r,g,b,a = map(ord, pixel)
        if r == 0 and g == 0 and b == 0:
            self.selection = {}
            return

        pid = rgba2pickid(r,b,g,a)
        marker = PICKABLE_OBJECTS.get(pid)
        if not marker:
            sid = min(PICKABLE_OBJECTS.keys(), key=lambda x:abs(x-pid))
            marker = PICKABLE_OBJECTS[sid]
        self.selection = marker.data


    def enable_picking(self):
        glDisable(GL_BLEND)
        self.render_ctx.shader.vs = self._picking_vs
        self.render_ctx.shader.fs = self._picking_fs
        self.g_map_color.rgba = (0,0,0,0)
        for m in self.markers:
            m.g_color.rgba = m.pick_color
            m.source = None

    def disable_picking(self):
        glEnable(GL_BLEND)
        self.render_ctx.shader.vs = self._map_vs
        self.render_ctx.shader.fs = self._map_fs
        self.g_map_color.rgba = (1,1,1,1)
        for m in self.markers:
            m.g_color.rgba = m.color
            m.source = m.icon



class DetailView(F.FloatLayout):
    selection = DictProperty({})

    def on_selection(self, *args):
        self.clear_widgets()
        if self.selection.get('icon') == 'historic':
            self.add_widget(HSDetails(data=self.selection))




class HSDetails(F.FloatLayout):
    data = DictProperty({})


class HSTitleLabel(F.Label):
    pass

class HSAddress(F.Label):
    pass

class HSText(F.Label):
    pass






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
