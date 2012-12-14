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
vs_map = open(resource_find('data/shaders/map.vs')).read()
fs_map = open(resource_find('data/shaders/map.fs')).read()
vs_pick = open(resource_find('data/shaders/pick.vs')).read()
fs_pick = open(resource_find('data/shaders/pick.fs')).read()



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
    #m.source = "data/map/mar`ker-%s.png" % mdata.get('icon', 'medal')
    return m



PICK_ID = 0
PICKABLE_OBJECTS = {}

def picking_id2rgb(pid):
    b = (pid) & 255
    g = (pid >> 8) & 255
    r = (pid >> 16) & 255
    return (r/255.0, g/255.0, b/255.0, 1.0)

def make_pickable(mesh):
    global PICK_ID, PICKABLE_OBJECTS
    PICK_ID += 4096
    mesh.pick_id = PICK_ID
    PICKABLE_OBJECTS[mesh.pick_id] = mesh
    mesh.g_color.rgba = picking_id2rgb(mesh_pick_id)

def gPickingMarker(mdata):
    mdata['map_pos'] = mdata.get('map_pos', marker_pos(mdata))
    m = gCube(0.05, mdata['map_pos'])
    make_pickable(m)
    return m





class SHSMap(IowaMap):
    pick_tex = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(SHSMap, self).__init__(**kwargs)

        self._picking_fbo = Fbo(size=self.size, with_depthbuffer=True, do_clear=True)
        self._picking_ctx = RenderContext(with_normal_mat=True)

        self._picking_ctx.add( PushMatrix() )
        self._picking_ctx.add( self.render_canvas )
        self._picking_ctx.add( PopMatrix() )

        self.pick_tex = self.fbo.texture

    def setup(self):
        self.places = self.app.historic_sites.values()
        self._picking_vs = open(resource_find('data/shaders/pick.vs')).read()
        self._picking_fs = open(resource_find('data/shaders/pick.fs')).read()


    def on_size(self, instance, value):
        super(SHSMap, self).on_size(instance, value)
        self._picking_fbo.size = value
        self.pick_tex = self.fbo.texture

    def on_touch_up(self, touch):
        self.selection_query(*touch.pos)
        return super(SHSMap, self).on_touch_up(touch)

    def selection_query(self, x,y):
        self._picking_ctx.shader.vs = self._picking_vs
        self._picking_ctx.shader.fs = self._picking_fs
        self._picking_ctx['projection_mat'] = self.projection_mat

        self._picking_fbo.bind()
        glDisable(GL_DEPTH_TEST)
        self._picking_ctx.draw()
        pixel = glReadPixels(x, y, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE)
        self._picking_fbo.release()

        self.pick_tex = self._picking_fbo.texture

        self._picking_fbo.bind()
        self._picking_fbo.release()
        print pixel


    def render(self):
        super(SHSMap, self).render()
        with self.map_space:
            self.render_markers()

    def render_markers(self):
        self.markers = []
        PushMatrix()
        Translate(0,0, -0.025)
        self.marker_space = Canvas()
        PopMatrix()

        with self.marker_space:
            for i in range(len(self.places)):
                SelectionID(i*1000)
                m = gMarker(self.places[i])
                self.markers.append(m)














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
