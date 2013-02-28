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
from functools import partial


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

def gCube(scale=1.0, pos=(0,0,0), color=(.8,.8,.8,1), source=None):
    PushMatrix()
    c = Color(*color)
    t = Translate(*pos)
    s = gScale(scale,scale,scale)
    mesh = gMesh(m_cube, source)
    mesh.scal = scale
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
    x,y = x-.5, y-.5
    x,y = x*.96, y*.99
    return (x, y, 0.001)


def gMarker(mdata):
    mdata['map_pos'] = mdata.get('map_pos', marker_pos(mdata))
    m = gCube(0.04, mdata['map_pos'])
    m.source = "data/map/marker-%s.png" % mdata.get('icon', 'medal')
    m.icon = "data/map/marker-%s.png" % mdata.get('icon', 'medal')
    make_pickable(m)
    m.is_selected  = False
    m.data = mdata
    return m


ATTR_STASH = {}


class SHSMap(IowaMap):
    selected_marker = ObjectProperty(None, allownone=True)
    selection = DictProperty({})

    def setup(self):
        self._map_vs = open(resource_find('data/shaders/map.vs')).read()
        self._map_fs = open(resource_find('data/shaders/map.fs')).read()
        self._picking_vs = open(resource_find('data/shaders/picking.vs')).read()
        self._picking_fs = open(resource_find('data/shaders/picking.fs')).read()
        self._picking = False
        self.markers = []
        self.last_marker = None
        self.selected_marker = None
        self.selection = {}

        self.historicsites = self.app.historic_sites.values()
        self.hollywood = self.app.hollywood.values()
        self.medals = self.app.medals.values()

    def on_touch_up(self, touch):
        if touch.time_update - touch.time_start < 300:
            self.selection_query(*touch.pos)
        return super(SHSMap, self).on_touch_up(touch)

    def render(self):
        super(SHSMap, self).render()
        with self.map_space:
            self.render_markers()

    def _disable_depth(self, *args):
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glEnable(GL_BLEND)

    def _enable_depth(self, *args):
        glEnable(GL_DEPTH_TEST)

    def render_markers(self):
        PushMatrix()
        Translate(0,0, -0.025)
        Callback(self._disable_depth)
        self.marker_space = Canvas()
        Callback(self._enable_depth)
        PopMatrix()

        with self.marker_space:
            self.historic_canvas = Canvas()
            self.hollywood_canvas = Canvas()
            self.medal_canvas = Canvas()

        with self.historic_canvas:
            for i in range(len(self.historicsites)):
                m = gMarker(self.historicsites[i])
                self.markers.append(m)

        with self.hollywood_canvas:
            for i in range(len(self.hollywood)):
                m = gMarker(self.hollywood[i])
                self.markers.append(m)

        with self.medal_canvas:
            for i in range(len(self.medals)):
                m = gMarker(self.medals[i])
                self.markers.append(m)


    def selection_query(self, x,y):
        if self.selected_marker:
            self.selected_marker.is_selected = False
            self.selected_marker = None

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
            return

        pid = rgba2pickid(r,b,g,a)
        marker = PICKABLE_OBJECTS.get(pid)
        if not marker:
            sid = min(PICKABLE_OBJECTS.keys(), key=lambda x:abs(x-pid))
            marker = PICKABLE_OBJECTS[sid]

        marker.is_selected = True
        self.selected_marker = marker


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

    def on_selected_marker(self, *args):
        if self.selected_marker:
            self.selection = self.selected_marker.data
        else:
            self.selection = {}


    def update(self):
        super(SHSMap, self).update()
        for m in self.markers:
            if m.is_selected:
                self.scale_up_marker(m)
            elif m.scal > 0.04 or min(m.color) > 0.75:
                self.scale_back_marker(m)

    def scale_back_marker(self, marker, *args):
        marker.color = interpolate(marker.color, (.75, .75, .75, .75))
        marker.scal = interpolate(marker.scal, 0.04)
        marker.g_color.rgba = marker.color
        marker.g_scale.matrix = Matrix().scale(marker.scal, marker.scal, marker.scal)

    def scale_up_marker(self, marker, *args):
        marker.color = interpolate(marker.color, (1,1,1,1))
        marker.scal = interpolate(marker.scal, 0.06)
        marker.g_color.rgba = marker.color
        marker.g_scale.matrix = Matrix().scale(marker.scal, marker.scal, marker.scal)



class DetailView(F.FloatLayout):
    selection = DictProperty({})

    def on_selection(self, *args):
        self.clear_widgets()
        if not self.selection:
            return
        print"SELECTION -->"
        print self.selection
        print ""
        print ""

        if self.selection.get('icon') == 'historic':
            self.add_widget(HSDetails(data=self.selection))
        if self.selection.get('icon') == 'medal':
            self.add_widget(MedalDetails(data=self.selection))
        if self.selection.get('icon') == 'hollywood':
            self.add_widget(HollywoodDetails(data=self.selection))



class HSDetails(F.FloatLayout):
    data = DictProperty({})

class MedalDetails(F.FloatLayout):
    data = DictProperty({})

class HollywoodDetails(F.FloatLayout):
    data = DictProperty({})
    image = StringProperty("data/img/avatar.png")

    def on_data(self, *args):
        print "!!!HW:"data.keys()
        if data.get('image'):
            self.image = data.get('image')['medium']

class H1(F.Label):
    pass

class H2(F.Label):
    pass

class Paragraph(F.Label):
    pass

class FactLabel(F.Label):
    pass


class FactDetail(F.Label):
    pass


