import random
import json
import kivy
from kivy.app import App
from kivy.resources import resource_find
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.factory import Factory as F
from kivy.utils import interpolate
from kivy.properties import StringProperty, ObjectProperty
from kivy.graphics.transformation import Matrix
from kivy.graphics.texture import *
from kivy.graphics.opengl import *
from kivy.graphics import *

from objloader import ObjFile
from math import sin, cos
from latlon import iowa_relative
from objloader import ObjFile

from kivy.core.image import Image as CoreImage

import sys
iowa_hd = None

if sys.platform == "darwin":
    iowa_hd = CoreImage("data/map/iowa_land.png", mipmap=True)
else:
    iowa_hd = CoreImage("data/map/iowa8k.png", mipmap=True)

class MapView(Widget):
    selected_county = StringProperty("")
    texture = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        self.aspect = 1.0
        self.app = App.get_running_app()
        self.map_model = self.app.map_model
        self.counties = self.app.counties
        self.setup()

        self.canvas = Canvas()
        with self.canvas:
            fbo_size = self.width, self.height
            self.fbo = Fbo(size=fbo_size, with_depthbuffer=True, do_clear=True)
            self.fbo_color = Color(1, 1, 1, 1)
            self.fbo_rect = Rectangle()
        with self.fbo:
            self.cb = Callback(self.setup_gl_context)
            self.render_ctx = RenderContext(with_normal_mat=True)
            self.cb2 = Callback(self.reset_gl_context)
        self.init_scene()
        with self.render_ctx:
            PushMatrix()
            self.render_canvas = Canvas()
            PopMatrix();
        with self.render_canvas:
            self.render_scene()


        self.texture = self.fbo.texture
        super(MapView, self).__init__(**kwargs)

        #must be set in right order on some gpu, or fs will fail linking
        self.render_ctx.shader.vs = open(resource_find("data/shaders/map.vs")).read()
        self.render_ctx.shader.fs = open(resource_find('data/shaders/map.fs')).read()
        Clock.schedule_interval(self.update_glsl, 1 / 60.)

    def setup(self):
        pass

    def on_texture(self, instance, value):
        self.fbo_rect.texture = value

    def on_pos(self, instance, value):
        self.fbo_rect.pos = value

    def on_size(self, instance, value):
        self.aspect = (self.width/float(self.height))
        self.fbo.size = value
        self.texture = self.fbo.texture
        self.fbo_rect.size = self.size
        self.update_projection()

    def setup_gl_context(self, *args):
        self.fbo.clear_buffer()
        glEnable(GL_DEPTH_TEST)

    def reset_gl_context(self, *args):
        glDisable(GL_DEPTH_TEST)

    def update_projection(self):
        hw = self.aspect /2.0
        self.projection_mat = Matrix().view_clip(-hw,hw,-.5,.5, .98, 100, 1)

    def update_glsl(self, *largs):
        self.update()
        self.render_ctx['projection_mat'] = self.projection_mat

    def init_scene(self, *args):
        self.meshes = {}
        self.update_projection()

    def render(self):
        Color(1,1,1,1)
        self.render_map()

    def render_scene(self):
        PushMatrix()
        Translate(0,0,-1.2)
        self.t_viewtrans = MatrixInstruction()
        self.view_space = Canvas()
        self.render()
        PopMatrix()

    def render_map(self):
        PushMatrix()
        cx,cy = self.map_model.bounds.center[:-1]
        Translate(-cx, -cy, -0)
        tz = self.map_model.bounds.zmax
        PushMatrix()
        Translate(0,0,-tz)
        self.g_map_color = Color(1,1,1,1)
        for name in sorted(self.counties.keys()):
            m = self.counties[name]['mesh']
            self.meshes[name] = Mesh(
                vertices=m.vertices,
                indices=m.indices,
                fmt = m.vertex_format,
                mode = 'triangles',
                texture=iowa_hd.texture)
                #source = 'data/map/iowa_4k.png' )
        PopMatrix()
        self.map_space = Canvas()
        PopMatrix()



class InteractiveMapView(MapView):
    scatter = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(InteractiveMapView, self).__init__(**kwargs)
        self.scatter = F.ScatterPlane(do_rotation=True)
        self.add_widget(self.scatter)
        self.canvas.remove(self.scatter.canvas)
        self.xpan, self.ypan = 0, 0

    def update(self):
        s = self.scatter.scale
        if s < 1.5 and not self.scatter._touches:
            self.scatter.center = interpolate(self.scatter.center, self.center, 30)
        if s < 1.8 and not self.scatter._touches:
            self.scatter.center = interpolate(self.scatter.center, self.center, 40)
        if s < 1 and not self.scatter._touches:
            self.scatter.scale = interpolate(self.scatter.scale, 1.0, 40)
        xpan = self.scatter.center_x - self.center_x
        ypan = self.scatter.center_y - self.center_y
        tx = xpan/float(1920)
        ty = ypan/float(1920)
        mat = Matrix().scale(s,s,s).translate(tx,ty,0)

        self.t_viewtrans.matrix = mat

    def on_size(self, instance, value):
        super(InteractiveMapView, self).on_size(instance, value)
        self.scatter.size = self.size


class IowaMap(InteractiveMapView):
    cube_mesh = ObjFile("data/map/unitcube.obj").objects.values()[0]

    def __init__(self, **kwargs):
        super(IowaMap, self).__init__(**kwargs)

    def update(self):
        super(IowaMap, self).update()



def Scale3(sx, sy, sz):
    mi = MatrixInstruction()
    mi.matrix = Matrix().scale(sx, sy, sz)
    return mi







"""


    def update(self):
        super(IowaMap, self).update()
        #sel = []
        #for m in self.markers:
        #    m.update(self)
        #    if m.selected:
        #        sel.append(m)
        #self.selection = sel

    #def add_marker(self, marker):
    #    self.markers.append(marker)
    #    with self.map_canvas:
    #        PushMatrix()
    #        marker.render(self)
    #        PopMatrix()





class MapMarker(object):

    def __init__(self, name="des moines", loc=(41.590833,-93.620833)):
        self.name = name
        self.loc = loc
        self.color = (1,0,0,1)
        self.pos = (0,0)
        self.selected = False
        self.data = {}

    def update(self, ctx):
        sx, sy, sz = ctx.map_model.bounds.size
        rx, ry = iowa_relative(self.loc)
        self.pos = rx*sx, ry*sy

        self.g_color.rgba = self.color
        self.t_pos.xy = self.pos
        self.visible = False

        bl = ctx.scatter.to_local(0, 0)
        tr = ctx.scatter.to_local(ctx.height, ctx.height)
        tr = tr[0], tr[1]-0.2

        xok = bl[0]/1080.0 < self.pos[0] < tr[0]/1080.0
        yok = bl[1]/1080.0 < self.pos[1] < tr[1]/1080.0
        self.selected = yok and xok
        #print self.name
        #print bl[0]/1080.0 , self.pos[0] , tr[0]/1080.0, xok
        #print  bl[1]/1080.0 , self.pos[1] , tr[1]/1080.0, yok



    def render(self, ctx):
        self.t_pos = Translate(self.pos[0], self.pos[1], 0)
        self.t_scale = Scale3(.04, .04, .001)
        Translate(0,0,1.0)
        self.g_color = Color(*self.color)
        m = ctx.cube_mesh
        self.g_mesh = Mesh(
            vertices=m.vertices,
            indices=m.indices,
            fmt = m.vertex_format,
            mode = 'triangles')
"""
